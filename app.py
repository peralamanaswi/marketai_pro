import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import json

from config import Config
from models import db, User, RequestLog
from groq_client import groq_chat
from prompts import campaign_prompt, pitch_prompt, lead_prompt
from export_pdf import make_pdf

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
CORS(app)

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()

# -------------------- UI PAGES --------------------
@app.get("/")
def login_page():
    return render_template("login.html")

@app.get("/register")
def register_page():
    return render_template("register.html")

@app.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.get("/campaign")
def campaign_page():
    return render_template("campaign.html")

@app.get("/pitch")
def pitch_page():
    return render_template("pitch.html")

@app.get("/lead")
def lead_page():
    return render_template("lead.html")

@app.get("/history")
def history_page():
    return render_template("history.html")

@app.get("/admin")
def admin_page():
    return render_template("admin.html")

# -------------------- HELPERS --------------------
def current_user():
    identity = get_jwt_identity()
    return User.query.filter_by(email=identity).first()

def require_role(*roles):
    u = current_user()
    if not u or u.role not in roles:
        return False
    return True

def save_log(user_id, module, inputs_dict, output_text):
    log = RequestLog(
        user_id=user_id,
        module=module,
        inputs_json=json.dumps(inputs_dict, ensure_ascii=False),
        output_json=json.dumps({"result": output_text}, ensure_ascii=False),
        model_used=app.config["GROQ_MODEL"]
    )
    db.session.add(log)
    db.session.commit()
    return log.id

# -------------------- AUTH APIs --------------------
@app.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"message": "All fields required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    # first user becomes ADMIN (optional but useful)
    role = "ADMIN" if User.query.count() == 0 else "MARKETER"

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered", "role": role}), 201

@app.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=user.email)
    return jsonify({
        "token": token,
        "role": user.role,
        "name": user.name,
        "email": user.email
    })

# -------------------- AI APIs --------------------
@app.post("/api/campaign/generate")
@jwt_required()
def campaign_generate():
    if not require_role("ADMIN", "MARKETER"):
        return jsonify({"message": "Forbidden"}), 403

    data = request.get_json() or {}
    sys = "You are a helpful marketing expert. Give clean, structured output."
    user_prompt = campaign_prompt(data)

    out = groq_chat(app.config["GROQ_API_KEY"], app.config["GROQ_MODEL"], sys, user_prompt)
    u = current_user()
    log_id = save_log(u.id, "campaign", data, out)
    return jsonify({"log_id": log_id, "result": out})

@app.post("/api/pitch/generate")
@jwt_required()
def pitch_generate():
    if not require_role("ADMIN", "SALES"):
        return jsonify({"message": "Forbidden"}), 403

    data = request.get_json() or {}
    sys = "You are a top sales coach. Be persuasive but clear."
    user_prompt = pitch_prompt(data)

    out = groq_chat(app.config["GROQ_API_KEY"], app.config["GROQ_MODEL"], sys, user_prompt)
    u = current_user()
    log_id = save_log(u.id, "pitch", data, out)
    return jsonify({"log_id": log_id, "result": out})

@app.post("/api/leads/score")
@jwt_required()
def lead_score():
    if not require_role("ADMIN", "SALES"):
        return jsonify({"message": "Forbidden"}), 403

    data = request.get_json() or {}
    sys = "You are a CRM lead scoring analyst. Output must be actionable."
    user_prompt = lead_prompt(data)

    out = groq_chat(app.config["GROQ_API_KEY"], app.config["GROQ_MODEL"], sys, user_prompt)
    u = current_user()
    log_id = save_log(u.id, "lead", data, out)
    return jsonify({"log_id": log_id, "result": out})

# -------------------- HISTORY APIs --------------------
@app.get("/api/history")
@jwt_required()
def history():
    u = current_user()
    module = request.args.get("module")

    q = RequestLog.query.filter_by(user_id=u.id)
    if module:
        q = q.filter_by(module=module)

    items = q.order_by(RequestLog.created_at.desc()).limit(50).all()
    out = []
    for i in items:
        out.append({
            "id": i.id,
            "module": i.module,
            "created_at": i.created_at.isoformat(),
            "inputs": json.loads(i.inputs_json),
            "output": json.loads(i.output_json)
        })
    return jsonify(out)

@app.get("/api/history/<int:log_id>")
@jwt_required()
def history_one(log_id):
    u = current_user()
    item = RequestLog.query.filter_by(id=log_id, user_id=u.id).first()
    if not item:
        return jsonify({"message": "Not found"}), 404

    return jsonify({
        "id": item.id,
        "module": item.module,
        "created_at": item.created_at.isoformat(),
        "inputs": json.loads(item.inputs_json),
        "output": json.loads(item.output_json)
    })

# -------------------- EXPORT PDF --------------------
@app.get("/api/export/pdf/<int:log_id>")
@jwt_required()
def export_pdf(log_id):
    u = current_user()
    item = RequestLog.query.filter_by(id=log_id, user_id=u.id).first()
    if not item:
        return jsonify({"message": "Not found"}), 404

    output = json.loads(item.output_json).get("result", "")
    title = f"MarketAI Export - {item.module.upper()} (ID: {item.id})"
    pdf_bytes = make_pdf(title, output)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"marketai_{item.module}_{item.id}.pdf"
    )

# -------------------- ADMIN ANALYTICS --------------------
@app.get("/api/admin/analytics")
@jwt_required()
def analytics():
    if not require_role("ADMIN"):
        return jsonify({"message": "Forbidden"}), 403

    total_users = User.query.count()
    total_requests = RequestLog.query.count()
    by_module = {
        "campaign": RequestLog.query.filter_by(module="campaign").count(),
        "pitch": RequestLog.query.filter_by(module="pitch").count(),
        "lead": RequestLog.query.filter_by(module="lead").count(),
    }

    return jsonify({
        "total_users": total_users,
        "total_requests": total_requests,
        "by_module": by_module
    })

if __name__ == "__main__":
    app.run(debug=True)
