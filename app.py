from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookglace_pro")

# DB CONFIG
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookglace.db"

app.config["UPLOAD_FOLDER"] = "static/images"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 📁 SERVIR IMÁGENES
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

# =========================
# 👤 MODELOS
# =========================

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50))
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto_id = db.Column(db.Integer)
    cantidad = db.Column(db.Integer)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

# =========================
# 🧱 CREAR DB + ADMIN
# =========================

@app.route("/crear")
def crear():
    db.create_all()

    if not Admin.query.filter_by(usuario="admin").first():
        admin = Admin(
            usuario="admin",
            password=generate_password_hash("1234")
        )
        db.session.add(admin)
        db.session.commit()

    return "✔ Base lista + admin creado (admin / 1234)"

# =========================
# 🔐 LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        # ADMIN
        admin = Admin.query.filter_by(usuario=user).first()
        if admin and check_password_hash(admin.password, password):
            session["role"] = "admin"
            session["user"] = user
            return redirect("/admin")

        # CLIENTE
        u = Usuario.query.filter_by(nombre=user).first()
        if u and check_password_hash(u.password, password):
            session["role"] = "cliente"
            session["user"] = user
            return redirect("/tienda")

        return "❌ Login incorrecto"

    return render_template("login.html")

# =========================
# 📝 REGISTRO CLIENTE
# =========================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["user"]
        password = generate_password_hash(request.form["pass"])

        db.session.add(Usuario(nombre=nombre, password=password))
        db.session.commit()
        return redirect("/")

    return render_template("registro.html")

# =========================
# ⚙️ ADMIN PANEL
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = float(request.form["precio"])
        stock = int(request.form["stock"])
        imagen = request.files["imagen"]

        filename = imagen.filename
        imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.add(Producto(nombre=nombre, precio=precio, stock=stock, imagen=filename))
        db.session.commit()

    return render_template("admin.html", productos=Producto.query.all())

# =========================
# 👥 ADMINS
# =========================

@app.route("/admins")
def admins():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admins.html", admins=Admin.query.all())

@app.route("/crear_admin", methods=["GET", "POST"])
def crear_admin():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if Admin.query.filter_by(usuario=usuario).first():
            return "❌ Ya existe"

        db.session.add(Admin(usuario=usuario, password=generate_password_hash(password)))
        db.session.commit()
        return redirect("/admins")

    return render_template("crear_admin.html")

@app.route("/editar_admin/<int:id>", methods=["GET", "POST"])
def editar_admin(id):
    if session.get("role") != "admin":
        return redirect("/")

    admin = Admin.query.get(id)

    if request.method == "POST":
        admin.usuario = request.form["usuario"]
        if request.form["password"]:
            admin.password = generate_password_hash(request.form["password"])
        db.session.commit()
        return redirect("/admins")

    return render_template("editar_admin.html", admin=admin)

@app.route("/eliminar_admin/<int:id>")
def eliminar_admin(id):
    if session.get("role") != "admin":
        return redirect("/")

    admin = Admin.query.get(id)

    if session.get("user") == admin.usuario:
        return "❌ No puedes eliminarte"

    db.session.delete(admin)
    db.session.commit()
    return redirect("/admins")

# =========================
# 🏪 TIENDA
# =========================

@app.route("/tienda")
def tienda():
    return render_template("tienda.html", productos=Producto.query.all())

# =========================
# 🛒 CAJA
# =========================

@app.route("/caja")
def caja():
    if session.get("role") != "admin":
        return redirect("/")

    caja = session.get("caja", [])
    total = sum(p["precio"] for p in caja)

    return render_template("caja.html", caja=caja, total=total, productos=Producto.query.all())

@app.route("/agregar/<int:id>")
def agregar(id):
    p = Producto.query.get(id)

    if p.stock <= 0:
        return "❌ Sin stock"

    caja = session.get("caja", [])

    for item in caja:
        if item["id"] == p.id:
            item["cantidad"] += 1
            item["precio"] = item["cantidad"] * item["precio_unitario"]
            session["caja"] = caja
            session.modified = True
            return redirect("/caja")

    caja.append({
        "id": p.id,
        "nombre": p.nombre,
        "cantidad": 1,
        "precio_unitario": float(p.precio),
        "precio": float(p.precio)
    })

    session["caja"] = caja
    session.modified = True

    return redirect("/caja")

# =========================
# 💰 COBRAR
# =========================

@app.route("/cobrar")
def cobrar():
    caja = session.get("caja", [])
    total = sum(p["precio"] for p in caja)

    for item in caja:
        p = Producto.query.get(item["id"])

        if p and p.stock >= item["cantidad"]:
            p.stock -= item["cantidad"]

            db.session.add(Venta(
                producto_id=p.id,
                cantidad=item["cantidad"],
                total=item["precio"]
            ))

    db.session.add(Ticket(
        items=json.dumps(caja),
        total=total
    ))

    db.session.commit()

    session["ticket"] = caja
    session["total"] = total
    session["caja"] = []

    return redirect("/ticket")

# =========================
# 🧾 TICKET
# =========================

@app.route("/ticket")
def ticket():
    return render_template("ticket.html",
                           items=session.get("ticket", []),
                           total=session.get("total", 0))

# =========================
# 📊 VENTAS
# =========================

@app.route("/ventas")
def ventas():
    return render_template("ventas.html",
                           ventas=Venta.query.all())

# =========================
# 🚪 LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
