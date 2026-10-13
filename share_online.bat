@echo off
title HoneyChain - Instant Worldwide Online Access (Tunnel)
echo ========================================================
echo   HoneyChain - Instant Public Internet Access
echo ========================================================
echo.
echo This tool generates a secure temporary HTTPS public link
echo so anyone outside your local Wi-Fi (mobile cellular, remote partners)
echo can access your HoneyChain portal and verify honey batches.
echo.
echo Make sure HoneyChain is running (run.bat) on Port 5000 first!
echo.
echo Starting secure tunnel via localtunnel...
echo (Your public HTTPS link will appear below in a few seconds)
echo ========================================================
echo.
cmd /c "npx localtunnel --port 5000"
pause
