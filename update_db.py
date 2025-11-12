"""
Veritabanını güncelleme scripti - category sütunu ekle
"""
import sqlite3
from datetime import datetime

DB_NAME = 'diyet_takip.db'

def update_database():
    """Veritabanına category sütunu ekle"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Category sütunu var mı kontrol et
        cursor.execute("PRAGMA table_info(foods)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            print("Category sutunu ekleniyor...")
            cursor.execute('ALTER TABLE foods ADD COLUMN category TEXT')
            conn.commit()
            print("OK: Category sutunu eklendi!")
        else:
            print("OK: Category sutunu zaten mevcut!")
        
        # Mevcut besinlerin category'sini güncelle (opsiyonel)
        # Bu adımı atlayabiliriz, sadece yeni besinler için kategori kullanacağız
        
    except Exception as e:
        print(f"HATA: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    update_database()

