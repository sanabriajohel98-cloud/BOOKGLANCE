#!/usr/bin/env python
"""
Script para inicializar la base de datos.
Se ejecuta automáticamente en Render/Heroku antes de iniciar la app.
"""
import os
from app import app, db, Producto

def init_database():
    """Inicializa la base de datos"""
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✅ Base de datos inicializada")
        
        # Verificar si hay productos
        producto_count = Producto.query.count()
        print(f"📊 Productos actuales: {producto_count}")
        
        if producto_count == 0:
            print("💡 No hay productos. Agrega algunos desde el panel de administración.")
        else:
            print("✓ Base de datos lista para usar")

if __name__ == '__main__':
    init_database()
