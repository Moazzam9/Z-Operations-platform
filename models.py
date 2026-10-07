import os
import sys
import json
import time
import random
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Text, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

PERSISTENT_SETTINGS_FILE = os.path.join(BASE_DIR, "persistent_settings.json")
INSTANCE_SETTINGS_FILE   = os.path.join(INSTANCE_DIR, "persistent_settings.json")


def get_secret(key: str, default=None):
    """
    Safely resolves configuration values from:
      1. os.environ (standard shell / Docker / .env)
      2. st.secrets (Streamlit Cloud Secrets) without crashing if unconfigured
      3. fallback default
    """
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def normalize_database_url(raw_url: str) -> str:
    """
    Normalizes PostgreSQL / MySQL connection strings for SQLAlchemy 2.0+.
    - Converts legacy 'postgres://' to 'postgresql://'
    - Falls back to pg8000 driver if psycopg2 is missing
    """
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg2" not in url and "+pg8000" not in url:
        try:
            import psycopg2
        except ImportError:
            try:
                import pg8000
                url = "postgresql+pg8000://" + url[len("postgresql://"):]
            except ImportError:
                pass
    return url


def resolve_database_url() -> tuple[str, bool]:
    raw_env_url = get_secret("DATABASE_URL")
    if raw_env_url and str(raw_env_url).strip():
        norm_url = normalize_database_url(str(raw_env_url))
        is_cloud = not norm_url.startswith("sqlite")
        return norm_url, is_cloud
    
    # Default to local SQLite
    sqlite_path = os.path.join(INSTANCE_DIR, "zynvex_portal.db")
    return f"sqlite:///{sqlite_path}", False


DATABASE_URL, IS_CLOUD_DB = resolve_database_url()

_SQLITE_BUSY_MS = 30000

if not IS_CLOUD_DB:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": _SQLITE_BUSY_MS / 1000.0,
        },
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _apply_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_MS}")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        finally:
            cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _is_transient_db_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "database is locked",
            "busy",
            "unable to open database file",
            "disk i/o error",
            "locking protocol",
            "connection closed",
            "server closed the connection",
            "connection refused",
            "terminating connection",
            "could not connect to server",
        )
    )


def retry_on_db_transient(func, *, max_attempts: int = 5, base_delay: float = 0.08):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except OperationalError as e:
            last_exc = e
            if not _is_transient_db_error(e) or attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, base_delay)
            time.sleep(delay)
        except Exception:
            raise
    if last_exc is not None:
        raise last_exc


# Backwards compatibility alias
retry_on_sqlite_busy = retry_on_db_transient


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        if db.is_active:
            retry_on_db_transient(lambda: db.commit())
    except Exception:
        try:
            if db.is_active:
                db.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            db.close()
        except Exception:
            pass


# ── MODELS ───────────────────────────────────────────────────────────────────

class WhatsAppLink(Base):
    __tablename__ = 'whatsapp_links'
    
    role = Column(String(100), primary_key=True)  # Normalized role title
    group_link = Column(String(255), nullable=False)

    def to_dict(self):
        return {
            'role': self.role,
            'group_link': self.group_link
        }


class SystemSetting(Base):
    __tablename__ = 'system_settings'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)

    @classmethod
    def get(cls, db_session, key, default=None):
        setting = db_session.query(cls).filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set(cls, db_session, key, value):
        setting = db_session.query(cls).filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = cls(key=key, value=str(value))
            db_session.add(setting)


# Automatically create tables on import (safe for SQLite and Cloud DBs)
try:
    Base.metadata.create_all(engine)
except Exception as e:
    import warnings
    warnings.warn(f"[models.py] Base.metadata.create_all warning: {e}")


# ── PERSISTENT SETTINGS JSON MIRRORING & UTILITIES ────────────────────────────

def export_settings_to_dict(db_session=None) -> dict:
    """
    Exports all WhatsAppLink and SystemSetting records (excluding internal markers)
    into a structured dictionary suitable for JSON serialization and backup.
    """
    def _extract(db):
        wa_rows = db.query(WhatsAppLink).order_by(WhatsAppLink.role).all()
        wa_dict = {row.role: row.group_link for row in wa_rows}
        ss_rows = db.query(SystemSetting).order_by(SystemSetting.key).all()
        ss_dict = {
            row.key: row.value
            for row in ss_rows
            if not row.key.startswith("_seed_")
        }
        return {
            "_version": "1.0",
            "_exported_at": datetime.now().isoformat(),
            "whatsapp_links": wa_dict,
            "system_settings": ss_dict
        }

    if db_session:
        return _extract(db_session)
    with get_db_session() as db:
        return _extract(db)


def import_settings_from_dict(db_session, data: dict) -> tuple[int, int]:
    """
    Imports WhatsApp links and system settings from a dictionary into the active database.
    Returns (num_wa_updated, num_settings_updated).
    """
    wa_data = data.get("whatsapp_links", {})
    ss_data = data.get("system_settings", {})
    
    wa_count = 0
    for role, link in wa_data.items():
        if not role or not link:
            continue
        row = db_session.query(WhatsAppLink).filter_by(role=role).first()
        if row:
            row.group_link = str(link)
        else:
            db_session.add(WhatsAppLink(role=str(role), group_link=str(link)))
        wa_count += 1
        
    ss_count = 0
    for k, v in ss_data.items():
        if not k or k.startswith("_seed_"):
            continue
        SystemSetting.set(db_session, k, str(v))
        ss_count += 1
        
    return wa_count, ss_count


def sync_settings_to_disk(db_session=None) -> bool:
    """
    Writes a snapshot of current settings to persistent_settings.json.
    This ensures that even when running locally or on ephemeral containers,
    a JSON representation is kept up to date for commits and cold restarts.
    """
    try:
        data = export_settings_to_dict(db_session)
        content = json.dumps(data, indent=2, ensure_ascii=False)
        for target_path in (PERSISTENT_SETTINGS_FILE, INSTANCE_SETTINGS_FILE):
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as fh:
                    fh.write(content)
            except Exception:
                pass
        return True
    except Exception:
        return False


def load_settings_from_disk() -> dict | None:
    """
    Loads saved settings from persistent_settings.json if present on disk.
    Checks BASE_DIR then INSTANCE_DIR.
    """
    for candidate in (PERSISTENT_SETTINGS_FILE, INSTANCE_SETTINGS_FILE):
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict) and ("system_settings" in data or "whatsapp_links" in data):
                    return data
            except Exception:
                pass
    return None


def get_db_info() -> dict:
    """
    Returns diagnostics about the current active database connection.
    Masks credentials for security.
    """
    raw_url = str(engine.url)
    masked_url = raw_url
    if "@" in raw_url and "://" in raw_url:
        prefix, rest = raw_url.split("://", 1)
        creds, host_part = rest.split("@", 1)
        if ":" in creds:
            user = creds.split(":", 1)[0]
            masked_url = f"{prefix}://{user}:****@{host_part}"
        else:
            masked_url = f"{prefix}://****@{host_part}"

    return {
        "is_cloud": IS_CLOUD_DB,
        "dialect": engine.dialect.name,
        "driver": engine.dialect.driver,
        "display_url": masked_url,
        "persistent_json_exists": os.path.exists(PERSISTENT_SETTINGS_FILE) or os.path.exists(INSTANCE_SETTINGS_FILE),
        "persistent_json_path": PERSISTENT_SETTINGS_FILE,
    }
