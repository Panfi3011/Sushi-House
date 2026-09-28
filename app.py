import os
import re
from datetime import date, datetime, time, timedelta
from functools import wraps

import pyodbc
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", ""),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Configura SECRET_KEY en .env antes de iniciar la aplicación.")

csrf = CSRFProtect(app)


def get_db():
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "sushi_house")
    parts = [f"DRIVER={{{driver}}}", f"SERVER={server}", f"DATABASE={database}", "Encrypt=yes"]
    if os.getenv("SQL_TRUSTED_CONNECTION", "true").lower() == "true":
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend((f"UID={os.getenv('SQL_USERNAME', '')}", f"PWD={os.getenv('SQL_PASSWORD', '')}"))
    parts.append("TrustServerCertificate=" + ("yes" if os.getenv("SQL_TRUST_SERVER_CERTIFICATE", "true").lower() == "true" else "no"))
    return pyodbc.connect(";".join(parts) + ";")


def query(sql, params=(), *, one=False, commit=False):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
        if one:
            row = cur.fetchone()
            return dict(zip([column[0] for column in cur.description], row)) if row else None
        columns = [column[0] for column in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para continuar.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": session.get("user_name"), "today": date.today().isoformat()}


@app.get("/")
def home():
    return render_template("index.html")


@app.route("/registro", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or len(name) > 100:
            flash("Escribe tu nombre (máximo 100 caracteres).", "error")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
            flash("Escribe un correo electrónico válido.", "error")
        elif len(password) < 10 or len(password) > 128:
            flash("La contraseña debe tener entre 10 y 128 caracteres.", "error")
        elif query("SELECT id FROM users WHERE email = ?", (email,), one=True):
            flash("Ese correo ya tiene una cuenta. Inicia sesión.", "error")
        else:
            user_id = query(
                "INSERT INTO users (name, email, password_hash) OUTPUT INSERTED.id VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)), commit=True,
            )
            session.clear()
            session.permanent = True
            session["user_id"], session["user_name"] = user_id, name
            flash("Tu cuenta está lista. ¡Bienvenido a Sushi House!", "success")
            return redirect(url_for("reservations"))
    return render_template("auth.html", mode="register")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT id, name, password_hash FROM users WHERE email = ?", (email,), one=True)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Correo o contraseña incorrectos.", "error")
        else:
            session.clear()
            session.permanent = True
            session["user_id"], session["user_name"] = user["id"], user["name"]
            flash(f"Qué gusto verte, {user['name']}.", "success")
            target = request.args.get("next", "")
            return redirect(target if target.startswith("/") and not target.startswith("//") else url_for("reservations"))
    return render_template("auth.html", mode="login")


@app.post("/cerrar-sesion")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("home"))


@app.route("/reservar", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        try:
            day = date.fromisoformat(request.form.get("date", ""))
            slot = time.fromisoformat(request.form.get("time", ""))
            guests = int(request.form.get("guests", "0"))
        except (ValueError, TypeError):
            flash("Revisa la fecha, hora y número de personas.", "error")
            return render_template("book.html")
        if day < date.today() or day > date.today() + timedelta(days=90):
            flash("Elige una fecha entre hoy y los próximos 90 días.", "error")
        elif slot < time(12) or slot > time(22) or slot.minute not in (0, 30):
            flash("El horario disponible es de 12:00 a 22:00, cada media hora.", "error")
        elif not 1 <= guests <= 12:
            flash("La reserva admite de 1 a 12 personas.", "error")
        else:
            when = datetime.combine(day, slot)
            notes = request.form.get("notes", "").strip()[:500]
            query(
                "INSERT INTO reservations (user_id, reservation_at, guests, notes) OUTPUT INSERTED.id VALUES (?, ?, ?, ?)",
                (session["user_id"], when, guests, notes or None), commit=True,
            )
            flash("Tu mesa está reservada. ¡Te esperamos!", "success")
            return redirect(url_for("reservations"))
    return render_template("book.html")


@app.get("/mis-reservas")
@login_required
def reservations():
    items = query(
        "SELECT id, reservation_at, guests, notes, status, created_at FROM reservations "
        "WHERE user_id = ? ORDER BY reservation_at DESC", (session["user_id"],),
    )
    return render_template("reservations.html", reservations=items, now=datetime.now())


@app.post("/reservas/<int:reservation_id>/cancelar")
@login_required
def cancel_reservation(reservation_id):
    # Ownership and upcoming status are enforced in the update itself.
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE id = ? AND user_id = ? "
            "AND status = 'confirmed' AND reservation_at > GETDATE()",
            (reservation_id, session["user_id"]),
        )
        conn.commit()
        changed = cur.rowcount
    finally:
        conn.close()
    flash("Reserva cancelada." if changed else "No se pudo cancelar: revisa que sea tuya y futura.", "success" if changed else "error")
    return redirect(url_for("reservations"))


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
