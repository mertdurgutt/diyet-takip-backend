"""
Besin Veritabanına Besin Ekleme Scripti
"""
import sqlite3
from datetime import datetime

DB_NAME = 'diyet_takip.db'

# Kapsamlı besin listesi - Türk mutfağı ve yaygın besinler
FOODS = [
    # Meyveler
    ('Elma', 52, 0.3, 14, 0.2, '100g', None, 'Meyve'),
    ('Muz', 89, 1.1, 23, 0.3, '100g', None, 'Meyve'),
    ('Portakal', 47, 0.9, 12, 0.1, '100g', None, 'Meyve'),
    ('Çilek', 32, 0.7, 8, 0.3, '100g', None, 'Meyve'),
    ('Üzüm', 69, 0.7, 18, 0.2, '100g', None, 'Meyve'),
    ('Karpuz', 30, 0.6, 8, 0.2, '100g', None, 'Meyve'),
    ('Kavun', 34, 0.8, 8, 0.2, '100g', None, 'Meyve'),
    ('Armut', 57, 0.4, 15, 0.1, '100g', None, 'Meyve'),
    ('Şeftali', 39, 0.9, 10, 0.3, '100g', None, 'Meyve'),
    ('Kivi', 61, 1.1, 15, 0.5, '100g', None, 'Meyve'),
    ('Ananas', 50, 0.5, 13, 0.1, '100g', None, 'Meyve'),
    ('Avokado', 160, 2, 9, 15, '100g', None, 'Meyve'),
    
    # Sebzeler
    ('Salatalık', 16, 0.7, 4, 0.1, '100g', None, 'Sebze'),
    ('Domates', 18, 0.9, 4, 0.2, '100g', None, 'Sebze'),
    ('Marul', 15, 1.4, 3, 0.2, '100g', None, 'Sebze'),
    ('Ispanak', 23, 2.9, 4, 0.4, '100g', None, 'Sebze'),
    ('Brokoli', 34, 2.8, 7, 0.4, '100g', None, 'Sebze'),
    ('Karnabahar', 25, 1.9, 5, 0.3, '100g', None, 'Sebze'),
    ('Havuç', 41, 0.9, 10, 0.2, '100g', None, 'Sebze'),
    ('Biber (Kırmızı)', 31, 1, 7, 0.3, '100g', None, 'Sebze'),
    ('Patlıcan', 25, 1, 6, 0.2, '100g', None, 'Sebze'),
    ('Kabak', 17, 1.2, 3, 0.2, '100g', None, 'Sebze'),
    ('Soğan', 40, 1.1, 9, 0.1, '100g', None, 'Sebze'),
    ('Sarımsak', 149, 6.4, 33, 0.5, '100g', None, 'Sebze'),
    ('Mantar', 22, 3.1, 3, 0.3, '100g', None, 'Sebze'),
    ('Bezelye', 81, 5.4, 14, 0.4, '100g', None, 'Sebze'),
    ('Fasulye (Yeşil)', 31, 1.8, 7, 0.2, '100g', None, 'Sebze'),
    
    # Et ve Tavuk
    ('Tavuk Göğsü', 165, 31, 0, 3.6, '100g', None, 'Et'),
    ('Tavuk But', 180, 27, 0, 7.4, '100g', None, 'Et'),
    ('Kırmızı Et (Dana)', 250, 26, 0, 15, '100g', None, 'Et'),
    ('Kıyma (Dana)', 250, 26, 0, 15, '100g', None, 'Et'),
    ('Köfte', 295, 26, 8, 18, '100g', None, 'Et'),
    ('Tavuk Kanat', 203, 27, 0, 9.5, '100g', None, 'Et'),
    ('Hindi Göğsü', 135, 30, 0, 1, '100g', None, 'Et'),
    ('Balık (Levrek)', 124, 24, 0, 2.8, '100g', None, 'Et'),
    ('Balık (Somon)', 208, 25, 0, 12, '100g', None, 'Et'),
    ('Balık (Ton)', 184, 30, 0, 6, '100g', None, 'Et'),
    ('Karides', 99, 24, 0, 0.3, '100g', None, 'Et'),
    
    # Süt Ürünleri
    ('Süt (Tam Yağlı)', 61, 3.2, 5, 3.3, '100ml', None, 'Süt Ürünleri'),
    ('Süt (Yağsız)', 34, 3.4, 5, 0.1, '100ml', None, 'Süt Ürünleri'),
    ('Yoğurt (Tam Yağlı)', 59, 10, 4, 0.4, '100g', None, 'Süt Ürünleri'),
    ('Yoğurt (Yağsız)', 59, 10, 4, 0.4, '100g', None, 'Süt Ürünleri'),
    ('Peynir (Beyaz)', 264, 18, 2, 21, '100g', None, 'Süt Ürünleri'),
    ('Peynir (Kaşar)', 350, 25, 2, 27, '100g', None, 'Süt Ürünleri'),
    ('Peynir (Lor)', 85, 11, 3, 3, '100g', None, 'Süt Ürünleri'),
    ('Ayran', 37, 1.5, 3, 1.5, '100ml', None, 'Süt Ürünleri'),
    ('Kefir', 41, 3.3, 4, 1, '100ml', None, 'Süt Ürünleri'),
    ('Tereyağı', 717, 0.9, 0.1, 81, '100g', None, 'Süt Ürünleri'),
    ('Kaymak', 545, 2.5, 4, 57, '100g', None, 'Süt Ürünleri'),
    
    # Yumurta
    ('Yumurta (Bütün)', 70, 6, 0.6, 5, '1 adet', None, 'Yumurta'),
    ('Yumurta (Beyaz)', 17, 3.6, 0.2, 0.1, '1 adet', None, 'Yumurta'),
    ('Yumurta (Sarı)', 55, 2.7, 0.6, 4.5, '1 adet', None, 'Yumurta'),
    
    # Tahıllar ve Bakliyat
    ('Pirinç (Beyaz)', 130, 2.7, 28, 0.3, '100g (pişmiş)', None, 'Tahıl'),
    ('Pirinç (Esmer)', 111, 2.6, 23, 0.9, '100g (pişmiş)', None, 'Tahıl'),
    ('Bulgur', 83, 3.1, 19, 0.2, '100g (pişmiş)', None, 'Tahıl'),
    ('Makarna', 131, 5, 25, 1.1, '100g (pişmiş)', None, 'Tahıl'),
    ('Ekmek (Beyaz)', 265, 9, 49, 3.2, '100g', None, 'Tahıl'),
    ('Ekmek (Tam Buğday)', 247, 13, 41, 4.2, '100g', None, 'Tahıl'),
    ('Ekmek (Çavdar)', 259, 8, 48, 3.3, '100g', None, 'Tahıl'),
    ('Yulaf', 389, 17, 66, 7, '100g', None, 'Tahıl'),
    ('Mısır', 365, 9, 74, 4.7, '100g', None, 'Tahıl'),
    ('Kinoa', 368, 14, 64, 6, '100g', None, 'Tahıl'),
    ('Mercimek', 116, 9, 20, 0.4, '100g (pişmiş)', None, 'Bakliyat'),
    ('Nohut', 164, 8.9, 27, 2.6, '100g (pişmiş)', None, 'Bakliyat'),
    ('Fasulye (Kuru)', 127, 8.7, 23, 0.5, '100g (pişmiş)', None, 'Bakliyat'),
    ('Barbunya', 127, 8.7, 23, 0.5, '100g (pişmiş)', None, 'Bakliyat'),
    
    # Kuruyemiş ve Tohumlar
    ('Badem', 579, 21, 22, 50, '100g', None, 'Kuruyemiş'),
    ('Ceviz', 654, 15, 14, 65, '100g', None, 'Kuruyemiş'),
    ('Fındık', 628, 15, 17, 61, '100g', None, 'Kuruyemiş'),
    ('Fıstık', 567, 26, 16, 49, '100g', None, 'Kuruyemiş'),
    ('Antep Fıstığı', 560, 20, 28, 45, '100g', None, 'Kuruyemiş'),
    ('Kaju', 553, 18, 30, 44, '100g', None, 'Kuruyemiş'),
    ('Çekirdek (Ayçiçeği)', 584, 21, 20, 51, '100g', None, 'Kuruyemiş'),
    ('Çekirdek (Kabak)', 559, 30, 11, 49, '100g', None, 'Kuruyemiş'),
    ('Susam', 573, 18, 23, 50, '100g', None, 'Kuruyemiş'),
    ('Chia Tohumu', 486, 17, 42, 31, '100g', None, 'Kuruyemiş'),
    
    # Yağlar
    ('Zeytinyağı', 884, 0, 0, 100, '100ml', None, 'Yağ'),
    ('Ayçiçek Yağı', 884, 0, 0, 100, '100ml', None, 'Yağ'),
    ('Tereyağı', 717, 0.9, 0.1, 81, '100g', None, 'Yağ'),
    ('Margarin', 717, 0.2, 0.7, 80, '100g', None, 'Yağ'),
    
    # İçecekler
    ('Su', 0, 0, 0, 0, '100ml', None, 'İçecek'),
    ('Çay (Şekersiz)', 2, 0, 0.5, 0, '100ml', None, 'İçecek'),
    ('Kahve (Şekersiz)', 2, 0.1, 0, 0, '100ml', None, 'İçecek'),
    ('Türk Kahvesi', 8, 0.1, 1, 0, '1 fincan', None, 'İçecek'),
    ('Meyve Suyu (Portakal)', 45, 0.7, 10, 0.2, '100ml', None, 'İçecek'),
    ('Meyve Suyu (Elma)', 46, 0.1, 11, 0.1, '100ml', None, 'İçecek'),
    ('Kola', 42, 0, 10, 0, '100ml', None, 'İçecek'),
    ('Gazoz', 40, 0, 10, 0, '100ml', None, 'İçecek'),
    ('Smoothie', 60, 1, 14, 0.2, '100ml', None, 'İçecek'),
    
    # Atıştırmalıklar
    ('Çikolata (Sütlü)', 535, 7.7, 60, 30, '100g', None, 'Atıştırmalık'),
    ('Çikolata (Bitter)', 546, 7.8, 46, 31, '100g', None, 'Atıştırmalık'),
    ('Bisküvi', 450, 7, 70, 16, '100g', None, 'Atıştırmalık'),
    ('Kraker', 465, 9, 65, 17, '100g', None, 'Atıştırmalık'),
    ('Cips', 536, 7, 53, 35, '100g', None, 'Atıştırmalık'),
    ('Kek', 350, 5, 55, 12, '100g', None, 'Atıştırmalık'),
    ('Kurabiye', 480, 6, 65, 22, '100g', None, 'Atıştırmalık'),
    ('Dondurma', 207, 3.5, 24, 11, '100g', None, 'Atıştırmalık'),
    ('Pudding', 130, 3, 20, 4, '100g', None, 'Atıştırmalık'),
    
    # Türk Yemekleri
    ('Döner (Tavuk)', 200, 25, 5, 8, '100g', None, 'Türk Yemekleri'),
    ('Döner (Et)', 250, 28, 3, 12, '100g', None, 'Türk Yemekleri'),
    ('Kebap (Adana)', 320, 28, 2, 22, '100g', None, 'Türk Yemekleri'),
    ('Kebap (Urfa)', 280, 26, 2, 18, '100g', None, 'Türk Yemekleri'),
    ('Lahmacun', 280, 12, 35, 12, '1 adet', None, 'Türk Yemekleri'),
    ('Pide', 350, 15, 45, 12, '100g', None, 'Türk Yemekleri'),
    ('Börek (Peynirli)', 350, 12, 35, 18, '100g', None, 'Türk Yemekleri'),
    ('Börek (Ispanaklı)', 320, 10, 32, 16, '100g', None, 'Türk Yemekleri'),
    ('Mantı', 280, 15, 35, 10, '100g', None, 'Türk Yemekleri'),
    ('Gözleme (Peynirli)', 280, 12, 35, 12, '1 adet', None, 'Türk Yemekleri'),
    ('Gözleme (Ispanaklı)', 250, 10, 32, 10, '1 adet', None, 'Türk Yemekleri'),
    ('Menemen', 120, 8, 8, 7, '100g', None, 'Türk Yemekleri'),
    ('Karnıyarık', 180, 12, 15, 9, '100g', None, 'Türk Yemekleri'),
    ('İmam Bayıldı', 150, 8, 12, 8, '100g', None, 'Türk Yemekleri'),
    ('Mücver', 180, 8, 18, 8, '100g', None, 'Türk Yemekleri'),
    ('Çorba (Mercimek)', 60, 4, 10, 1, '100ml', None, 'Türk Yemekleri'),
    ('Çorba (Domates)', 50, 2, 8, 1.5, '100ml', None, 'Türk Yemekleri'),
    ('Çorba (Tavuk)', 45, 5, 3, 1.5, '100ml', None, 'Türk Yemekleri'),
    ('Çorba (Ezogelin)', 55, 3, 9, 1, '100ml', None, 'Türk Yemekleri'),
    ('Pilav', 130, 2.7, 28, 0.3, '100g', None, 'Türk Yemekleri'),
    ('Makarna (Domates Soslu)', 150, 5, 28, 3, '100g', None, 'Türk Yemekleri'),
    ('Makarna (Bolognese)', 180, 12, 25, 6, '100g', None, 'Türk Yemekleri'),
    ('Izgara Balık', 180, 25, 0, 8, '100g', None, 'Türk Yemekleri'),
    ('Izgara Tavuk', 165, 31, 0, 3.6, '100g', None, 'Türk Yemekleri'),
    
    # Salatalar
    ('Çoban Salata', 50, 2, 8, 2, '100g', None, 'Salata'),
    ('Mevsim Salata', 30, 2, 5, 1, '100g', None, 'Salata'),
    ('Roka Salatası', 25, 3, 4, 0.7, '100g', None, 'Salata'),
    ('Sezar Salata', 180, 8, 12, 12, '100g', None, 'Salata'),
    ('Cacık', 60, 3, 4, 3, '100g', None, 'Salata'),
    
    # Tatlılar
    ('Baklava', 450, 8, 55, 22, '100g', None, 'Tatlı'),
    ('Künefe', 350, 8, 45, 15, '100g', None, 'Tatlı'),
    ('Sütlaç', 120, 3, 20, 3, '100g', None, 'Tatlı'),
    ('Kazandibi', 140, 4, 22, 4, '100g', None, 'Tatlı'),
    ('Dondurma (Kaymaklı)', 207, 3.5, 24, 11, '100g', None, 'Tatlı'),
    ('Lokum', 320, 0.2, 80, 0.2, '100g', None, 'Tatlı'),
    ('Revani', 280, 5, 45, 10, '100g', None, 'Tatlı'),
    
    # Kahvaltılık
    ('Bal', 304, 0.3, 82, 0, '100g', None, 'Kahvaltılık'),
    ('Reçel', 260, 0.4, 65, 0.1, '100g', None, 'Kahvaltılık'),
    ('Tahin', 595, 18, 21, 54, '100g', None, 'Kahvaltılık'),
    ('Pekmez', 290, 0.9, 75, 0.1, '100g', None, 'Kahvaltılık'),
    ('Zeytin (Siyah)', 115, 0.8, 6, 11, '100g', None, 'Kahvaltılık'),
    ('Zeytin (Yeşil)', 115, 1, 4, 11, '100g', None, 'Kahvaltılık'),
    ('Sucuk', 452, 18, 2, 40, '100g', None, 'Kahvaltılık'),
    ('Pastırma', 250, 30, 2, 12, '100g', None, 'Kahvaltılık'),
    ('Yumurta (Menemen)', 120, 8, 8, 7, '100g', None, 'Kahvaltılık'),
    ('Omlet', 154, 11, 1, 12, '100g', None, 'Kahvaltılık'),
]

def add_foods():
    """Besinleri veritabanına ekle"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Mevcut besinleri kontrol et
    cursor.execute('SELECT COUNT(*) FROM foods')
    existing_count = cursor.fetchone()[0]
    
    print(f"Mevcut {existing_count} besin var. Besinler guncelleniyor...")
    
    # Tüm besinleri sil ve yeniden ekle (kategori bilgisi için)
    cursor.execute('DELETE FROM foods')
    print("Eski besinler silindi.")
    
    added_count = 0
    for food in FOODS:
        name, calories, protein, carbs, fat, serving_size, barcode, category = food
        
        cursor.execute('''
            INSERT INTO foods (name, calories, protein, carbs, fat, serving_size, barcode, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, calories, protein, carbs, fat, serving_size, barcode, category, datetime.now().isoformat()))
        added_count += 1
    
    conn.commit()
    conn.close()
    print(f"OK: {added_count} besin eklendi!")
    print(f"Toplam besin sayisi: {added_count}")

if __name__ == '__main__':
    add_foods()

