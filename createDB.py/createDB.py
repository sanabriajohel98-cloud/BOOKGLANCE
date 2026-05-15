# createDB.py
from app import app, db
from flask_migrate import upgrade

with app.app_context():
      upgrade()  # aplica las migraciones pendientes
      print("✅ Migraciones aplicadas correctamente, productos e imágenes conservados.")
