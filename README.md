# 📚 Bookglance - Tienda Online con Sistema POS

Sistema de punto de venta (POS) integrado con tienda online, desarrollado con Flask y SQLAlchemy.

---

## 🎯 Características

✅ Autenticación de usuarios  
✅ Panel de administración  
✅ Gestión de productos (crear, editar, eliminar)  
✅ Sistema de caja POS  
✅ Historial de ventas  
✅ Generación de tickets  
✅ Subida de imágenes de productos  
✅ **Base de datos persistente** ✨  
✅ Compatible con PostgreSQL y SQLite  

---

## 🖥️ Desarrollo Local (SQLite)

### 1️⃣ Clonar repositorio
```bash
git clone https://github.com/sanabriajohel98-cloud/BOOKGLANCE.git
cd BOOKGLANCE
```

### 2️⃣ Crear entorno virtual
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ Crear archivo .env (opcional)
```bash
cp .env.example .env
```

O crear `.env` manualmente:
```
SECRET_KEY=tu_clave_secreta_aqui
FLASK_ENV=development
```

### 5️⃣ Ejecutar la aplicación
```bash
python app.py
```

**Acceso:** `http://localhost:5000`

**Base de datos:** Se crea automáticamente en `bookglance.db` y es **PERSISTENTE** ✅

---

## 👤 Credenciales de Login

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `Johel` | `Johel123` | Admin |
| — | — | Crear en Registro |

---

## 🚀 Despliegue en Render (PRODUCCIÓN)

### 1️⃣ Crear cuenta en [render.com](https://render.com)

### 2️⃣ Crear Base de Datos PostgreSQL

1. Click en **"New"** → **"PostgreSQL"**
2. **Name:** `bookglance-db`
3. **Region:** Selecciona la más cercana
4. **Plan:** Free (o pagado según necesidad)
5. **Guardar** la URL de conexión (la necesitarás en el paso 4)

**Ejemplo de URL:**
```
postgresql://user:password@dpg-xxx.render.internal/bookglance_db
```

### 3️⃣ Crear Web Service

1. Click en **"New"** → **"Web Service"**
2. **Repository:** Conecta tu repositorio GitHub
3. **Name:** `bookglance`
4. **Region:** Igual a la BD
5. **Branch:** `main`
6. **Runtime:** Python 3
7. **Build Command:** (Dejar vacío)
8. **Start Command:** 
   ```
   gunicorn app:app
   ```

### 4️⃣ Configurar Variables de Entorno

En la sección **"Environment"** del Web Service, agregar:

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | Pega la URL de PostgreSQL del paso 2 |
| `SECRET_KEY` | Genera una clave segura (ej: `openssl rand -base64 32`) |
| `FLASK_ENV` | `production` |

### 5️⃣ Deploy

- Click en **"Create Web Service"**
- Render desplegará automáticamente
- La URL se mostrará en el dashboard

**Acceso:** `https://bookglance.render.com` (la URL exacta aparecerá en el dashboard)

---

## 💾 Persistencia de Datos

### ✅ Desarrollo Local (SQLite)
- Datos guardados en `bookglance.db`
- **PERSISTENTE** entre reinicios
- Se actualiza con cada cambio
- Archivo local en el proyecto

### ✅ Producción (PostgreSQL)
- Datos guardados en BD de Render
- **Completamente persistente**
- Independiente del servidor web
- Automático con la URL `DATABASE_URL`

---

## 📁 Estructura del Proyecto

```
BOOKGLANCE/
├── app.py                 # Aplicación principal (Flask)
├── init_db.py            # Script de inicialización
├── requirements.txt      # Dependencias Python
├── .env.example          # Variables de entorno (ejemplo)
├── .gitignore            # Archivos a ignorar en git
├── Procfile              # Configuración para Render
├── runtime.txt           # Versión de Python
├── static/
│   └── images/           # Imágenes de productos
├── templates/
│   ├── login.html
│   ├── admin.html
│   ├── caja.html
│   ├── ticket.html
│   └── ...
└── README.md
```

---

## 🗄️ Modelos de Base de Datos

| Tabla | Descripción | Persistencia |
|-------|------------|---|
| **Usuario** | Usuarios registrados | ✅ Permanente |
| **Producto** | Catálogo de productos | ✅ Permanente |
| **CajaItem** | Items temporales en caja | ✅ Permanente hasta cobrar |
| **Venta** | Historial de ventas | ✅ Permanente |
| **Ticket** | Tickets generados | ✅ Permanente |

---

## 🔧 Guía de Uso

### Para Administradores

1. **Login** con `Johel` / `Johel123`
2. **Panel Admin** - Agregar productos:
   - Código (único)
   - Nombre
   - Precio
   - Stock
   - Imagen (PNG, JPG, GIF)

3. **Ver productos** - Se guardan automáticamente ✅

### Para Vendedores

1. **Crear cuenta** en Registro
2. **Login** con tu usuario
3. **Ir a Caja POS**
4. **Agregar productos** a la venta
5. **Cobrar** - Se genera ticket automáticamente

---

## ⚠️ Solución de Problemas

### ❓ Los productos desaparecen
**✅ SOLUCIONADO:** El archivo `.gitignore` fue actualizado para permitir `bookglance.db`

**En Render:**
- Verificar que `DATABASE_URL` esté en variables de entorno
- Los datos se guardan en PostgreSQL de Render

### ❓ Error: "No such table"
**Solución:**
```bash
# Local
rm bookglance.db  # Eliminar BD antigua
python app.py      # Reiniciar (crea nueva BD)
```

**En Render:**
- Ir a Environment → Reiniciar Web Service

### ❓ Imágenes no cargan
1. Verificar que `static/images/` exista
2. Usar rutas relativas en HTML
3. En Render, subir imágenes locales (se pierden entre deploys)

---

## 🔒 Seguridad

- ✅ Validación de sesión en rutas protegidas
- ✅ Variables de entorno para información sensible
- ⚠️ **TODO:** Agregar hashing de contraseñas (bcrypt)
- ⚠️ **TODO:** CSRF protection

---

## 🛠️ Stack Tecnológico

| Componente | Versión |
|-----------|---------|
| **Framework** | Flask 3.0 |
| **Base de Datos** | SQLite (local) / PostgreSQL (prod) |
| **ORM** | SQLAlchemy 3.1 |
| **Servidor Web** | Gunicorn 21.2 |
| **Frontend** | HTML5 + Bootstrap 5 |
| **Hosting** | Render |

---

## 📝 Próximas Mejoras

- [ ] Hashing de contraseñas con bcrypt
- [ ] Validación CSRF con Flask-WTF
- [ ] API REST para cliente móvil
- [ ] Integración de Cloudinary para imágenes persistentes
- [ ] Reportes avanzados con gráficos
- [ ] Backup automático de datos
- [ ] Dashboard de ventas en tiempo real

---

## 📞 Soporte

Para reportar problemas o sugerencias, abre un [issue](https://github.com/sanabriajohel98-cloud/BOOKGLANCE/issues).

---

**Desarrollado con ❤️ usando Flask**

**Última actualización:** Mayo 2026 ✅
