from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_migrate import Migrate
import flask_migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookglace_pro")

# 📦 BASE DE DATOS
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookglace.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 📁 Servir imágenes
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)
# 👤 USUARIOS
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

# 📦 PRODUCTOS
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50))
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))
    
class CajaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"))
    cantidad = db.Column(db.Integer, default=1)
    precio_total = db.Column(db.Float)
    usuario = db.Column(db.String(100))  # opcional, para saber quién abrió la caja

# 📊 VENTAS
class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, default=1)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

# 🧾 TICKETS
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.Column(db.Text)  # JSON con los items
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))
# 🔧 DIAGNÓSTICO
@app.route("/debug")
def debug():
    try:
        # Solo mostrar las tablas, NO crear de nuevo
        return f"✅ DB OK. Tablas: {[t for t in db.metadata.tables.keys()]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

   # createDB.py

# createDB.py
from app import app, db
from flask_migrate import upgrade

with app.app_context():
      upgrade()  # aplica las migraciones pendientes
      print("✅ Migraciones aplicadas correctamente, productos e imágenes conservados.")

# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        # ADMIN
        if user == "admin" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin")

        # CLIENTE
        u = Usuario.query.filter_by(nombre=user, password=password).first()
        if u:
            session["role"] = "cliente"
            session["user"] = user
            return redirect("/tienda")

        return "❌ Error login"

    return render_template("login.html")

# 📝 REGISTRO
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["user"]
        password = request.form["pass"]

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
        codigo = request.form.get("codigo", "")
        nombre = request.form["nombre"]
        precio = float(request.form.get("precio", 0))
        stock = int(request.form.get("stock", 0))


        # Manejo seguro de la imagen
        nombre_imagen = None  # por defecto no hay imagen
        if "imagen" in request.files:
            imagen = request.files["imagen"]
            if imagen and imagen.filename.strip():  # solo si realmente se subió algo
                ruta = os.path.join(app.config["UPLOAD_FOLDER"], imagen.filename)
                imagen.save(ruta)
        nombre_imagen = imagen.filename
            # si no hay imagen, no se hace nada


        # Crear producto
        p = Producto(
            codigo=codigo,
            nombre=nombre,
            precio=float(precio),
            stock=int(stock),
            imagen=nombre_imagen)

        db.session.add(p)
        db.session.commit()

    productos = Producto.query.all()
    return render_template("admin.html", productos=productos)

# ✏️ EDITAR PRODUCTO
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if session.get("role") != "admin":
        return redirect("/")

    producto = Producto.query.get(id)
    if not producto:
        return redirect("/admin")

    if request.method == "POST":
        producto.codigo = request.form.get("codigo", producto.codigo)
        producto.nombre = request.form.get("nombre", producto.nombre)
        try:
            producto.precio = float(request.form.get("precio", producto.precio))
            producto.stock = int(request.form.get("stock", producto.stock))
        except ValueError:
            return "❌ Error: precio o stock inválido"

        # Imagen opcional: si no se sube nueva, se mantiene la anterior
        if "imagen" in request.files:
            imagen = request.files["imagen"]
            if imagen and imagen.filename.strip():
             ruta = os.path.join(app.config["UPLOAD_FOLDER"], imagen.filename)
        imagen.save(ruta)
        producto.imagen = imagen.filename
# si no hay imagen, no se toca producto.imagen


        db.session.commit()
        return redirect("/admin")

    return render_template("editar.html", producto=producto)

# 🗑️ ELIMINAR PRODUCTO
@app.route("/eliminar/<int:id>")
def eliminar(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    p = Producto.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    
    return redirect("/admin")

# 🏪 TIENDA
@app.route("/tienda")
def tienda():
    productos = Producto.query.all()
    return render_template("tienda.html", productos=productos)

@app.route("/caja")
def caja_view():
    if session.get("role") != "admin":
        return redirect("/")
    
    # Traer los ítems de la base
    caja = CajaItem.query.filter_by(usuario=session.get("user","admin")).all()
    total = sum(i.precio_total for i in caja)
    productos = Producto.query.all()
    
    return render_template("caja.html", caja=caja, total=total, productos=productos)


# 🔍 BUSCAR PRODUCTOS (para caja)
@app.route("/buscar")
def buscar():
    q = request.args.get("q", "")
    if q:
        productos = Producto.query.filter(
            (Producto.nombre.ilike(f"%{q}%")) | 
            (Producto.codigo.ilike(f"%{q}%"))
        ).all()
    else:
        productos = Producto.query.all()

    caja = CajaItem.query.filter_by(usuario=session.get("user","admin")).all()
    total = sum(i.precio_total for i in caja)
    return render_template("caja.html", caja=caja, total=total, productos=productos)

# 🛒 CAJA
@app.route("/actualizar_cantidad/<int:index>", methods=["POST"], endpoint="actualizar_cantidad_post")
def actualizar_cantidad_post(index):
    if session.get("role") != "admin":
        return redirect("/")

    cantidad = int(request.form.get("cantidad", 1))
    item = CajaItem.query.get(id)

    if item:
        if cantidad > 0:
            item.cantidad = cantidad
            producto = Producto.query.get(item.producto_id)
            item.precio_total = producto.precio * cantidad
        else:
            db.session.delete(item)

        db.session.commit()

    return redirect("/caja")



# ➕ AGREGAR A CAJA
@app.route("/agregar/<int:id>")
def agregar(id):
    if session.get("role") != "admin":
        return redirect("/")

    producto = Producto.query.get(id)
    if not producto:
        return redirect("/caja")

    usuario = session.get("user","admin")
    item = CajaItem.query.filter_by(producto_id=producto.id, usuario=usuario).first()

    if item:
        item.cantidad += 1
        item.precio_total = producto.precio * item.cantidad
    else:
        item = CajaItem(
            producto_id=producto.id,
            cantidad=1,
            precio_total=producto.precio,
            usuario=usuario
        )
        db.session.add(item)

    db.session.commit()
    return redirect("/caja")


# ✏️ ACTUALIZAR CANTIDAD
@app.route("/actualizar_cantidad/<int:index>", methods=["POST"])
def actualizar_cantidad(index):
    cantidad = int(request.form.get("cantidad", 1))
    caja = session.get("caja", [])
    
    if 0 <= index < len(caja):
        if cantidad > 0:
            caja[index]["cantidad"] = cantidad
            caja[index]["precio"] = caja[index].get("precio_unitario", caja[index]["precio"] / caja[index].get("cantidad", 1)) * cantidad
        else:
            caja.pop(index)
    
    session["caja"] = caja
    session.modified = True
    
    return redirect("/caja")

# ❌ QUITAR DE CAJA
@app.route("/quitar/<int:id>")
def quitar(id):
    if session.get("role") != "admin":
        return redirect("/")

    item = CajaItem.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect("/caja")


# 🗑️ LIMPIAR CAJA
@app.route("/limpiar")
def limpiar():
    if session.get("role") != "admin":
        return redirect("/")

    CajaItem.query.filter_by(usuario=session.get("user","admin")).delete()
    db.session.commit()

    return redirect("/caja")


# 💰 COBRAR
@app.route("/cobrar", methods=["GET", "POST"])
def cobrar():
    if session.get("role") != "admin":
        return redirect("/")

    items = CajaItem.query.filter_by(usuario=session.get("user","admin")).all()
    total = sum(i.precio_total for i in items)

    cliente = request.form.get("cliente", "") if request.method == "POST" else ""

    for item in items:
        producto = Producto.query.get(item.producto_id)
        if producto:
            # Registrar venta
            v = Venta(producto=producto.nombre, total=item.precio_total, cantidad=item.cantidad, cliente=cliente)
            db.session.add(v)

            # Descontar stock
            if producto.stock >= item.cantidad:
                producto.stock -= item.cantidad

    # Guardar ticket
    ticket = Ticket(
        fecha=datetime.now(),
        items=json.dumps([{"producto": Producto.query.get(i.producto_id).nombre, "cantidad": i.cantidad, "precio": i.precio_total} for i in items]),
        total=total,
        cliente=cliente
    )
    db.session.add(ticket)

    # Vaciar caja
    CajaItem.query.filter_by(usuario=session.get("user","admin")).delete()
    db.session.commit()

    return redirect("/ticket")


# 🧾 VER ÚLTIMO TICKET
@app.route("/ticket")
def ver_ultimo_ticket():
    if session.get("role") != "admin":
        return redirect("/")
    
    items = session.get("ticket", [])
    total = session.get("ticket_total", 0)
    cliente = session.get("ticket_cliente", "")
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return render_template("ticket.html", items=items, total=total, fecha=fecha, cliente=cliente)

# 📋 LISTA DE TICKETS
@app.route("/tickets")
def tickets():
    if session.get("role") != "admin":
        return redirect("/")
    
    tickets = Ticket.query.order_by(Ticket.fecha.desc()).all()
    return render_template("tickets.html", tickets=tickets)

# 🧾 VER TICKET
@app.route("/ticket/<int:id>")
def ver_ticket(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    ticket = Ticket.query.get(id)
    if ticket:
        items = json.loads(ticket.items)
        return render_template("ticket.html", items=items, total=ticket.total, fecha=ticket.fecha.strftime("%d/%m/%Y %H:%M:%S"), cliente=ticket.cliente if hasattr(ticket, 'cliente') else "")
    return redirect("/tickets")

# ✏️ EDITAR TICKET
@app.route("/editar_ticket/<int:id>", methods=["GET", "POST"])
def editar_ticket(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    ticket = Ticket.query.get(id)
    
    if request.method == "POST":
        ticket.total = float(request.form["total"])
        db.session.commit()
        return redirect("/tickets")
    
    return render_template("editar_ticket.html", ticket=ticket)

# 🗑️ ELIMINAR TICKET
@app.route("/eliminar_ticket/<int:id>")
def eliminar_ticket(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    ticket = Ticket.query.get(id)
    if ticket:
        db.session.delete(ticket)
        db.session.commit()
    
    return redirect("/tickets")

# 📊 VENTAS
@app.route("/ventas")
def ventas():
    if session.get("role") != "admin":
        return redirect("/")

    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    
    # Agrupar por día
    ventas_por_dia = {}
    for v in ventas:
        dia = v.fecha.strftime("%Y-%m-%d")
        if dia not in ventas_por_dia:
            ventas_por_dia[dia] = []
        ventas_por_dia[dia].append(v)
    
    return render_template("ventas.html", ventas=ventas, ventas_por_dia=ventas_por_dia)

# ✏️ EDITAR VENTA
@app.route("/editar_venta/<int:id>", methods=["GET", "POST"])
def editar_venta(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    venta = Venta.query.get(id)
    
    if request.method == "POST":
        venta.producto = request.form["producto"]
        venta.cantidad = int(request.form["cantidad"])
        venta.total = float(request.form["total"])
        venta.cliente = request.form.get("cliente", "")
        db.session.commit()
        return redirect("/ventas")
    
    return render_template("editar_venta.html", venta=venta)

# 🗑️ ELIMINAR VENTA
@app.route("/eliminar_venta/<int:id>")
def eliminar_venta(id):
    if session.get("role") != "admin":
        return redirect("/")
    
    venta = Venta.query.get(id)
    if venta:
        db.session.delete(venta)
        db.session.commit()
    
    return redirect("/ventas")

# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

    # =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

