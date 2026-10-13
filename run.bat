@echo off
title HoneyChain Unified Blockchain Network Portal
echo ========================================================
echo   HoneyChain - 5-Block Provenance Blockchain Portal
echo.
echo   Block 0: Genesis Block
echo      ^|
echo      v
echo   Block 1: Honey Batch Registered (Apiary)
echo      ^|
echo      v
echo   Block 2: Laboratory Test Recorded (Lab Purity)
echo      ^|
echo      v
echo   Block 3: Honey Packaging Recorded (Bottling)
echo      ^|
echo      v
echo   Block 4: Seller Information Recorded (Retail Shelf)
echo ========================================================
echo.
echo [1/3] Checking dependencies...
python -m pip install -r requirements.txt >nul 2>&1
echo.
echo [2/3] Freeing port 5000 if already in use...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
echo.
echo [3/3] Detecting Local and Network IP...
for /f "tokens=*" %%i in ('python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()" 2^>nul') do set LAN_IP=%%i
if "%LAN_IP%"=="" set LAN_IP=127.0.0.1

echo.
echo ========================================================
echo   HONEYCHAIN IS NOW AVAILABLE ON YOUR NETWORK!
echo ========================================================
echo   * Host Computer:    http://127.0.0.1:5000
echo   * Network / Wi-Fi:  http://%LAN_IP%:5000
echo.
echo   Connect any phone, tablet, or PC on the same Wi-Fi!
echo   Tip: Scan the Network QR Code in the top portal bar.
echo ========================================================
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"
python app.py
pause
