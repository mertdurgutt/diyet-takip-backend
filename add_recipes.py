"""
Tarif Veritabanına Tarif Ekleme Scripti
"""
import sqlite3
from datetime import datetime
import sys
import os

# UTF-8 encoding ayarla (Windows icin)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_NAME = 'diyet_takip.db'

# Türk mutfağı ve sağlıklı tarifler
RECIPES = [
    # Kilo Verme Tarifleri
    {
        'name': 'Yeşil Salata (Proteinli)',
        'description': 'Yüksek protein, düşük kalorili yeşil salata',
        'instructions': '1. Marul, roka, ıspanak yapraklarını yıkayın\n2. Tavuk göğsü haşlayıp küp küp doğrayın\n3. Sebzeleri karıştırın\n4. Zeytinyağı ve limon ile soslayın\n5. Tavuk etini ekleyip servis yapın',
        'calories': 280,
        'protein': 35,
        'carbs': 12,
        'fat': 8,
        'servings': 1,
        'prep_time': 10,
        'cook_time': 15,
        'difficulty': 'Kolay',
        'category': 'Salata',
        'goal': 'kilo verme'
    },
    {
        'name': 'Izgara Tavuk Göğsü + Sebze',
        'description': 'Düşük kalorili, yüksek protein ana öğün',
        'instructions': '1. Tavuk göğsünü marine edin (zeytinyağı, limon, baharatlar)\n2. Izgarada pişirin (her iki taraf 6-7 dakika)\n3. Brokoli, karnabahar, havuç buharda pişirin\n4. Zeytinyağı ve baharatlarla servis yapın',
        'calories': 320,
        'protein': 42,
        'carbs': 15,
        'fat': 8,
        'servings': 1,
        'prep_time': 15,
        'cook_time': 20,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo verme'
    },
    {
        'name': 'Yoğurtlu Sebze Çorbası',
        'description': 'Düşük kalorili, doyurucu çorba',
        'instructions': '1. Sebzeleri (kabak, havuç, kereviz) doğrayın\n2. Sebzeleri haşlayın\n3. Blender\'dan geçirin\n4. Yoğurt ekleyip karıştırın\n5. Baharatlarla servis yapın',
        'calories': 150,
        'protein': 8,
        'carbs': 20,
        'fat': 3,
        'servings': 2,
        'prep_time': 10,
        'cook_time': 25,
        'difficulty': 'Kolay',
        'category': 'Çorba',
        'goal': 'kilo verme'
    },
    {
        'name': 'Yumurta Beyazı Omlet',
        'description': 'Yüksek protein, düşük kalorili kahvaltı',
        'instructions': '1. 4 yumurta beyazını çırpın\n2. Sebzeleri (mantar, biber, domates) doğrayın\n3. Teflon tavada sebzeleri pişirin\n4. Yumurta beyazını ekleyin\n5. Peynir ekleyip servis yapın',
        'calories': 180,
        'protein': 24,
        'carbs': 8,
        'fat': 4,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 10,
        'difficulty': 'Kolay',
        'category': 'Kahvaltı',
        'goal': 'kilo verme'
    },
    {
        'name': 'Balık + Sebze Buharda',
        'description': 'Düşük kalorili, yüksek protein balık yemeği',
        'instructions': '1. Balığı temizleyin ve baharatlayın\n2. Buharda pişirin (15-20 dakika)\n3. Sebzeleri buharda pişirin\n4. Limon ve zeytinyağı ile servis yapın',
        'calories': 250,
        'protein': 38,
        'carbs': 10,
        'fat': 6,
        'servings': 1,
        'prep_time': 10,
        'cook_time': 20,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo verme'
    },
    
    # Kilo Alma Tarifleri
    {
        'name': 'Protein Smoothie (Yüksek Kalorili)',
        'description': 'Yüksek kalorili, protein içeren smoothie',
        'instructions': '1. 1 muz, 1 avokado, 2 kaşık fıstık ezmesi\n2. 1 su bardağı süt, 1 ölçek protein tozu\n3. 2 kaşık yulaf ezmesi\n4. Tüm malzemeleri blender\'dan geçirin\n5. Buz ekleyip servis yapın',
        'calories': 650,
        'protein': 35,
        'carbs': 65,
        'fat': 25,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 0,
        'difficulty': 'Kolay',
        'category': 'İçecek',
        'goal': 'kilo alma'
    },
    {
        'name': 'Kırmızı Et + Patates + Sebze',
        'description': 'Yüksek kalorili, protein içeren ana öğün',
        'instructions': '1. Kırmızı eti marine edin\n2. Izgarada veya tavada pişirin\n3. Patatesleri fırında pişirin\n4. Sebzeleri buharda pişirin\n5. Zeytinyağı ve baharatlarla servis yapın',
        'calories': 680,
        'protein': 45,
        'carbs': 55,
        'fat': 28,
        'servings': 1,
        'prep_time': 20,
        'cook_time': 30,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo alma'
    },
    {
        'name': 'Fıstık Ezmesi + Tam Tahıl Ekmek',
        'description': 'Yüksek kalorili, sağlıklı atıştırmalık',
        'instructions': '1. 2 dilim tam tahıl ekmeği kızartın\n2. Fıstık ezmesi sürün\n3. Muz dilimleri ekleyin\n4. Bal ekleyip servis yapın',
        'calories': 420,
        'protein': 15,
        'carbs': 45,
        'fat': 20,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 3,
        'difficulty': 'Kolay',
        'category': 'Atıştırmalık',
        'goal': 'kilo alma'
    },
    {
        'name': 'Mercimek Köfte (Yüksek Kalorili)',
        'description': 'Yüksek kalorili, protein içeren vejetaryen yemek',
        'instructions': '1. Mercimeği haşlayın\n2. Soğan, maydanoz, baharatlar ekleyin\n3. Köfte şeklini verin\n4. Zeytinyağında kızartın\n5. Salata ile servis yapın',
        'calories': 380,
        'protein': 18,
        'carbs': 45,
        'fat': 12,
        'servings': 4,
        'prep_time': 20,
        'cook_time': 30,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo alma'
    },
    {
        'name': 'Yulaf + Kuruyemiş + Bal',
        'description': 'Yüksek kalorili, sağlıklı kahvaltı',
        'instructions': '1. Yulaf ezmesini süt ile pişirin\n2. Kuruyemiş (ceviz, badem, fındık) ekleyin\n3. Bal ve meyve ekleyin\n4. Servis yapın',
        'calories': 520,
        'protein': 18,
        'carbs': 65,
        'fat': 20,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 10,
        'difficulty': 'Kolay',
        'category': 'Kahvaltı',
        'goal': 'kilo alma'
    },
    
    # Kilo Koruma Tarifleri
    {
        'name': 'Dengeli Tavuk Pilav',
        'description': 'Dengeli makro besin içeren ana öğün',
        'instructions': '1. Tavuk göğsünü haşlayın\n2. Pilavı pişirin\n3. Sebzeleri buharda pişirin\n4. Zeytinyağı ve baharatlarla servis yapın',
        'calories': 480,
        'protein': 35,
        'carbs': 50,
        'fat': 12,
        'servings': 1,
        'prep_time': 15,
        'cook_time': 25,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo koruma'
    },
    {
        'name': 'Mevsim Salatası + Protein',
        'description': 'Dengeli, sağlıklı salata',
        'instructions': '1. Mevsim sebzelerini yıkayın\n2. Tavuk veya balık ekleyin\n3. Zeytinyağı ve limon ile soslayın\n4. Servis yapın',
        'calories': 320,
        'protein': 28,
        'carbs': 20,
        'fat': 12,
        'servings': 1,
        'prep_time': 10,
        'cook_time': 15,
        'difficulty': 'Kolay',
        'category': 'Salata',
        'goal': 'kilo koruma'
    },
    {
        'name': 'Sebzeli Omlet',
        'description': 'Dengeli, sağlıklı kahvaltı',
        'instructions': '1. 3 yumurta çırpın\n2. Sebzeleri (mantar, biber, domates) doğrayın\n3. Teflon tavada pişirin\n4. Peynir ve baharatlarla servis yapın',
        'calories': 280,
        'protein': 20,
        'carbs': 12,
        'fat': 16,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 10,
        'difficulty': 'Kolay',
        'category': 'Kahvaltı',
        'goal': 'kilo koruma'
    },
    {
        'name': 'Balık + Sebze + Karbonhidrat',
        'description': 'Dengeli, sağlıklı ana öğün',
        'instructions': '1. Balığı temizleyin ve baharatlayın\n2. Fırında pişirin\n3. Sebzeleri buharda pişirin\n4. Patates veya pilav ekleyin\n5. Servis yapın',
        'calories': 420,
        'protein': 32,
        'carbs': 45,
        'fat': 12,
        'servings': 1,
        'prep_time': 15,
        'cook_time': 25,
        'difficulty': 'Orta',
        'category': 'Ana Yemek',
        'goal': 'kilo koruma'
    },
    {
        'name': 'Yoğurt + Meyve + Kuruyemiş',
        'description': 'Dengeli, sağlıklı atıştırmalık',
        'instructions': '1. Yoğurt hazırlayın\n2. Meyve (çilek, muz, yaban mersini) ekleyin\n3. Kuruyemiş (ceviz, badem) ekleyin\n4. Bal ekleyip servis yapın',
        'calories': 280,
        'protein': 12,
        'carbs': 30,
        'fat': 12,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 0,
        'difficulty': 'Kolay',
        'category': 'Atıştırmalık',
        'goal': 'kilo koruma'
    },
    
    # Genel Tarifler
    {
        'name': 'Mercimek Çorbası',
        'description': 'Protein içeren, sağlıklı çorba',
        'instructions': '1. Mercimeği yıkayın\n2. Soğan, havuç, patates doğrayın\n3. Sebzeleri haşlayın\n4. Blender\'dan geçirin\n5. Baharatlarla servis yapın',
        'calories': 180,
        'protein': 12,
        'carbs': 28,
        'fat': 3,
        'servings': 2,
        'prep_time': 10,
        'cook_time': 30,
        'difficulty': 'Kolay',
        'category': 'Çorba',
        'goal': None
    },
    {
        'name': 'Izgara Sebze Tabak',
        'description': 'Sebze ağırlıklı, sağlıklı yemek',
        'instructions': '1. Sebzeleri (patlıcan, kabak, biber) doğrayın\n2. Zeytinyağı ve baharatlarla marine edin\n3. Izgarada pişirin\n4. Yoğurt ile servis yapın',
        'calories': 220,
        'protein': 8,
        'carbs': 25,
        'fat': 10,
        'servings': 2,
        'prep_time': 15,
        'cook_time': 20,
        'difficulty': 'Kolay',
        'category': 'Ana Yemek',
        'goal': None
    },
    {
        'name': 'Tam Tahıl Ekmek + Peynir + Zeytin',
        'description': 'Dengeli, sağlıklı kahvaltı',
        'instructions': '1. Tam tahıl ekmeği hazırlayın\n2. Peynir ve zeytin ekleyin\n3. Domates, salatalık ekleyin\n4. Servis yapın',
        'calories': 320,
        'protein': 15,
        'carbs': 35,
        'fat': 14,
        'servings': 1,
        'prep_time': 5,
        'cook_time': 0,
        'difficulty': 'Kolay',
        'category': 'Kahvaltı',
        'goal': None
    },
]

def add_recipes():
    """Tarifleri veritabanına ekle"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tarifler tablosunu oluştur (eğer yoksa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            instructions TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            servings INTEGER DEFAULT 1,
            prep_time INTEGER,
            cook_time INTEGER,
            difficulty TEXT,
            category TEXT,
            goal TEXT,
            image_url TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    # Tarifler tablosunu kontrol et
    cursor.execute('PRAGMA table_info(recipes)')
    columns = cursor.fetchall()
    if not columns:
        print("HATA: recipes tablosu olusturulamadi!")
        conn.close()
        return
    
    added_count = 0
    skipped_count = 0
    
    for recipe in RECIPES:
        try:
            # Tarif zaten var mı kontrol et
            cursor.execute('SELECT id FROM recipes WHERE name = ?', (recipe['name'],))
            if cursor.fetchone():
                skipped_count += 1
                continue
            
            # Tarifi ekle
            cursor.execute('''
                INSERT INTO recipes (
                    name, description, instructions, calories, protein, carbs, fat,
                    servings, prep_time, cook_time, difficulty, category, goal, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe['name'],
                recipe.get('description'),
                recipe.get('instructions'),
                recipe.get('calories'),
                recipe.get('protein'),
                recipe.get('carbs'),
                recipe.get('fat'),
                recipe.get('servings', 1),
                recipe.get('prep_time'),
                recipe.get('cook_time'),
                recipe.get('difficulty'),
                recipe.get('category'),
                recipe.get('goal'),
                datetime.now().isoformat()
            ))
            added_count += 1
        except Exception as e:
            print(f"Hata: {recipe['name']} eklenirken hata olustu: {e}")
            skipped_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"{added_count} tarif eklendi!")
    if skipped_count > 0:
        print(f"{skipped_count} tarif atlandi (zaten mevcut)")

if __name__ == '__main__':
    add_recipes()

