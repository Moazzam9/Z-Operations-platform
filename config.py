import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "zynvex-operations-super-secret-key-12984712")
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'zynvex_portal.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload and Temp directories
    TEMP_DIR = os.path.join(INSTANCE_DIR, "temp")
    FONTS_DIR = os.path.join(INSTANCE_DIR, "fonts")
    
    # Make sure critical directories exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(FONTS_DIR, exist_ok=True)
