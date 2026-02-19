from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(20), default="MARKETER")  # ADMIN / MARKETER / SALES
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    module = db.Column(db.String(30), nullable=False)  # campaign/pitch/lead
    inputs_json = db.Column(db.Text, nullable=False)
    output_json = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
