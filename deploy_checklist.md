# ✅ Hosting Deploy Checklist

## 📦 Yüklenecek Dosyalar

- [ ] `app.py`
- [ ] `wsgi.py`
- [ ] `requirements.txt`
- [ ] `runtime.txt`
- [ ] `Procfile`
- [ ] `env_example.txt`
- [ ] `admin/` klasörü (index.html, app.js)
- [ ] `diyet_takip.db` (varsa, yoksa oluşturulacak)

---

## ⚙️ Ayarlar

- [ ] Python versiyonu ayarlandı (3.11 veya 3.10)
- [ ] Uygulama yolu ayarlandı (/backend)
- [ ] WSGI dosyası ayarlandı (wsgi.py)
- [ ] Startup dosyası ayarlandı (app.py veya wsgi.py)

---

## 🔐 Environment Variables

- [ ] `JWT_SECRET_KEY` eklendi
- [ ] `FLASK_DEBUG=False` eklendi
- [ ] `PORT=5000` eklendi
- [ ] `HOST=0.0.0.0` eklendi
- [ ] `DB_PATH` eklendi (doğru yol)
- [ ] `CORS_ORIGINS=*` eklendi

---

## 📥 Bağımlılıklar

- [ ] `flask==3.0.0` yüklendi
- [ ] `flask-cors==4.0.0` yüklendi
- [ ] `flask-jwt-extended==4.6.0` yüklendi
- [ ] `sqlalchemy==2.0.23` yüklendi
- [ ] `python-dotenv==1.0.0` yüklendi
- [ ] `bcrypt==4.1.1` yüklendi
- [ ] `pydantic==2.5.2` yüklendi
- [ ] `gunicorn==21.2.0` yüklendi

---

## 🗄️ Veritabanı

- [ ] Veritabanı başlatıldı (init_db)
- [ ] Admin kullanıcısı oluşturuldu
- [ ] Örnek besinler yüklendi (varsa)

---

## 🚀 Uygulama

- [ ] Uygulama başlatıldı
- [ ] Health check çalışıyor (https://mertdurgut.net/api/health)
- [ ] Admin panel çalışıyor (https://mertdurgut.net/admin)
- [ ] API endpoints çalışıyor

---

## 📱 Mobil Uygulama

- [ ] API URL güncellendi (mobile/config/api.js)
- [ ] HOSTING_MODE = true yapıldı
- [ ] HOSTING_URL doğru ayarlandı
- [ ] Mobil uygulama test edildi

---

## 🎉 Tamamlandı!

Tüm adımlar tamamlandı! ✅

