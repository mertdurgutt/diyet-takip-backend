"""
WSGI entry point for hosting
Bu dosya hosting sağlayıcıları için WSGI application olarak kullanılır
"""
import os
import sys

# Proje dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(__file__))

# Environment variables yükle (varsa)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yüklü değilse devam et

# Flask uygulamasını import et
from app import app, init_db

# Veritabanını başlat (sadece ilk çalıştırmada)
# Render.com'da otomatik başlat
try:
    print("Veritabani baslatiliyor...")
    init_db()
    print("Veritabani baslatildi!")
except Exception as e:
    print(f"Veritabani baslatma hatasi (normal olabilir): {e}")
    import traceback
    traceback.print_exc()

# WSGI application (hosting sağlayıcıları bunu kullanır)
application = app

# Development modu (eğer doğrudan çalıştırılırsa)
if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host=host, port=port)

