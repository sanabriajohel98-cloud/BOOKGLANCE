# 📚 Bookglance - Tienda Online con Sistema POS

Tienda online con sistema de caja POS integrado, desarrollada con Flask y SQLAlchemy.

## 🖥️ Local (SQLite)

### Primera vez (crear base de datos)
```bash
flask db init
flask db migrate -m "Inicial"
flask db upgrade
```

### Desarrollo local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

Acceso: `http://localhost:5000`

## 👤 Credenciales de Login

- **Admin**: `Johel` / `Johel123`
- **Usuarios normales**: Crear cuenta en el registro

## 🚀 Despliegue en Render

### 1. Crear cuenta
Ve a [render.com](https://render.com)

### 2. Crear base de datos PostgreSQL
- Dashboard → "New" → "PostgreSQL"
- Nombre: `bookglance-db`
- Guarda la URL de conexión

### 3. Crear Web Service
- "New" → "Web Service"
- Conecta tu repositorio GitHub
- **Build Command**: (dejar vacío)
- **Start Command**: `gunicorn app:app`
- **Environment Variables**:
  - `DATABASE_URL`: pega la URL de PostgreSQL
  - `SECRET_KEY`: genera una clave segura

### 4. Subir imágenes
- Los productos necesitan imágenes en la carpeta `static/images`
- Usa el panel de Render o un bucket externo (Cloudinary)

## 📋 Características

✅ Autenticación de usuarios  
✅ Panel de administración  
✅ Gestión de productos  
✅ Sistema de caja POS  
✅ Historial de ventas  
✅ Generación de tickets  
✅ Subida de imágenes de productos  

## 🗄️ Base de Datos

- **Usuario**: usuarios registrados
- **Producto**: catálogo de productos
- **CajaItem**: items temporales en la caja
- **Venta**: historial de ventas
- **Ticket**: tickets de ventas

## ⚙️ Configuración

- SQLite para desarrollo
- PostgreSQL para producción
- Flask-Migrate para migraciones
- Bootstrap 5 para UI

---

**Desarrollado con ❤️ usando Flask**
