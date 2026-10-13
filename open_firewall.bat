@echo off
title HoneyChain - Allow Port 5000 in Windows Firewall
echo ========================================================
echo   HoneyChain - Windows Firewall Network Configuration
echo ========================================================
echo.
echo Checking administrator privileges...

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Requesting Administrator elevation...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

echo.
echo Adding inbound Windows Firewall rule for Port 5000 (TCP)...
netsh advfirewall firewall delete rule name="HoneyChain Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="HoneyChain Port 5000" dir=in action=allow protocol=TCP localport=5000 profile=any description="Allows incoming network connections to HoneyChain Blockchain Portal"

echo.
echo Detecting your Network IP address...
for /f "tokens=*" %%i in ('python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()" 2^>nul') do set LAN_IP=%%i
if "%LAN_IP%"=="" set LAN_IP=10.40.247.29

echo.
echo ========================================================
echo SUCCESS: Port 5000 is now open!
echo All phones, tablets, and computers on your Wi-Fi/LAN
echo can now connect to HoneyChain without restriction.
echo ========================================================
echo.
echo   ======================================================
echo   USER ACCESS LINKS (Share with any phone / device):
echo   ======================================================
echo   * Phone / Wi-Fi User Link:   http://%LAN_IP%:5000
echo   * Public Consumer Trace:     http://%LAN_IP%:5000/?tab=trace
echo   * Host Computer User Link:   http://127.0.0.1:5000
echo   ======================================================
echo.
echo Tip: Open http://%LAN_IP%:5000 in your mobile browser or scan the QR code.
echo.
choice /c YN /m "Would you like to open the User Link in your browser now (Y/N)?"
if errorlevel 2 goto done
if errorlevel 1 start http://%LAN_IP%:5000

:done
echo.
pause
