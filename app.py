from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookglance_pro_secure_key_2024")
app.config["UPLOAD_FOLDER"] = "static/images"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ==================== ADMINS PREDETERMINADOS ====================
# FÁCIL: Agrega aquí más admins sin modificar el código
ADMIN_USERS = {
    'Johel': 'Johel123',
    'Nawel': 'Nawe123',
    # Agregar más admins aquí:
    # 'usuario': 'contraseña',
}

# Configuración de base de datos
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Heroku usa postgres://, pero SQLAlchemy 1.4+ requiere postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # SQLite para desarrollo local
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookglance.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ==================== MODELOS DE BASE DE DATOS ====================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(200))
    creado = db.Column(db.DateTime, default=datetime.now)
    # Relación inversa con CajaItem
    caja_items = db.relationship("CajaItem", back_populates="producto", cascade="all, delete-orphan")

class CajaItem(db.Model):
    __tablename__ = 'cajaitem'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="caja_items")
    cantidad = db.Column(db.Integer, default=1)
    precio_total = db.Column(db.Float, nullable=False)
    usuario = db.Column(db.String(100), nullable=False)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    total = db.Column(db.Float, nullable=False)
    cliente = db.Column(db.String(100))

class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.Column(db.Text, nullable=False)
    total = db.Column(db.Float, nullable=False)
    cliente = db.Column(db.String(100))

# ==================== FUNCIONES DE VALIDACIÓN ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validar_sesion_usuario():
    """Valida que el usuario esté autenticado (admin o user)"""
    if not session.get("role"):
        return redirect(url_for("login"))
    return None

def validar_sesion_admin():
    """Valida que el usuario esté autenticado como admin"""
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return None

def init_db():
    """Inicializa la base de datos y carga datos de ejemplo"""
    with app.app_context():
        db.create_all()
        
        # Verificar si ya existen productos
        if Producto.query.first() is None:
            productos_demo = [
                Producto(codigo="P001", nombre="Lapicera Azul", precio=5000, stock=100),
                Producto(codigo="P002", nombre="Cuaderno A4", precio=15000, stock=50),
                Producto(codigo="P003", nombre="Regla 30cm", precio=3000, stock=200),
            ]
            db.session.bulk_save_objects(productos_demo)
            db.session.commit()
            print("✅ Base de datos inicializada con productos de prueba.")
        else:
            print("✅ Base de datos ya contiene datos.")


# ==================== RUTAS PÚBLICAS ====================

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
        usuario = request.form.get('usuario', '').strip()
        clave = request.form.get('clave', '').strip()
        
        if not usuario or not clave:
            return render_template('login.html', error='Usuario y contraseña requeridos')
        
        # Verificar si es admin predeterminado
        if usuario in ADMIN_USERS and ADMIN_USERS[usuario] == clave:
            session['role'] = 'admin'
            session['user'] = usuario
            return redirect(url_for('admin'))
        
        # Usuarios registrados
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
        usuario = request.form.get('usuario', '').strip()
        clave = request.form.get('clave', '').strip()
        
        if not usuario or not clave:
            return render_template('registro.html', error='Completa todos los campos.')
        
        if Usuario.query.filter_by(nombre=usuario).first():
            return render_template('registro.html', error='El usuario ya existe.')
        
        # Evitar que registren nombres de admins
        if usuario in ADMIN_USERS:
            return render_template('registro.html', error='Este usuario está reservado.')
        
        nuevo = Usuario(nombre=usuario, password=clave)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('registro.html')

# ==================== RUTAS DE ADMINISTRACIÓN ====================

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    check = validar_sesion_admin()
    if check:
        return check
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        nombre = request.form.get('nombre', '').strip()
        precio_str = request.form.get('precio', '0')
        stock_str = request.form.get('stock', '0')
        
        if not nombre:
            return render_template('admin.html', error='Nombre del producto requerido', productos=Producto.query.all())
        
        try:
            precio = float(precio_str)
            stock = int(stock_str)
        except ValueError:
            return render_template('admin.html', error='Precio o stock inválidos', productos=Producto.query.all())
        
        if codigo and Producto.query.filter_by(codigo=codigo).first():
            return render_template('admin.html', error='El código ya existe', productos=Producto.query.all())
        
        imagen = request.files.get('imagen')
        imagen_filename = None
        
        if imagen and imagen.filename and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            imagen_filename = timestamp + filename
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))
        
        nuevo = Producto(
            codigo=codigo,
            nombre=nombre,
            precio=precio,
            stock=stock,
            imagen=imagen_filename
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('admin'))
    
    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    check = validar_sesion_admin()
    if check:
        return check
    
    producto = Producto.query.get(id)
    if not producto:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        producto.codigo = request.form.get('codigo', producto.codigo).strip()
        producto.nombre = request.form.get('nombre', producto.nombre).strip()
        
        try:
            precio_str = request.form.get('precio', str(producto.precio))
            stock_str = request.form.get('stock', str(producto.stock))
            producto.precio = float(precio_str)
            producto.stock = int(stock_str)
        except ValueError:
            return render_template('editar.html', producto=producto, error='Precio o stock inválidos')
        
        imagen = request.files.get('imagen')
        if imagen and imagen.filename and imagen.filename.strip() and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(ruta)
            producto.imagen = filename
        
        db.session.commit()
        return redirect(url_for('admin'))
    
    return render_template('editar.html', producto=producto)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    check = validar_sesion_admin()
    if check:
        return check
    
    p = Producto.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    
    return redirect(url_for('admin'))

# ==================== RUTAS DE TIENDA ====================

@app.route('/tienda')
def tienda():
    check = validar_sesion_usuario()
    if check:
        return check
    
    productos = Producto.query.all()
    return render_template('tienda.html', productos=productos)

@app.route('/caja')
def caja():
    check = validar_sesion_usuario()
    if check:
        return check
    
    usuario_actual = session.get('user', 'admin')
    caja_items = CajaItem.query.filter_by(usuario=usuario_actual).all()
    total = sum(i.precio_total or 0 for i in caja_items)
    productos = Producto.query.all()
    fecha = datetime.now().strftime('%d/%m/%Y %H:%M')

    return render_template('caja.html', caja=caja_items, total=total, productos=productos, fecha=fecha)

@app.route('/buscar')
def buscar():
    check = validar_sesion_usuario()
    if check:
        return check
    
    q = request.args.get('q', '').strip()
    
    if q:
        productos = Producto.query.filter(
            (Producto.nombre.ilike(f"%{q}%")) |
            (Producto.codigo.ilike(f"%{q}%"))
        ).all()
    else:
        productos = Producto.query.all()
    
    usuario_actual = session.get('user', 'admin')
    caja_items = CajaItem.query.filter_by(usuario=usuario_actual).all()
    total = sum(i.precio_total or 0 for i in caja_items)
    
    return render_template('caja.html', caja=caja_items, total=total, productos=productos)

@app.route('/actualizar_cantidad/<int:id>', methods=['POST'])
def actualizar_cantidad_item(id):
    check = validar_sesion_usuario()
    if check:
        return check
    
    try:
        cantidad = int(request.form.get('cantidad', 1))
    except ValueError:
        return redirect(url_for('caja'))
    
    item = CajaItem.query.get(id)
    if item:
        if cantidad > 0:
            producto = Producto.query.get(item.producto_id)
            if producto:
                item.cantidad = cantidad
                item.precio_total = producto.precio * cantidad
                db.session.commit()
        else:
            db.session.delete(item)
            db.session.commit()
    
    return redirect(url_for('caja'))

@app.route('/agregar/<int:id>')
def agregar(id):
    check = validar_sesion_usuario()
    if check:
        return check
    
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
    check = validar_sesion_usuario()
    if check:
        return check
    
    item = CajaItem.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    
    return redirect(url_for('caja'))

@app.route('/limpiar')
def limpiar():
    check = validar_sesion_usuario()
    if check:
        return check
    
    usuario_actual = session.get('user', 'admin')
    CajaItem.query.filter_by(usuario=usuario_actual).delete()
    db.session.commit()
    
    return redirect(url_for('caja'))

@app.route('/cobrar', methods=['GET', 'POST'])
def cobrar():
    check = validar_sesion_usuario()
    if check:
        return check
    
    usuario_actual = session.get('user', 'admin')
    items = CajaItem.query.filter_by(usuario=usuario_actual).all()
    total = sum(i.precio_total or 0 for i in items)
    cliente = request.form.get('cliente', '') if request.method == 'POST' else ''
    
    if request.method == 'POST':
        if not items:
            return render_template('cobrar.html', items=items, total=total, cliente=cliente, error='No hay items en la caja')
        
        for item in items:
            producto = Producto.query.get(item.producto_id)
            if producto:
                v = Venta(producto=producto.nombre, total=item.precio_total or 0, cantidad=item.cantidad, cliente=cliente)
                db.session.add(v)
                if producto.stock >= item.cantidad:
                    producto.stock -= item.cantidad
        
        items_json = []
        for i in items:
            producto = Producto.query.get(i.producto_id)
            if producto:
                items_json.append({
                    "producto": producto.nombre,
                    "cantidad": i.cantidad,
                    "precio": i.precio_total
                })
        
        ticket = Ticket(
            fecha=datetime.now(),
            items=json.dumps(items_json),
            total=total,
            cliente=cliente
        )
        db.session.add(ticket)
        CajaItem.query.filter_by(usuario=usuario_actual).delete()
        db.session.commit()
        return redirect(url_for('ticket_ultima'))
    
    return render_template('cobrar.html', items=items, total=total, cliente=cliente)

@app.route('/ticket')
def ticket_ultima():
    check = validar_sesion_usuario()
    if check:
        return check
    
    ultimo_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    
    if ultimo_ticket:
        items = json.loads(ultimo_ticket.items)
        fecha = ultimo_ticket.fecha.strftime('%d/%m/%Y %H:%M:%S')
        return render_template('ticket.html', items=items, total=ultimo_ticket.total, fecha=fecha, cliente=ultimo_ticket.cliente)
    
    return render_template('ticket.html', items=[], total=0, fecha='', cliente='')

@app.route('/tickets')
def tickets():
    check = validar_sesion_usuario()
    if check:
        return check
    
    tickets_list = Ticket.query.order_by(Ticket.fecha.desc()).all()
    return render_template('tickets.html', tickets=tickets_list)

@app.route('/ticket/<int:id>')
def ver_ticket(id):
    check = validar_sesion_usuario()
    if check:
        return check
    
    ticket = Ticket.query.get(id)
    if ticket:
        items = json.loads(ticket.items)
        fecha = ticket.fecha.strftime('%d/%m/%Y %H:%M:%S')
        cliente = ticket.cliente or ''
        return render_template('ticket.html', items=items, total=ticket.total, fecha=fecha, cliente=cliente)
    
    return redirect(url_for('tickets'))

@app.route('/editar_ticket/<int:id>', methods=['GET', 'POST'])
def editar_ticket(id):
    check = validar_sesion_admin()
    if check:
        return check
    
    ticket = Ticket.query.get(id)
    if not ticket:
        return redirect(url_for('tickets'))
    
    if request.method == 'POST':
        try:
            ticket.total = float(request.form.get('total', ticket.total))
            db.session.commit()
            return redirect(url_for('tickets'))
        except ValueError:
            return render_template('editar_ticket.html', ticket=ticket, error='Total inválido')
    
    return render_template('editar_ticket.html', ticket=ticket)

@app.route('/eliminar_ticket/<int:id>')
def eliminar_ticket(id):
    check = validar_sesion_admin()
    if check:
        return check
    
    ticket = Ticket.query.get(id)
    if ticket:
        db.session.delete(ticket)
        db.session.commit()
    
    return redirect(url_for('tickets'))

@app.route('/ventas')
def ventas():
    check = validar_sesion_admin()
    if check:
        return check
    
    ventas_list = Venta.query.order_by(Venta.fecha.desc()).all()
    ventas_por_dia = {}
    
    for v in ventas_list:
        dia = v.fecha.strftime('%Y-%m-%d')
        ventas_por_dia.setdefault(dia, []).append(v)
    
    return render_template('ventas.html', ventas=ventas_list, ventas_por_dia=ventas_por_dia)

@app.route('/editar_venta/<int:id>', methods=['GET', 'POST'])
def editar_venta(id):
    check = validar_sesion_admin()
    if check:
        return check
    
    venta = Venta.query.get(id)
    if not venta:
        return redirect(url_for('ventas'))
    
    if request.method == 'POST':
        try:
            venta.producto = request.form.get('producto', venta.producto)
            venta.cantidad = int(request.form.get('cantidad', venta.cantidad))
            venta.total = float(request.form.get('total', venta.total))
            venta.cliente = request.form.get('cliente', '')
            db.session.commit()
            return redirect(url_for('ventas'))
        except ValueError:
            return render_template('editar_venta.html', venta=venta, error='Datos inválidos')
    
    return render_template('editar_venta.html', venta=venta)

@app.route('/eliminar_venta/<int:id>')
def eliminar_venta(id):
    check = validar_sesion_admin()
    if check:
        return check
    
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
    # Solo crear tablas si no existen (para desarrollo local)
    if not os.environ.get("RENDER"):
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
