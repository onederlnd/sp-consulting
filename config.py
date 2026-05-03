import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@sunceraypatterson.com"
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'dev.db')}"
    )
    MAIL_USE_TLS = False
    MAIL_PORT = 1025
    UPLOAD_PATH = os.path.join(BASE_DIR, "instance", "uploads")


class StagingConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    MAIL_SUPRESS_SEND = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "_#Me!:-DaG?2SDf_D2!#SLsdas"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    SERVER_NAME = None
    RATELIMIT_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    UPLOAD_PATH = os.path.join(BASE_DIR, "instance", "uploads_test")


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    UPLOAD_PATH = "/data/uploads"


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}
