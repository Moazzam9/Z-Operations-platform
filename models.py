import os
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Setup base paths matching config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(INSTANCE_DIR, 'zynvex_portal.db')}"

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Context Manager for thread-safe database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

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
