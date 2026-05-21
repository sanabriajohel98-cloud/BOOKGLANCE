from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookglace_pro")
app.config["UPLOAD_FOLDER"] = "static/images"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

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
    usuario = db.Column(db.String(100))

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, default=1)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    cliente = db.Column(db.String(100))

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

@app.route('/debug')
def debug():
    try:
        return f"✅ DB OK. Tablas: {[t for t in db.metadata.tables.keys()]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('role'):
        return redirect(url_for('admin') if session.get('role') == 'admin' else url_for('tienda'))

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        if usuario == 'admin' and clave == '1234':
            session['role'] = 'admin'
            session['user'] = usuario
            return redirect(url_for('admin'))
        usuario_db = Usuario.query.filter_by(nombre=usuario, password=clave).first()
        if usuario_db:
            session['role'] = 'user'
            session['user'] = usuario
            return redirect(url_for('tienda'))
        return render_template('login.html', error='Credenciales inválidas')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        if not usuario or not clave:
            return render_template('registro.html', error='Completa todos los campos.')
        if Usuario.query.filter_by(nombre=usuario).first():
            return render_template('registro.html', error='El usuario ya existe.')
        nuevo = Usuario(nombre=usuario, password=clave)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        imagen = request.files.get('imagen')
        imagen_filename = None
        if imagen and imagen.filename:
            imagen_filename = imagen.filename
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))
        nuevo = Producto(
            codigo=codigo,
            nombre=nombre,
            precio=float(precio or 0),
            stock=int(stock or 0),
            imagen=imagen_filename
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('admin'))
    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if session.get('role') != 'admin':
        return redirect('/')
    producto = Producto.query.get(id)
    if not producto:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        producto.codigo = request.form.get('codigo', producto.codigo)
        producto.nombre = request.form.get('nombre', producto.nombre)
        try:
            producto.precio = float(request.form.get('precio', producto.precio))
            producto.stock = int(request.form.get('stock', producto.stock))
        except ValueError:
            return '❌ Error: precio o stock inválido'
        imagen = request.files.get('imagen')
        if imagen and imagen.filename.strip():
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], imagen.filename)
            imagen.save(ruta)
            producto.imagen = imagen.filename
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('editar.html', producto=producto)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if session.get('role') != 'admin':
        return redirect('/')
    p = Producto.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/tienda')
def tienda():
    productos = Producto.query.all()
    return render_template('tienda.html', productos=productos)

@app.route('/caja')
def caja():
    if session.get('role') != 'admin':
        return redirect('/')
    caja_items = CajaItem.query.filter_by(usuario=session.get('user', 'admin')).all()
    total = sum(i.precio_total or 0 for i in caja_items)
    productos = Producto.query.all()
    return render_template('caja.html', caja=caja_items, total=total, productos=productos)

@app.route('/buscar')
def buscar():
    q = request.args.get('q', '')
    productos = Producto.query.filter(
        (Producto.nombre.ilike(f"%{q}%")) |
        (Producto.codigo.ilike(f"%{q}%"))
    ).all() if q else Producto.query.all()
    caja_items = CajaItem.query.filter_by(usuario=session.get('user', 'admin')).all()
    total = sum(i.precio_total or 0 for i in caja_items)
    return render_template('caja.html', caja=caja_items, total=total, productos=productos)

@app.route('/actualizar_cantidad/<int:id>', methods=['POST'])
def actualizar_cantidad(id):
    if session.get('role') != 'admin':
        return redirect('/')
    cantidad = int(request.form.get('cantidad', 1))
    item = CajaItem.query.get(id)
    if item:
        if cantidad > 0:
            producto = Producto.query.get(item.producto_id)
            item.cantidad = cantidad
            item.precio_total = (producto.precio * cantidad) if producto else item.precio_total
            db.session.commit()
        else:
            db.session.delete(item)
            db.session.commit()
    return redirect(url_for('caja'))

@app.route('/agregar/<int:id>')
def agregar(id):
    if session.get('role') != 'admin':
        return redirect('/')
    producto = Producto.query.get(id)
    if not producto:
        return redirect(url_for('caja'))
    usuario = session.get('user', 'admin')
    item = CajaItem.query.filter_by(producto_id=producto.id, usuario=usuario).first()
    if item:
        item.cantidad += 1
        item.precio_total = producto.precio * item.cantidad
    else:
        item = CajaItem(producto_id=producto.id, cantidad=1, precio_total=producto.precio, usuario=usuario)
        db.session.add(item)
    db.session.commit()
    return redirect(url_for('caja'))

@app.route('/quitar/<int:id>')
def quitar(id):
    if session.get('role') != 'admin':
        return redirect('/')
    item = CajaItem.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('caja'))

@app.route('/limpiar')
def limpiar():
    if session.get('role') != 'admin':
        return redirect('/')
    CajaItem.query.filter_by(usuario=session.get('user', 'admin')).delete()
    db.session.commit()
    return redirect(url_for('caja'))

@app.route('/cobrar', methods=['GET', 'POST'])
def cobrar():
    if session.get('role') != 'admin':
        return redirect('/')
    items = CajaItem.query.filter_by(usuario=session.get('user', 'admin')).all()
    total = sum(i.precio_total or 0 for i in items)
    cliente = request.form.get('cliente', '') if request.method == 'POST' else ''
    for item in items:
        producto = Producto.query.get(item.producto_id)
        if producto:
            v = Venta(producto=producto.nombre, total=item.precio_total or 0, cantidad=item.cantidad, cliente=cliente)
            db.session.add(v)
            if producto.stock >= item.cantidad:
                producto.stock -= item.cantidad
    ticket = Ticket(
        fecha=datetime.now(),
        items=json.dumps([
            {"producto": Producto.query.get(i.producto_id).nombre if Producto.query.get(i.producto_id) else None,
             "cantidad": i.cantidad, "precio": i.precio_total}
            for i in items
        ]),
        total=total,
        cliente=cliente
    )
    db.session.add(ticket)
    CajaItem.query.filter_by(usuario=session.get('user', 'admin')).delete()
    db.session.commit()
    return redirect(url_for('ticket'))

@app.route('/ticket')
def ticket():
    if session.get('role') != 'admin':
        return redirect('/')
    items = session.get('ticket', [])
    total = session.get('ticket_total', 0)
    cliente = session.get('ticket_cliente', '')
    fecha = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    return render_template('ticket.html', items=items, total=total, fecha=fecha, cliente=cliente)

@app.route('/tickets')
def tickets():
    if session.get('role') != 'admin':
        return redirect('/')
    tickets = Ticket.query.order_by(Ticket.fecha.desc()).all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/ticket/<int:id>')
def ver_ticket(id):
    if session.get('role') != 'admin':
        return redirect('/')
    ticket = Ticket.query.get(id)
    if ticket:
        items = json.loads(ticket.items)
        return render_template('ticket.html', items=items, total=ticket.total, fecha=ticket.fecha.strftime('%d/%m/%Y %H:%M:%S'), cliente=ticket.cliente or '')
    return redirect(url_for('tickets'))

@app.route('/editar_ticket/<int:id>', methods=['GET', 'POST'])
def editar_ticket(id):
    if session.get('role') != 'admin':
        return redirect('/')
    ticket = Ticket.query.get(id)
    if request.method == 'POST':
        ticket.total = float(request.form['total'])
        db.session.commit()
        return redirect(url_for('tickets'))
    return render_template('editar_ticket.html', ticket=ticket)

@app.route('/eliminar_ticket/<int:id>')
def eliminar_ticket(id):
    if session.get('role') != 'admin':
        return redirect('/')
    ticket = Ticket.query.get(id)
    if ticket:
        db.session.delete(ticket)
        db.session.commit()
    return redirect(url_for('tickets'))

@app.route('/ventas')
def ventas():
    if session.get('role') != 'admin':
        return redirect('/')
    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    ventas_por_dia = {}
    for v in ventas:
        dia = v.fecha.strftime('%Y-%m-%d')
        ventas_por_dia.setdefault(dia, []).append(v)
    return render_template('ventas.html', ventas=ventas, ventas_por_dia=ventas_por_dia)

@app.route('/editar_venta/<int:id>', methods=['GET', 'POST'])
def editar_venta(id):
    if session.get('role') != 'admin':
        return redirect('/')
    venta = Venta.query.get(id)
    if request.method == 'POST':
        venta.producto = request.form['producto']
        venta.cantidad = int(request.form['cantidad'])
        venta.total = float(request.form['total'])
        venta.cliente = request.form.get('cliente', '')
        db.session.commit()
        return redirect(url_for('ventas'))
    return render_template('editar_venta.html', venta=venta)

@app.route('/eliminar_venta/<int:id>')
def eliminar_venta(id):
    if session.get('role') != 'admin':
        return redirect('/')
    venta = Venta.query.get(id)
    if venta:
        db.session.delete(venta)
        db.session.commit()
    return redirect(url_for('ventas'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
