"""
Örnek besin veritabanını doldur
"""
import sqlite3
from datetime import datetime

DB_NAME = 'diyet_takip.db'

# Örnek besinler (Türkiye'ye özel)
sample_foods = [
    {'name': 'Tavuk Göğsü (100g)', 'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'serving_size': '100g'},
    {'name': 'Yumurta (1 adet)', 'calories': 70, 'protein': 6, 'carbs': 0.6, 'fat': 5, 'serving_size': '1 adet'},
    {'name': 'Yoğurt (100g)', 'calories': 59, 'protein': 10, 'carbs': 3.6, 'fat': 0.4, 'serving_size': '100g'},
    {'name': 'Pirinç (100g)', 'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'serving_size': '100g'},
    {'name': 'Makarna (100g)', 'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'serving_size': '100g'},
    {'name': 'Ekmek (1 dilim)', 'calories': 80, 'protein': 3, 'carbs': 15, 'fat': 1, 'serving_size': '1 dilim'},
    {'name': 'Muz (1 adet)', 'calories': 105, 'protein': 1.3, 'carbs': 27, 'fat': 0.4, 'serving_size': '1 adet'},
    {'name': 'Elma (1 adet)', 'calories': 95, 'protein': 0.5, 'carbs': 25, 'fat': 0.3, 'serving_size': '1 adet'},
    {'name': 'Balık (100g)', 'calories': 206, 'protein': 22, 'carbs': 0, 'fat': 12, 'serving_size': '100g'},
    {'name': 'Kırmızı Et (100g)', 'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17, 'serving_size': '100g'},
    {'name': 'Süt (200ml)', 'calories': 122, 'protein': 6.4, 'carbs': 9.6, 'fat': 5, 'serving_size': '200ml'},
    {'name': 'Peynir (50g)', 'calories': 150, 'protein': 10, 'carbs': 1, 'fat': 12, 'serving_size': '50g'},
    {'name': 'Zeytin (10 adet)', 'calories': 59, 'protein': 0.6, 'carbs': 0.5, 'fat': 6, 'serving_size': '10 adet'},
    {'name': 'Salata (100g)', 'calories': 15, 'protein': 1, 'carbs': 3, 'fat': 0.2, 'serving_size': '100g'},
    {'name': 'Domates (1 adet)', 'calories': 22, 'protein': 1.1, 'carbs': 4.8, 'fat': 0.2, 'serving_size': '1 adet'},
]

def add_sample_foods():
    """Örnek besinleri veritabanına ekle"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Mevcut besinleri kontrol et
    cursor.execute('SELECT COUNT(*) FROM foods')
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Veritabani zaten {count} besin iceriyor. Ekleniyor...")
    
    # Örnek besinleri ekle
    for food in sample_foods:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO foods (name, calories, protein, carbs, fat, serving_size, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                food['name'],
                food['calories'],
                food['protein'],
                food['carbs'],
                food['fat'],
                food['serving_size'],
                datetime.now().isoformat()
            ))
        except Exception as e:
            print(f"Besin eklenemedi ({food['name']}): {e}")
    
    conn.commit()
    conn.close()
    print(f"{len(sample_foods)} ornek besin eklendi!")

if __name__ == '__main__':
    add_sample_foods()

