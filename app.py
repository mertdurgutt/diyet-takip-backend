"""
Diyet Takip Uygulaması - Backend API
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import sqlite3
import bcrypt
import os
import sys

# Environment variables yükle (varsa)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yüklü değilse devam et

app = Flask(__name__)

# JWT Secret Key (production'da mutlaka environment variable'dan alın)
jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
if jwt_secret == 'your-secret-key-change-in-production':
    print("⚠️  UYARI: JWT_SECRET_KEY varsayılan değerde! Production'da mutlaka değiştirin!")
app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# CORS ayarları (production'da sadece belirli domain'lere izin verin)
# Mobil uygulamalar için tüm origin'lere izin vermek gerekebilir
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins != '*':
    # Birden fazla origin varsa liste olarak ayır
    cors_origins = [origin.strip() for origin in cors_origins.split(',')]
# Mobil uygulamalar için CORS ayarları (tüm origin'lere izin ver)
CORS(app, origins=cors_origins if isinstance(cors_origins, list) else '*', 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

jwt = JWTManager(app)

# Veritabanı bağlantısı
# Hosting için mutlak yol veya environment variable kullan
# Render.com için: DB_PATH environment variable'ını kullan veya default path
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diyet_takip.db'))
DB_NAME = DB_PATH

# Render.com için veritabanı yolu (Render.com otomatik PORT verir)
# Render.com'da veritabanı dosyası geçici olarak çalışır (ücretsiz planda)
# Production için PostgreSQL kullanılmalı
if os.getenv('PORT'):  # Render.com'da PORT environment variable'ı otomatik verilir
    # Render.com'da veritabanı için geçici path kullan
    DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diyet_takip.db'))
    DB_NAME = DB_PATH

def init_db():
    """Veritabanını oluştur"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            target_weight REAL,
            activity_level TEXT,
            goal TEXT,
            bmr REAL,
            tdee REAL,
            daily_calories REAL,
            daily_protein REAL,
            daily_carbs REAL,
            daily_fat REAL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Tabloyu commit et
    conn.commit()
    
    # Eski veritabanları için is_admin kolonu ekle (eğer yoksa)
    # SQLite'da ALTER TABLE ADD COLUMN işlemi kolon zaten varsa hata verir
    # Bu yüzden try-except ile kontrol ediyoruz
    is_admin_column_exists = False
    try:
        # PRAGMA ile tablo yapısını kontrol et
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'is_admin':  # col[1] = column name
                is_admin_column_exists = True
                break
    except Exception as e:
        print(f"Tablo yapisi kontrol hatasi: {e}")
    
    # Eğer is_admin kolonu yoksa ekle
    if not is_admin_column_exists:
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
            conn.commit()
            print("is_admin kolonu eklendi")
            is_admin_column_exists = True
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if 'duplicate column name' in error_msg or 'already exists' in error_msg:
                is_admin_column_exists = True
                print("is_admin kolonu zaten mevcut")
            else:
                print(f"is_admin kolonu ekleme hatasi: {e}")
                # Hata olsa bile devam et
    
    # Admin kullanıcısı kontrolü ve oluşturma
    try:
        # Önce sadece id'yi kontrol et (is_admin kolonu olmayabilir)
        cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@diyettakip.com',))
        admin_user = cursor.fetchone()
        
        if not admin_user:
            # Admin kullanıcısı yok, oluştur
            if is_admin_column_exists:
                admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('''
                    INSERT INTO users (email, password, name, is_admin, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin@diyettakip.com', admin_password, 'Admin', 1, datetime.now().isoformat()))
            else:
                # is_admin kolonu yoksa, önce kolonu ekle
                try:
                    cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
                    conn.commit()
                    is_admin_column_exists = True
                    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute('''
                        INSERT INTO users (email, password, name, is_admin, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', ('admin@diyettakip.com', admin_password, 'Admin', 1, datetime.now().isoformat()))
                except Exception as e:
                    print(f"Admin kullanici olusturma hatasi: {e}")
                    # Hata olsa bile devam et
            conn.commit()
            print("Admin kullanici olusturuldu: admin@diyettakip.com / admin123")
        else:
            # Admin kullanıcısı var, is_admin değerini kontrol et ve güncelle
            if is_admin_column_exists:
                cursor.execute('SELECT id, is_admin FROM users WHERE email = ?', ('admin@diyettakip.com',))
                admin_user_data = cursor.fetchone()
                if admin_user_data and len(admin_user_data) > 1:
                    admin_is_admin = admin_user_data[1] if admin_user_data[1] is not None else 0
                    if admin_is_admin != 1:
                        cursor.execute('UPDATE users SET is_admin = 1 WHERE email = ?', ('admin@diyettakip.com',))
                        conn.commit()
                        print("Admin kullanici is_admin olarak guncellendi")
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if 'no such column' in error_msg:
            # is_admin kolonu hala yok, tekrar eklemeyi dene
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
                conn.commit()
                print("is_admin kolonu eklendi (retry)")
                # Admin kullanıcısını tekrar oluşturmayı dene
                cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@diyettakip.com',))
                admin_user = cursor.fetchone()
                if not admin_user:
                    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute('''
                        INSERT INTO users (email, password, name, is_admin, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', ('admin@diyettakip.com', admin_password, 'Admin', 1, datetime.now().isoformat()))
                    conn.commit()
                    print("Admin kullanici olusturuldu: admin@diyettakip.com / admin123")
            except Exception as e2:
                print(f"Admin kullanici olusturma hatasi (retry): {e2}")
        else:
            print(f"Admin kullanici olusturma hatasi: {e}")
    
    # Besinler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL,
            carbs REAL,
            fat REAL,
            serving_size TEXT,
            barcode TEXT,
            category TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Günlük kayıtlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            meal_type TEXT,
            food_id INTEGER,
            food_name TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            quantity REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (food_id) REFERENCES foods (id)
        )
    ''')
    
    # Su kayıtları
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Egzersiz kayıtları
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercise_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            exercise_name TEXT,
            duration INTEGER,
            calories_burned REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Kilo kayıtları
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            weight REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Favori besinler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (food_id) REFERENCES foods (id),
            UNIQUE(user_id, food_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Veritabani hazir!")

# Veritabanı helper fonksiyonları
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Hesaplama fonksiyonları
def calculate_bmr(weight, height, age, gender):
    """Bazal Metabolizma Hızı (BMR) hesapla - Mifflin-St Jeor formülü"""
    if gender.lower() == 'erkek' or gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return round(bmr, 2)

def calculate_tdee(bmr, activity_level):
    """Günlük Toplam Enerji Harcaması (TDEE) hesapla"""
    multipliers = {
        'sedentary': 1.2,      # Hareketsiz
        'light': 1.375,        # Az Aktif
        'moderate': 1.55,      # Aktif
        'active': 1.725,       # Çok Aktif
        'very_active': 1.9     # Aşırı Aktif
    }
    multiplier = multipliers.get(activity_level.lower(), 1.2)
    return round(bmr * multiplier, 2)

def calculate_macros(tdee, goal, weight):
    """Makro besin hesapla"""
    if goal.lower() in ['kilo verme', 'weight loss']:
        daily_calories = tdee - 500  # Haftalık 0.5kg verme için
    elif goal.lower() in ['kilo alma', 'weight gain']:
        daily_calories = tdee + 500  # Haftalık 0.5kg alma için
    else:  # Kilo koruma
        daily_calories = tdee
    
    # Makro dağılımı (önrnek: %30 protein, %40 karbonhidrat, %30 yağ)
    protein = round((daily_calories * 0.30) / 4, 2)  # 1g protein = 4 kalori
    carbs = round((daily_calories * 0.40) / 4, 2)    # 1g karbonhidrat = 4 kalori
    fat = round((daily_calories * 0.30) / 9, 2)      # 1g yağ = 9 kalori
    
    return {
        'daily_calories': round(daily_calories, 2),
        'protein': protein,
        'carbs': carbs,
        'fat': fat
    }

# API Endpoints

@app.route('/api/health', methods=['GET'])
def health():
    """Sağlık kontrolü"""
    return jsonify({'status': 'ok', 'message': 'API çalışıyor'})

@app.route('/api/register', methods=['POST'])
def register():
    """Kullanıcı kaydı"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        age = data.get('age')
        gender = data.get('gender')
        height = data.get('height')
        weight = data.get('weight')
        target_weight = data.get('target_weight')
        activity_level = data.get('activity_level')
        goal = data.get('goal')
        
        if not email or not password:
            return jsonify({'error': 'Email ve şifre gerekli'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcı zaten var mı?
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bu email zaten kullanılıyor'}), 400
        
        # Şifreyi hashle
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # BMR ve TDEE hesapla
        bmr = calculate_bmr(weight, height, age, gender)
        tdee = calculate_tdee(bmr, activity_level)
        macros = calculate_macros(tdee, goal, weight)
        
        # Kullanıcıyı kaydet
        cursor.execute('''
            INSERT INTO users (email, password, name, age, gender, height, weight, target_weight,
                             activity_level, goal, bmr, tdee, daily_calories, daily_protein,
                             daily_carbs, daily_fat, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, hashed_password, name, age, gender, height, weight, target_weight,
              activity_level, goal, bmr, tdee, macros['daily_calories'], macros['protein'],
              macros['carbs'], macros['fat'], datetime.now().isoformat()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # JWT token oluştur
        access_token = create_access_token(identity=str(user_id))
        
        return jsonify({
            'message': 'Kullanıcı kaydedildi',
            'token': access_token,
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email ve şifre gerekli'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcıyı bul
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # Şifre kontrolü
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # JWT token oluştur
        access_token = create_access_token(identity=str(user['id']))
        
        return jsonify({
            'message': 'Giriş başarılı',
            'token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'daily_calories': user['daily_calories'],
                'daily_protein': user['daily_protein'],
                'daily_carbs': user['daily_carbs'],
                'daily_fat': user['daily_fat']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Kullanıcı profili"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'age': user['age'],
            'gender': user['gender'],
            'height': user['height'],
            'weight': user['weight'],
            'target_weight': user['target_weight'],
            'activity_level': user['activity_level'],
            'goal': user['goal'],
            'bmr': user['bmr'],
            'tdee': user['tdee'],
            'daily_calories': user['daily_calories'],
            'daily_protein': user['daily_protein'],
            'daily_carbs': user['daily_carbs'],
            'daily_fat': user['daily_fat']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/foods', methods=['GET'])
@jwt_required()
def get_foods():
    """Besinleri listele"""
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM foods WHERE 1=1'
        params = []
        
        if search:
            query += ' AND name LIKE ?'
            params.append(f'%{search}%')
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY name LIMIT 200'
        
        cursor.execute(query, params)
        foods = [dict(row) for row in cursor.fetchall()]
        
        # Kategorileri de döndür
        cursor.execute('SELECT DISTINCT category FROM foods WHERE category IS NOT NULL ORDER BY category')
        categories = [row['category'] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'foods': foods, 'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/foods', methods=['POST'])
@jwt_required()
def add_food():
    """Yeni besin ekle (kullanıcı özel besin)"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO foods (name, calories, protein, carbs, fat, serving_size, barcode, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('name'), data.get('calories'), data.get('protein'), data.get('carbs'),
              data.get('fat'), data.get('serving_size'), data.get('barcode'), data.get('category', 'Diğer'), 
              datetime.now().isoformat()))
        
        food_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Besin eklendi', 'food_id': food_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-log', methods=['POST'])
@jwt_required()
def add_daily_log():
    """Günlük besin kaydı ekle"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO daily_logs (user_id, date, meal_type, food_id, food_name, calories,
                                   protein, carbs, fat, quantity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, date, data.get('meal_type'), data.get('food_id'), data.get('food_name'),
              data.get('calories'), data.get('protein'), data.get('carbs'), data.get('fat'),
              data.get('quantity', 1), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Kayıt eklendi'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-log/<date>', methods=['GET'])
@jwt_required()
def get_daily_log(date):
    """Günlük kayıtları getir"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        # Besin kayıtları
        cursor.execute('''
            SELECT * FROM daily_logs WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Toplam hesapla
        total_calories = sum(log['calories'] for log in logs)
        total_protein = sum(log['protein'] or 0 for log in logs)
        total_carbs = sum(log['carbs'] or 0 for log in logs)
        total_fat = sum(log['fat'] or 0 for log in logs)
        
        # Su kayıtları
        cursor.execute('''
            SELECT SUM(amount) as total_water FROM water_logs WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        water_result = cursor.fetchone()
        total_water = water_result['total_water'] or 0
        
        # Egzersiz kayıtları
        cursor.execute('''
            SELECT * FROM exercise_logs WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        exercises = [dict(row) for row in cursor.fetchall()]
        total_exercise_calories = sum(ex['calories_burned'] or 0 for ex in exercises)
        
        conn.close()
        
        return jsonify({
            'date': date,
            'logs': logs,
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat,
                'water': total_water,
                'exercise_calories': total_exercise_calories
            },
            'exercises': exercises
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/water', methods=['POST'])
@jwt_required()
def add_water():
    """Su kaydı ekle"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        amount = data.get('amount', 250)  # ml cinsinden
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO water_logs (user_id, date, amount, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date, amount, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Su kaydı eklendi'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/exercise', methods=['POST'])
@jwt_required()
def add_exercise():
    """Egzersiz kaydı ekle"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exercise_logs (user_id, date, exercise_name, duration, calories_burned, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, date, data.get('exercise_name'), data.get('duration'),
              data.get('calories_burned'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Egzersiz kaydı eklendi'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weight', methods=['POST'])
@jwt_required()
def add_weight():
    """Kilo kaydı ekle"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        weight = data.get('weight')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO weight_logs (user_id, date, weight, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date, weight, datetime.now().isoformat()))
        
        # Kullanıcının mevcut kilosunu güncelle
        cursor.execute('UPDATE users SET weight = ? WHERE id = ?', (weight, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Kilo kaydı eklendi'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weight/history', methods=['GET'])
@jwt_required()
def get_weight_history():
    """Kilo geçmişi"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, weight FROM weight_logs WHERE user_id = ? ORDER BY date ASC
        ''', (user_id,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Kullanıcı hedefine göre öneriler"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcı bilgilerini al
        cursor.execute('SELECT goal, daily_calories, weight, target_weight FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        goal = user['goal'].lower() if user['goal'] else 'kilo koruma'
        daily_calories = user['daily_calories'] or 2000
        weight = user['weight'] or 70
        target_weight = user['target_weight'] or weight
        
        recommendations = []
        
        # Kilo verme önerileri
        if 'verme' in goal or 'loss' in goal:
            recommendations = [
                {
                    'title': '💧 Bol Su İçin',
                    'description': 'Günde en az 2-3 litre su içmek metabolizmanızı hızlandırır ve tokluk hissi verir.',
                    'icon': '💧'
                },
                {
                    'title': '🥗 Protein Ağırlıklı Beslenin',
                    'description': 'Protein, kas kütlenizi korurken yağ yakımını destekler. Her öğünde protein içeren besinler tüketin.',
                    'icon': '🥗'
                },
                {
                    'title': '🏃 Düzenli Egzersiz Yapın',
                    'description': 'Haftada 3-4 kez kardiyovasküler egzersiz ve ağırlık antrenmanı yapın. Günde en az 30 dakika yürüyüş yapın.',
                    'icon': '🏃'
                },
                {
                    'title': '⏰ Düzenli Uyku',
                    'description': 'Günde 7-8 saat kaliteli uyku, hormon dengesini korur ve kilo vermeyi kolaylaştırır.',
                    'icon': '⏰'
                },
                {
                    'title': '🍎 Sağlıklı Atıştırmalıklar',
                    'description': 'Açlık hissettiğinizde meyve, kuruyemiş veya yoğurt gibi sağlıklı atıştırmalıklar tercih edin.',
                    'icon': '🍎'
                },
                {
                    'title': '📊 Kalori Takibi',
                    'description': f'Günlük {int(daily_calories)} kalori hedefinizi aşmamaya çalışın. Küçük porsiyonlar ve yavaş yeme alışkanlığı edinin.',
                    'icon': '📊'
                }
            ]
        # Kilo alma önerileri
        elif 'alma' in goal or 'gain' in goal:
            recommendations = [
                {
                    'title': '🥩 Kalori Yoğun Besinler',
                    'description': 'Kuruyemiş, avokado, tam tahıllar gibi kalori yoğun ama sağlıklı besinler tüketin.',
                    'icon': '🥩'
                },
                {
                    'title': '💪 Ağırlık Antrenmanı',
                    'description': 'Haftada 3-4 kez ağırlık antrenmanı yaparak kas kütlenizi artırın. Kardiyo egzersizlerini sınırlı tutun.',
                    'icon': '💪'
                },
                {
                    'title': '🍽️ Sık Öğünler',
                    'description': 'Günde 5-6 öğün yiyin. Her öğünde protein, karbonhidrat ve sağlıklı yağ içeren dengeli beslenme yapın.',
                    'icon': '🍽️'
                },
                {
                    'title': '🥤 Kalorili İçecekler',
                    'description': 'Smoothie, süt, meyve suyu gibi besleyici içecekler tüketin. Su yerine bazen protein shake içebilirsiniz.',
                    'icon': '🥤'
                },
                {
                    'title': '📈 İlerleme Takibi',
                    'description': f'Hedefiniz {int(target_weight)} kg. Haftalık kilo takibi yapın ve sabırlı olun. Sağlıklı kilo alma zaman alır.',
                    'icon': '📈'
                },
                {
                    'title': '🌙 İyi Uyku',
                    'description': 'Kas gelişimi için günde 7-9 saat uyuyun. Uyku, büyüme hormonu salgılanmasını artırır.',
                    'icon': '🌙'
                }
            ]
        # Kilo koruma önerileri
        else:
            recommendations = [
                {
                    'title': '⚖️ Dengeli Beslenme',
                    'description': f'Günlük {int(daily_calories)} kalori hedefinizi koruyun. Makro besinlerinizi dengeli tüketin.',
                    'icon': '⚖️'
                },
                {
                    'title': '🏋️ Düzenli Egzersiz',
                    'description': 'Haftada 3-4 kez egzersiz yapın. Kardiyovasküler ve direnç antrenmanlarını kombine edin.',
                    'icon': '🏋️'
                },
                {
                    'title': '💧 Su İçmeyi Unutmayın',
                    'description': 'Günde 2-3 litre su için. Su, metabolizmanızı aktif tutar ve genel sağlığınızı destekler.',
                    'icon': '💧'
                },
                {
                    'title': '🍎 Çeşitli Besinler',
                    'description': 'Farklı renk ve türde meyve-sebze tüketin. Çeşitlilik, vitamin ve mineral alımınızı artırır.',
                    'icon': '🍎'
                },
                {
                    'title': '📊 Düzenli Takip',
                    'description': 'Kilonuzu ve beslenmenizi düzenli takip edin. Küçük değişiklikleri erken fark edin.',
                    'icon': '📊'
                },
                {
                    'title': '😊 Stres Yönetimi',
                    'description': 'Stres, kilo alımına neden olabilir. Meditasyon, yoga veya hobilerinizle stresi yönetin.',
                    'icon': '😊'
                }
            ]
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Favori besinler endpoint'leri
@app.route('/api/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    """Favori besinleri listele"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.* FROM foods f
            INNER JOIN favorite_foods ff ON f.id = ff.food_id
            WHERE ff.user_id = ?
            ORDER BY f.name
        ''', (user_id,))
        foods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'foods': foods}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    """Favorilere besin ekle"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        food_id = data.get('food_id')
        
        if not food_id:
            return jsonify({'error': 'Besin ID gerekli'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Zaten favori mi kontrol et
        cursor.execute('SELECT id FROM favorite_foods WHERE user_id = ? AND food_id = ?', (user_id, food_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bu besin zaten favorilerde'}), 400
        
        cursor.execute('''
            INSERT INTO favorite_foods (user_id, food_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, food_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Favorilere eklendi'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites/<food_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(food_id):
    """Favorilerden besin çıkar"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM favorite_foods WHERE user_id = ? AND food_id = ?', (user_id, food_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Favorilerden çıkarıldı'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# İstatistikler endpoint'leri
@app.route('/api/statistics/weekly', methods=['GET'])
@jwt_required()
def get_weekly_statistics():
    """Haftalık istatistikler"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        # Son 7 gün
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Günlük toplamlar
        daily_stats = []
        for i in range(7):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # Kalori toplamı
            cursor.execute('''
                SELECT SUM(calories) as total FROM daily_logs 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            calories_result = cursor.fetchone()
            total_calories = calories_result['total'] or 0
            
            # Makro toplamları
            cursor.execute('''
                SELECT 
                    SUM(protein) as total_protein,
                    SUM(carbs) as total_carbs,
                    SUM(fat) as total_fat
                FROM daily_logs 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            macro_result = cursor.fetchone()
            
            # Su toplamı
            cursor.execute('''
                SELECT SUM(amount) as total FROM water_logs 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            water_result = cursor.fetchone()
            total_water = water_result['total'] or 0
            
            daily_stats.append({
                'date': date,
                'calories': total_calories,
                'protein': macro_result['total_protein'] or 0,
                'carbs': macro_result['total_carbs'] or 0,
                'fat': macro_result['total_fat'] or 0,
                'water': total_water,
            })
        
        # Ortalama hesapla
        avg_calories = sum(stat['calories'] for stat in daily_stats) / len(daily_stats)
        avg_protein = sum(stat['protein'] for stat in daily_stats) / len(daily_stats)
        avg_carbs = sum(stat['carbs'] for stat in daily_stats) / len(daily_stats)
        avg_fat = sum(stat['fat'] for stat in daily_stats) / len(daily_stats)
        avg_water = sum(stat['water'] for stat in daily_stats) / len(daily_stats)
        
        conn.close()
        
        return jsonify({
            'daily_stats': daily_stats,
            'averages': {
                'calories': round(avg_calories, 2),
                'protein': round(avg_protein, 2),
                'carbs': round(avg_carbs, 2),
                'fat': round(avg_fat, 2),
                'water': round(avg_water, 2),
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics/monthly', methods=['GET'])
@jwt_required()
def get_monthly_statistics():
    """Aylık istatistikler"""
    try:
        user_id = get_jwt_identity()
        conn = get_db()
        cursor = conn.cursor()
        
        # Son 30 gün
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Günlük toplamlar (30 gün)
        daily_stats = []
        for i in range(30):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT SUM(calories) as total FROM daily_logs 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            calories_result = cursor.fetchone()
            total_calories = calories_result['total'] or 0
            
            daily_stats.append({
                'date': date,
                'calories': total_calories,
            })
        
        # Ortalama hesapla
        avg_calories = sum(stat['calories'] for stat in daily_stats) / len(daily_stats) if daily_stats else 0
        
        # En çok tüketilen besinler
        cursor.execute('''
            SELECT food_name, SUM(calories) as total_calories, COUNT(*) as count
            FROM daily_logs
            WHERE user_id = ? AND date >= ? AND date <= ?
            GROUP BY food_name
            ORDER BY total_calories DESC
            LIMIT 10
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        top_foods = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'daily_stats': daily_stats,
            'average_calories': round(avg_calories, 2),
            'top_foods': top_foods,
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Endpoints
ADMIN_EMAIL = 'admin@diyettakip.com'

def is_admin(user_id):
    """Kullanıcı admin mi kontrol et"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return user['is_admin'] == 1 or user['email'] == ADMIN_EMAIL
        return False
    except Exception as e:
        print(f"Admin kontrol hatası: {e}")
        return False

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin girişi"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email ve şifre gerekli'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # Admin kontrolü
        if user['is_admin'] != 1 and user['email'] != ADMIN_EMAIL:
            return jsonify({'error': 'Bu kullanıcı admin değil'}), 403
        
        # Şifre kontrolü
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # JWT token oluştur
        access_token = create_access_token(identity=str(user['id']))
        
        return jsonify({
            'message': 'Admin girişi başarılı',
            'token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'is_admin': True
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    """Admin istatistikleri"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Toplam kullanıcı sayısı
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_admin = 0')
        total_users = cursor.fetchone()['total']
        
        # Aktif kullanıcı sayısı (son 30 günde giriş yapan)
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as active FROM daily_logs 
            WHERE date >= date('now', '-30 days')
        ''')
        active_users = cursor.fetchone()['active']
        
        # Toplam besin sayısı
        cursor.execute('SELECT COUNT(*) as total FROM foods')
        total_foods = cursor.fetchone()['total']
        
        # Toplam log sayısı
        cursor.execute('SELECT COUNT(*) as total FROM daily_logs')
        total_logs = cursor.fetchone()['total']
        
        # Bugünkü log sayısı
        cursor.execute('SELECT COUNT(*) as total FROM daily_logs WHERE date = date("now")')
        today_logs = cursor.fetchone()['total']
        
        # Son 7 günlük kullanıcı aktivitesi
        cursor.execute('''
            SELECT date, COUNT(DISTINCT user_id) as count 
            FROM daily_logs 
            WHERE date >= date('now', '-7 days')
            GROUP BY date
            ORDER BY date
        ''')
        activity_data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_foods': total_foods,
            'total_logs': total_logs,
            'today_logs': today_logs,
            'activity_data': activity_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    """Kullanıcı listesi"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Toplam kullanıcı sayısı
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_admin = 0')
        total = cursor.fetchone()['total']
        
        # Kullanıcıları getir
        cursor.execute('''
            SELECT id, email, name, age, gender, weight, target_weight, goal, 
                   daily_calories, created_at
            FROM users 
            WHERE is_admin = 0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'users': users,
            'total': total,
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@jwt_required()
def admin_get_user(user_id):
    """Kullanıcı detayı"""
    try:
        admin_id = get_jwt_identity()
        if not is_admin(admin_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcı bilgileri
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Kullanıcının log sayıları
        cursor.execute('SELECT COUNT(*) as total FROM daily_logs WHERE user_id = ?', (user_id,))
        total_logs = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM water_logs WHERE user_id = ?', (user_id,))
        total_water = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM exercise_logs WHERE user_id = ?', (user_id,))
        total_exercises = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM weight_logs WHERE user_id = ?', (user_id,))
        total_weights = cursor.fetchone()['total']
        
        # Son aktiviteler
        cursor.execute('''
            SELECT date, SUM(calories) as total_calories, COUNT(*) as meal_count
            FROM daily_logs 
            WHERE user_id = ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7
        ''', (user_id,))
        recent_activities = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'user': dict(user),
            'stats': {
                'total_logs': total_logs,
                'total_water': total_water,
                'total_exercises': total_exercises,
                'total_weights': total_weights
            },
            'recent_activities': recent_activities
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def admin_update_user(user_id):
    """Kullanıcı güncelle (admin)"""
    try:
        admin_id = get_jwt_identity()
        if not is_admin(admin_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcıyı kontrol et
        cursor.execute('SELECT id FROM users WHERE id = ? AND is_admin = 0', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Önce mevcut kullanıcı bilgilerini al
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        current_user = cursor.fetchone()
        if not current_user:
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Güncellenecek alanları belirle
        updates = []
        params = []
        
        # Güncellenecek değerleri belirle (varsayılan olarak mevcut değerleri kullan)
        new_weight = data.get('weight', current_user['weight'])
        new_height = data.get('height', current_user['height'])
        new_age = data.get('age', current_user['age'])
        new_gender = data.get('gender', current_user['gender'])
        new_activity_level = data.get('activity_level', current_user['activity_level'])
        new_goal = data.get('goal', current_user['goal'])
        
        # Güncellenecek alanları ekle
        if 'name' in data:
            updates.append('name = ?')
            params.append(data['name'])
        if 'age' in data:
            updates.append('age = ?')
            params.append(data['age'])
            new_age = data['age']
        if 'gender' in data:
            updates.append('gender = ?')
            params.append(data['gender'])
            new_gender = data['gender']
        if 'height' in data:
            updates.append('height = ?')
            params.append(data['height'])
            new_height = data['height']
        if 'weight' in data:
            updates.append('weight = ?')
            params.append(data['weight'])
            new_weight = data['weight']
        if 'target_weight' in data:
            updates.append('target_weight = ?')
            params.append(data['target_weight'])
        if 'activity_level' in data:
            updates.append('activity_level = ?')
            params.append(data['activity_level'])
            new_activity_level = data['activity_level']
        if 'goal' in data:
            updates.append('goal = ?')
            params.append(data['goal'])
            new_goal = data['goal']
        
        # BMR ve TDEE'yi yeniden hesapla (kilo, boy, yaş, cinsiyet veya aktivite seviyesi değiştiyse)
        needs_recalculation = ('weight' in data or 'height' in data or 'age' in data or 
                              'gender' in data or 'activity_level' in data)
        
        if needs_recalculation:
            if new_weight and new_height and new_age and new_gender:
                bmr = calculate_bmr(new_weight, new_height, new_age, new_gender)
                tdee = calculate_tdee(bmr, new_activity_level)
                macros = calculate_macros(tdee, new_goal, new_weight)
                updates.append('bmr = ?')
                params.append(bmr)
                updates.append('tdee = ?')
                params.append(tdee)
                updates.append('daily_calories = ?')
                params.append(macros['daily_calories'])
                updates.append('daily_protein = ?')
                params.append(macros['protein'])
                updates.append('daily_carbs = ?')
                params.append(macros['carbs'])
                updates.append('daily_fat = ?')
                params.append(macros['fat'])
        elif 'goal' in data:
            # Sadece hedef değiştiyse, mevcut TDEE ile makroları yeniden hesapla
            current_tdee = current_user['tdee'] if current_user['tdee'] else 0
            current_weight = current_user['weight'] if current_user['weight'] else new_weight
            if current_tdee and current_weight:
                macros = calculate_macros(current_tdee, new_goal, current_weight)
                updates.append('daily_calories = ?')
                params.append(macros['daily_calories'])
                updates.append('daily_protein = ?')
                params.append(macros['protein'])
                updates.append('daily_carbs = ?')
                params.append(macros['carbs'])
                updates.append('daily_fat = ?')
                params.append(macros['fat'])
        
        if not updates:
            conn.close()
            return jsonify({'error': 'Güncellenecek alan yok'}), 400
        
        # UPDATE sorgusu
        params.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Kullanıcı güncellendi'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    """Kullanıcı sil"""
    try:
        admin_id = get_jwt_identity()
        if not is_admin(admin_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kullanıcıyı kontrol et
        cursor.execute('SELECT id FROM users WHERE id = ? AND is_admin = 0', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        # Kullanıcıyı ve ilgili verileri sil
        cursor.execute('DELETE FROM daily_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM water_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM exercise_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM weight_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM favorite_foods WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Kullanıcı silindi'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/foods', methods=['GET'])
@jwt_required()
def admin_get_foods():
    """Besin listesi (admin)"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM foods WHERE 1=1'
        params = []
        
        if search:
            query += ' AND name LIKE ?'
            params.append(f'%{search}%')
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        # Toplam sayı
        count_query = query.replace('SELECT *', 'SELECT COUNT(*) as total')
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Besinleri getir
        query += ' ORDER BY name LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        cursor.execute(query, params)
        foods = [dict(row) for row in cursor.fetchall()]
        
        # Kategoriler
        cursor.execute('SELECT DISTINCT category FROM foods WHERE category IS NOT NULL ORDER BY category')
        categories = [row['category'] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'foods': foods,
            'categories': categories,
            'total': total,
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/foods', methods=['POST'])
@jwt_required()
def admin_add_food():
    """Besin ekle (admin)"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO foods (name, calories, protein, carbs, fat, serving_size, barcode, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('name'), data.get('calories'), data.get('protein'), data.get('carbs'),
              data.get('fat'), data.get('serving_size'), data.get('barcode'), data.get('category', 'Diğer'), 
              datetime.now().isoformat()))
        
        food_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Besin eklendi', 'food_id': food_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/foods/<int:food_id>', methods=['PUT'])
@jwt_required()
def admin_update_food(food_id):
    """Besin güncelle (admin)"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE foods 
            SET name = ?, calories = ?, protein = ?, carbs = ?, fat = ?, 
                serving_size = ?, barcode = ?, category = ?
            WHERE id = ?
        ''', (data.get('name'), data.get('calories'), data.get('protein'), data.get('carbs'),
              data.get('fat'), data.get('serving_size'), data.get('barcode'), data.get('category'),
              food_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Besin güncellendi'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/foods/<int:food_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_food(food_id):
    """Besin sil (admin)"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM foods WHERE id = ?', (food_id,))
        cursor.execute('DELETE FROM favorite_foods WHERE food_id = ?', (food_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Besin silindi'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Logs Endpoints
@app.route('/api/admin/logs', methods=['GET'])
@jwt_required()
def admin_get_logs():
    """Tüm logları listele (admin)"""
    try:
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return jsonify({'error': 'Yetkisiz erişim'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        log_type = request.args.get('type', 'all')  # all, daily, water, exercise, weight
        user_id_filter = request.args.get('user_id', None)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        logs = []
        total = 0
        
        # Filtre koşulları (güvenli parametreli sorgu)
        filter_conditions = []
        filter_params = []
        
        if user_id_filter:
            filter_conditions.append('user_id = ?')
            filter_params.append(user_id_filter)
        if date_from:
            filter_conditions.append('date >= ?')
            filter_params.append(date_from)
        if date_to:
            filter_conditions.append('date <= ?')
            filter_params.append(date_to)
        
        # Log tipine göre sorgu oluştur
        if log_type == 'daily':
            # Sadece besin logları
            where_parts = ['dl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    dl.id, dl.user_id, u.email, u.name, dl.date, dl.meal_type,
                    dl.food_name, dl.calories, dl.protein, dl.carbs, dl.fat, dl.quantity,
                    dl.created_at, 'daily' as log_type
                FROM daily_logs dl
                LEFT JOIN users u ON dl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY dl.created_at DESC
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, filter_params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            
            # Toplam sayı
            count_where_parts = ['daily_logs.' + cond for cond in filter_conditions] if filter_conditions else []
            count_where = ' AND '.join(count_where_parts) if count_where_parts else '1=1'
            count_query = 'SELECT COUNT(*) as total FROM daily_logs WHERE ' + count_where
            cursor.execute(count_query, filter_params)
            total = cursor.fetchone()['total']
            
        elif log_type == 'water':
            # Sadece su logları
            where_parts = ['wl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    wl.id, wl.user_id, u.email, u.name, wl.date, wl.amount,
                    wl.created_at, 'water' as log_type
                FROM water_logs wl
                LEFT JOIN users u ON wl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY wl.created_at DESC
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, filter_params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            
            # Toplam sayı
            count_where_parts = ['water_logs.' + cond for cond in filter_conditions] if filter_conditions else []
            count_where = ' AND '.join(count_where_parts) if count_where_parts else '1=1'
            count_query = 'SELECT COUNT(*) as total FROM water_logs WHERE ' + count_where
            cursor.execute(count_query, filter_params)
            total = cursor.fetchone()['total']
            
        elif log_type == 'exercise':
            # Sadece egzersiz logları
            where_parts = ['el.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    el.id, el.user_id, u.email, u.name, el.date, el.exercise_name,
                    el.duration, el.calories_burned, el.created_at, 'exercise' as log_type
                FROM exercise_logs el
                LEFT JOIN users u ON el.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY el.created_at DESC
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, filter_params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            
            # Toplam sayı
            count_where_parts = ['exercise_logs.' + cond for cond in filter_conditions] if filter_conditions else []
            count_where = ' AND '.join(count_where_parts) if count_where_parts else '1=1'
            count_query = 'SELECT COUNT(*) as total FROM exercise_logs WHERE ' + count_where
            cursor.execute(count_query, filter_params)
            total = cursor.fetchone()['total']
            
        elif log_type == 'weight':
            # Sadece kilo logları
            where_parts = ['wl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    wl.id, wl.user_id, u.email, u.name, wl.date, wl.weight,
                    wl.created_at, 'weight' as log_type
                FROM weight_logs wl
                LEFT JOIN users u ON wl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY wl.created_at DESC
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, filter_params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            
            # Toplam sayı
            count_where_parts = ['weight_logs.' + cond for cond in filter_conditions] if filter_conditions else []
            count_where = ' AND '.join(count_where_parts) if count_where_parts else '1=1'
            count_query = 'SELECT COUNT(*) as total FROM weight_logs WHERE ' + count_where
            cursor.execute(count_query, filter_params)
            total = cursor.fetchone()['total']
            
        else:  # log_type == 'all'
            # Tüm logları birleştir - her tablodan son 200 kaydı getir, sonra birleştir ve sırala
            all_logs = []
            fetch_limit = 200  # Her tablodan son 200 kayıt (sayfalama için yeterli)
            
            # Besin logları
            where_parts = ['dl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    dl.id, dl.user_id, u.email, u.name, dl.date, dl.meal_type,
                    dl.food_name, dl.calories, dl.protein, dl.carbs, dl.fat, dl.quantity,
                    dl.created_at, 'daily' as log_type
                FROM daily_logs dl
                LEFT JOIN users u ON dl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY dl.created_at DESC
                LIMIT ''' + str(fetch_limit)
            cursor.execute(query, filter_params)
            all_logs.extend([dict(row) for row in cursor.fetchall()])
            
            # Su logları
            where_parts = ['wl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    wl.id, wl.user_id, u.email, u.name, wl.date, wl.amount,
                    wl.created_at, 'water' as log_type
                FROM water_logs wl
                LEFT JOIN users u ON wl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY wl.created_at DESC
                LIMIT ''' + str(fetch_limit)
            cursor.execute(query, filter_params)
            all_logs.extend([dict(row) for row in cursor.fetchall()])
            
            # Egzersiz logları
            where_parts = ['el.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    el.id, el.user_id, u.email, u.name, el.date, el.exercise_name,
                    el.duration, el.calories_burned, el.created_at, 'exercise' as log_type
                FROM exercise_logs el
                LEFT JOIN users u ON el.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY el.created_at DESC
                LIMIT ''' + str(fetch_limit)
            cursor.execute(query, filter_params)
            all_logs.extend([dict(row) for row in cursor.fetchall()])
            
            # Kilo logları
            where_parts = ['wl.' + cond for cond in filter_conditions] if filter_conditions else []
            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            
            query = '''
                SELECT 
                    wl.id, wl.user_id, u.email, u.name, wl.date, wl.weight,
                    wl.created_at, 'weight' as log_type
                FROM weight_logs wl
                LEFT JOIN users u ON wl.user_id = u.id
                WHERE ''' + where_clause + '''
                ORDER BY wl.created_at DESC
                LIMIT ''' + str(fetch_limit)
            cursor.execute(query, filter_params)
            all_logs.extend([dict(row) for row in cursor.fetchall()])
            
            # Toplam sayı (tüm loglar için)
            total = 0
            for table in ['daily_logs', 'water_logs', 'exercise_logs', 'weight_logs']:
                count_where_parts = [table + '.' + cond for cond in filter_conditions] if filter_conditions else []
                count_where = ' AND '.join(count_where_parts) if count_where_parts else '1=1'
                count_query = 'SELECT COUNT(*) as total FROM ' + table + ' WHERE ' + count_where
                cursor.execute(count_query, filter_params)
                total += cursor.fetchone()['total']
            
            # Tarihe göre sırala
            all_logs.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
            
            # Pagination uygula
            logs = all_logs[offset:offset + limit]
        
        conn.close()
        
        return jsonify({
            'logs': logs,
            'total': total,
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Admin paneli için static dosya servisi
# Render.com için: admin klasörü backend klasörü içinde olmalı
# Önce backend/admin dizinini kontrol et (Render.com için)
current_dir = os.path.dirname(os.path.abspath(__file__))
admin_dir = os.path.join(current_dir, 'admin')

# Eğer backend/admin yoksa, bir üst dizindeki admin'i kontrol et (local için)
if not os.path.exists(admin_dir):
    parent_dir = os.path.dirname(current_dir)
    admin_dir = os.path.join(parent_dir, 'admin')

# Mutlak yola çevir
admin_dir = os.path.abspath(admin_dir)

# Admin dizini kontrolü (modül yüklendiğinde bir kez çalışır)
print("=" * 60)
print("ADMIN PANEL KONTROL")
print("=" * 60)
print(f"Mevcut dizin: {current_dir}")
print(f"Admin dizini: {admin_dir}")
print(f"Admin dizini mevcut mu: {os.path.exists(admin_dir)}")

if os.path.exists(admin_dir):
    files = os.listdir(admin_dir)
    print(f"Admin dizinindeki dosyalar: {files}")
    if 'index.html' in files:
        print("✅ index.html bulundu!")
    else:
        print("❌ index.html BULUNAMADI!")
    if 'app.js' in files:
        print("✅ app.js bulundu!")
    else:
        print("❌ app.js BULUNAMADI!")
else:
    print(f"❌ UYARI: Admin dizini bulunamadı!")
    print(f"   Kontrol edilen yollar:")
    print(f"   1. {os.path.join(current_dir, 'admin')}")
    print(f"   2. {os.path.join(os.path.dirname(current_dir), 'admin')}")
print("=" * 60)

# Admin route'ları (modül seviyesinde - Render.com'da çalışması için)
@app.route('/admin')
def admin_index():
    """Admin paneli ana sayfası"""
    try:
        print(f"Admin index isteği alındı. Admin dizini: {admin_dir}")
        print(f"Admin dizini mevcut mu: {os.path.exists(admin_dir)}")
        
        if not os.path.exists(admin_dir):
            error_msg = f"Admin dizini bulunamadı: {admin_dir}"
            print(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 404
        
        index_path = os.path.join(admin_dir, 'index.html')
        print(f"Index.html yolu: {index_path}")
        print(f"Index.html mevcut mu: {os.path.exists(index_path)}")
        
        if not os.path.exists(index_path):
            error_msg = f"index.html bulunamadı: {index_path}"
            print(f"ERROR: {error_msg}")
            # Admin dizinindeki dosyaları listele
            if os.path.exists(admin_dir):
                files = os.listdir(admin_dir)
                print(f"Admin dizinindeki dosyalar: {files}")
            return jsonify({'error': error_msg}), 404
        
        print(f"Admin index.html gönderiliyor...")
        return send_from_directory(admin_dir, 'index.html', mimetype='text/html')
    except Exception as e:
        error_msg = f"Admin index hatası: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/admin/<path:filename>')
def admin_static(filename):
    """Admin paneli static dosyaları (JS, CSS, vs.)"""
    try:
        print(f"Admin static dosya isteği: {filename}")
        print(f"Admin dizini: {admin_dir}")
        print(f"Admin dizini mevcut mu: {os.path.exists(admin_dir)}")
        
        if not os.path.exists(admin_dir):
            error_msg = f"Admin dizini bulunamadı: {admin_dir}"
            print(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 404
        
        file_path = os.path.join(admin_dir, filename)
        print(f"Dosya yolu: {file_path}")
        print(f"Dosya mevcut mu: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            # Admin dizinindeki dosyaları listele
            if os.path.exists(admin_dir):
                files = os.listdir(admin_dir)
                print(f"Admin dizinindeki dosyalar: {files}")
            error_msg = f"Dosya bulunamadı: {filename} (yol: {file_path})"
            print(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 404
        
        # MIME type belirle
        if filename.endswith('.js'):
            mimetype = 'application/javascript'
        elif filename.endswith('.css'):
            mimetype = 'text/css'
        elif filename.endswith('.html'):
            mimetype = 'text/html'
        elif filename.endswith('.json'):
            mimetype = 'application/json'
        elif filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        elif filename.endswith('.svg'):
            mimetype = 'image/svg+xml'
        else:
            mimetype = None
        
        print(f"Dosya gönderiliyor: {filename} (mimetype: {mimetype})")
        return send_from_directory(admin_dir, filename, mimetype=mimetype)
    except Exception as e:
        error_msg = f"Admin static dosya hatası: {str(e)}, dosya: {filename}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

# Development modu (sadece doğrudan çalıştırıldığında)
if __name__ == '__main__':
    init_db()
    
    # Örnek besinleri ekle (eğer yoksa)
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM foods')
        food_count = cursor.fetchone()[0]
        conn.close()
        
        if food_count == 0:
            print("Kapsamli besin veritabani yukleniyor...")
            # Kapsamlı besin listesi import et
            try:
                from add_foods import add_foods
                add_foods()
            except ImportError:
                print("add_foods.py bulunamadi, basit ornek besinler ekleniyor...")
                # Basit örnek besinler (fallback)
                sample_foods = [
                    ('Tavuk Göğsü (100g)', 165, 31, 0, 3.6, '100g', None, 'Et'),
                    ('Yumurta (1 adet)', 70, 6, 0.6, 5, '1 adet', None, 'Yumurta'),
                    ('Yoğurt (100g)', 59, 10, 3.6, 0.4, '100g', None, 'Süt Ürünleri'),
                    ('Pirinç (100g)', 130, 2.7, 28, 0.3, '100g', None, 'Tahıl'),
                    ('Makarna (100g)', 131, 5, 25, 1.1, '100g', None, 'Tahıl'),
                ]
                
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for food in sample_foods:
                    cursor.execute('''
                        INSERT INTO foods (name, calories, protein, carbs, fat, serving_size, barcode, category, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (*food, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                print(f"{len(sample_foods)} ornek besin eklendi!")
        else:
            print(f"Veritabanda {food_count} besin mevcut.")
    except Exception as e:
        print(f"Ornek besin ekleme hatasi: {e}")
    
    # Production modu kontrolü
    # Render.com için: FLASK_DEBUG = False (production)
    # Local için: FLASK_DEBUG = True (development)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))  # Render.com otomatik port atar
    host = os.getenv('HOST', '0.0.0.0')  # 0.0.0.0 = tüm ağ arayüzlerinde dinle
    
    print("=" * 60)
    print("Diyet Takip - Backend API")
    print("=" * 60)
    print(f"Mode: {'Development' if debug_mode else 'Production'}")
    print(f"API: http://localhost:{port}")
    print(f"API: http://127.0.0.1:{port}")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"Admin Panel: http://localhost:{port}/admin")
    print(f"Database: {DB_NAME}")
    print("=" * 60)
    print("⚠️  ÖNEMLİ: Mobil uygulamadan bağlanmak için IP adresini kullan!")
    print("   IP adresini öğrenmek için: ipconfig (Windows) veya ifconfig (Mac/Linux)")
    print("   Örnek: http://192.168.1.6:5000")
    print("=" * 60)
    print("Backend baslatildi! Mobil uygulamayi baslatabilirsiniz.")
    print("=" * 60)
    app.run(debug=debug_mode, host=host, port=port)
