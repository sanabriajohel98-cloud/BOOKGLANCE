from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookglace_pro")

# DB (Render/Postgres o local SQLite)
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

# 👤 USUARIOS
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# 📦 PRODUCTOS
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50))
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))

# 📊 VENTAS
class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto_id = db.Column(db.Integer)
    cantidad = db.Column(db.Integer)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

# 🧾 TICKETS
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        if user == "admin" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin")

        u = Usuario.query.filter_by(nombre=user).first()
        if u and check_password_hash(u.password, password):
            session["role"] = "cliente"
            session["user"] = user
            return redirect("/tienda")

        return "❌ Login incorrecto"

    return render_template("login.html")

# 📝 REGISTRO
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["user"]
        password = generate_password_hash(request.form["pass"])

        nuevo = Usuario(nombre=nombre, password=password)
        db.session.add(nuevo)
        db.session.commit()

        return redirect("/")

    return render_template("registro.html")

# ⚙️ ADMIN
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

        p = Producto(nombre=nombre, precio=precio, stock=stock, imagen=filename)
        db.session.add(p)
        db.session.commit()

    productos = Producto.query.all()
    return render_template("admin.html", productos=productos)

# 🛒 CAJA
@app.route("/caja")
def caja():
    if session.get("role") != "admin":
        return redirect("/")

    caja = session.get("caja", [])
    total = sum(p["precio"] for p in caja)

    productos = Producto.query.all()

    return render_template("caja.html", caja=caja, total=total, productos=productos)

# ➕ AGREGAR A CAJA
@app.route("/agregar/<int:id>")
def agregar(id):
    p = Producto.query.get(id)

    if p.stock <= 0:
        return "❌ Sin stock"

    caja = session.get("caja", [])

    encontrado = False
    for item in caja:
        if item["id"] == p.id:
            item["cantidad"] += 1
            item["precio"] = item["cantidad"] * item["precio_unitario"]
            encontrado = True
            break

    if not encontrado:
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

# 💰 COBRAR
@app.route("/cobrar")
def cobrar():
    caja = session.get("caja", [])
    total = sum(p["precio"] for p in caja)

    for item in caja:
        p = Producto.query.get(item["id"])

        if p and p.stock >= item["cantidad"]:
            p.stock -= item["cantidad"]

            venta = Venta(
                producto_id=p.id,
                cantidad=item["cantidad"],
                total=item["precio"]
            )
            db.session.add(venta)

    ticket = Ticket(
        items=json.dumps(caja),
        total=total
    )

    db.session.add(ticket)
    db.session.commit()

    session["ticket"] = caja
    session["total"] = total
    session["caja"] = []

    return redirect("/ticket")

# 🧾 TICKET
@app.route("/ticket")
def ticket():
    items = session.get("ticket", [])
    total = session.get("total", 0)
    return render_template("ticket.html", items=items, total=total)

# 📊 VENTAS
@app.route("/ventas")
def ventas():
    ventas = Venta.query.all()
    return render_template("ventas.html", ventas=ventas)

# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
