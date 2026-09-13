import os
import time
import random
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Text, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(INSTANCE_DIR, 'zynvex_portal.db')}"

_SQLITE_BUSY_MS = 30000

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


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _is_transient_sqlite_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "database is locked",
            "busy",
            "unable to open database file",
            "disk i/o error",
            "locking protocol",
        )
    )


def retry_on_sqlite_busy(func, *, max_attempts: int = 5, base_delay: float = 0.08):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except OperationalError as e:
            last_exc = e
            if not _is_transient_sqlite_error(e) or attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, base_delay)
            time.sleep(delay)
        except Exception:
            raise
    if last_exc is not None:
        raise last_exc


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        if db.is_active:
            retry_on_sqlite_busy(lambda: db.commit())
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
    
    role = Column(String(100), primary_key=True)  # Normalized role title (e.g. "Frontend Development")
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

# Automatically create tables on import
Base.metadata.create_all(engine)
