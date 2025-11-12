"""
Veritabani baslatma ve tarif ekleme scripti
"""
import sys
import os

# UTF-8 encoding ayarla (Windows icin)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# app.py'den init_db'yi import et
from app import init_db

# add_recipes.py'den add_recipes'i import et
from add_recipes import add_recipes

if __name__ == '__main__':
    print("Veritabani baslatiliyor...")
    init_db()
    print("Tarifler ekleniyor...")
    add_recipes()
    print("Tamamlandi!")

