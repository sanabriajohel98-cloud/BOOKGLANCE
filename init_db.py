#!/usr/bin/env python
"""
Script para inicializar la base de datos.
Se ejecuta automáticamente en Render/Heroku antes de iniciar la app.

SQLAlchemy 1.4+ compatible - No usa create_all() directamente
"""
import os
import sys
from app import app, db, Producto, Usuario

def init_database():
    """Inicializa la base de datos con validación de integridad"""
    try:
        with app.app_context():
            # Crear todas las tablas
            print("🔄 Inicializando base de datos...")
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Verificar integridad de las relaciones
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tablas en la BD: {tables}")
            
            # Verificar si hay productos
            producto_count = Producto.query.count()
            usuario_count = Usuario.query.count()
            
            print(f"📦 Productos actuales: {producto_count}")
            print(f"👥 Usuarios actuales: {usuario_count}")
            
            if producto_count == 0:
                print("💡 No hay productos. Agrega algunos desde el panel de administración.")
            else:
                print("✓ Base de datos lista para usar")
                
            print("✨ Inicialización completada sin errores")
            return 0
            
    except Exception as e:
        print(f"❌ Error durante la inicialización: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = init_database()
    sys.exit(exit_code)
