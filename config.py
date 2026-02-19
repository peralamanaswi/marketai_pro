import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtsecret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///marketai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
