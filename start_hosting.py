#!/usr/bin/env python
"""
Hosting için basit başlatma scripti
Bu script hosting'de uygulamayı başlatmak için kullanılabilir
"""
import os
import sys

# Proje dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Environment variables yükle (varsa)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yüklü değilse devam et

# Flask uygulamasını import et
from app import app, init_db

# Veritabanını başlat (sadece ilk çalıştırmada)
try:
    print("Veritabani baslatiliyor...")
    init_db()
    print("Veritabani baslatildi!")
except Exception as e:
    print(f"Veritabani baslatma hatasi (normal olabilir): {e}")

# Gunicorn ile başlat (eğer gunicorn yüklüyse)
try:
    import gunicorn
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    workers = int(os.getenv('WORKERS', 4))
    timeout = int(os.getenv('TIMEOUT', 120))
    
    print("=" * 60)
    print("Diyet Takip - Backend API (Gunicorn)")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Workers: {workers}")
    print(f"Timeout: {timeout}")
    print("=" * 60)
    print("Backend baslatildi! Mobil uygulamayi baslatabilirsiniz.")
    print("=" * 60)
    
    # Gunicorn ile başlat
    from gunicorn.app.base import BaseApplication
    
    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()
        
        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)
        
        def load(self):
            return self.application
    
    options = {
        'bind': f'{host}:{port}',
        'workers': workers,
        'timeout': timeout,
        'accesslog': '-',
        'errorlog': '-',
    }
    
    StandaloneApplication(app, options).run()
except ImportError:
    # Gunicorn yüklü değilse Flask'ın kendi server'ını kullan
    print("=" * 60)
    print("Diyet Takip - Backend API (Flask Development Server)")
    print("=" * 60)
    print("UYARI: Gunicorn yuklu degil! Production icin Gunicorn onerilir.")
    print("=" * 60)
    
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Mode: {'Development' if debug_mode else 'Production'}")
    print(f"API: http://{host}:{port}")
    print(f"Health Check: http://{host}:{port}/api/health")
    print(f"Admin Panel: http://{host}:{port}/admin")
    print("=" * 60)
    print("Backend baslatildi! Mobil uygulamayi baslatabilirsiniz.")
    print("=" * 60)
    
    app.run(debug=debug_mode, host=host, port=port)

