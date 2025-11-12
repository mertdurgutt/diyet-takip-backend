@echo off
echo ========================================
echo Diyet Takip - Backend Baslatiliyor
echo ========================================
echo.

cd /d %~dp0

echo Python kontrol ediliyor...
python --version
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo Lutfen Python 3.8+ yukleyin.
    pause
    exit /b 1
)

echo.
echo IP adresi ogreniliyor...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo Bulunan IP: !IP!
    goto :found
)

:found
echo.
echo ========================================
echo Backend baslatiliyor...
echo ========================================
echo API: http://localhost:5000
if defined IP (
    echo API: http://%IP%:5000
    echo.
    echo ONEMLI: Mobil uygulamada bu IP adresini kullan!
    echo mobile/config/api.js dosyasinda IP_ADRESI = '%IP%' yap!
)
echo.
echo Admin Panel: http://localhost:5000/admin
echo Health Check: http://localhost:5000/api/health
echo.
echo ========================================
echo.

python app.py

pause

