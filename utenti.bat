@echo off
title Gestione Utenti Windows - Avanzato
setlocal enabledelayedexpansion

:: Disable command echoing to avoid trace logs
set "LOGGING=false"

:: Clear screen and initialize menu
:menu
cls
echo *************************************
echo          Gestione Utenti Windows
echo *************************************
echo 1. Aggiungere un Utente
echo 2. Eliminare un Utente
echo 3. Cambiare Password Utente
echo 4. Visualizzare Utenti Esistenti
echo 5. Visualizzare Informazioni Dettagliate Utente
echo 6. Abilitare o Disabilitare un Utente
echo 7. Aprire Cartella Profilo Utente
echo 8. Controllare Appartenenza a un Gruppo
echo 9. Bloccare un Utente
echo 10. Sbloccare un Utente
echo 11. Aggiungere un Utente a un Gruppo
echo 12. Rimuovere un Utente da un Gruppo
echo 13. Creare un Gruppo Locale
echo 14. Eliminare un Gruppo Locale
echo 15. Visualizzare Gruppi Esistenti
echo 16. Impostare Password che Scade
echo 17. Impostare Password che Non Scade
echo 18. Impostare Utente per Cambiare Password al Prossimo Login
echo 19. Impostare Utente per Non Cambiare Password
echo 20. Impostare Descrizione Utente
echo 21. Impostare Nome Completo Utente
echo 22. Impostare Directory Home Utente
echo 23. Visualizzare Sessioni Utente Attive
echo 24. Disconnettere una Sessione Utente
echo 25. Forzare il Cambio Password
echo 26. Mostrare Stato Password Utente
echo 27. Creare Utente con Password Complessa
echo 28. Abilitare Audit per Utente
echo 29. Disabilitare Audit per Utente
echo 30. Visualizzare Percorso Profilo Utente
echo 31. Cambiare Nome Completo Utente
echo 32. Visualizzare Ultimo Login Utente
echo 33. Resettare Password Utente
echo 34. Attivare Account Utente
echo 35. Disattivare Account Utente
echo 36. Forzare Blocco Schermo per Utente
echo 37. Schedulare Disconnessione Utente
echo 38. Impostare Limite di Tempo per Sessione Utente
echo 39. Visualizzare Politiche Password Utente
echo 40. Configurare Accesso Desktop Remoto per Utente
echo 41. Impostare Quota Disco per Utente
echo 42. Abilitare o Disabilitare il Cambiamento Password
echo 43. Bloccare Tutti i Corsi di Login per Utente
echo 44. Sbloccare Tutti i Corsi di Login per Utente
echo 45. Abilitare o Disabilitare l'Esecuzione Automatica per Utente
echo 46. Impostare Script di Login per Utente
echo 47. Rimuovere Script di Login per Utente
echo 48. Visualizzare Variabili d'Ambiente Utente
echo 49. Modificare Variabili d'Ambiente Utente
echo 50. Ripristinare Variabili d'Ambiente Predefinite
echo 51. Uscire
echo *************************************
set /p scelta= Scegli un'opzione (1-51): 

if "%scelta%"=="1" goto aggiungi
if "%scelta%"=="2" goto elimina
if "%scelta%"=="3" goto cambia_password
if "%scelta%"=="4" goto visualizza
if "%scelta%"=="5" goto info_utente
if "%scelta%"=="6" goto abilita_disabilita
if "%scelta%"=="7" goto apri_cartella
if "%scelta%"=="8" goto verifica_gruppo
if "%scelta%"=="9" goto blocca_utente
if "%scelta%"=="10" goto sblocca_utente
if "%scelta%"=="11" goto aggiungi_gruppo
if "%scelta%"=="12" goto rimuovi_gruppo
if "%scelta%"=="13" goto crea_gruppo
if "%scelta%"=="14" goto elimina_gruppo
if "%scelta%"=="15" goto visualizza_gruppi
if "%scelta%"=="16" goto password_scade
if "%scelta%"=="17" goto password_non_scade
if "%scelta%"=="18" goto forza_cambio_password
if "%scelta%"=="19" goto non_cambiare_password
if "%scelta%"=="20" goto imposta_descrizione
if "%scelta%"=="21" goto imposta_nome_completo
if "%scelta%"=="22" goto imposta_home_dir
if "%scelta%"=="23" goto visualizza_sessioni
if "%scelta%"=="24" goto disconnetti_sessione
if "%scelta%"=="25" goto forza_reset_password
if "%scelta%"=="26" goto mostra_stato_password
if "%scelta%"=="27" goto crea_utente_complesso
if "%scelta%"=="28" goto abilita_audit
if "%scelta%"=="29" goto disabilita_audit
if "%scelta%"=="30" goto mostra_percorso_profilo
if "%scelta%"=="31" goto cambia_nome_completo
if "%scelta%"=="32" goto mostra_ultimo_login
if "%scelta%"=="33" goto resetta_password
if "%scelta%"=="34" goto attiva_account
if "%scelta%"=="35" goto disattiva_account
if "%scelta%"=="36" goto forza_blocco_schermo
if "%scelta%"=="37" goto schedula_disconnessione
if "%scelta%"=="38" goto imposta_limite_tempo
if "%scelta%"=="39" goto visualizza_politiche_password
if "%scelta%"=="40" goto configura_rdp
if "%scelta%"=="41" goto imposta_quota_disco
if "%scelta%"=="42" goto abilita_disabilita_cambio_password
if "%scelta%"=="43" goto blocca_corsi_login
if "%scelta%"=="44" goto sblocca_corsi_login
if "%scelta%"=="45" goto abilita_esecuzione_automatica
if "%scelta%"=="46" goto imposta_script_login
if "%scelta%"=="47" goto rimuovi_script_login
if "%scelta%"=="48" goto visualizza_variabili_env
if "%scelta%"=="49" goto modifica_variabili_env
if "%scelta%"=="50" goto ripristina_variabili_env
if "%scelta%"=="51" goto uscire

echo Scelta non valida. Riprova.
pause
goto menu

:: Function to list all users on the system
:visualizza
echo *************************************
echo Visualizzando gli utenti esistenti...
echo *************************************
net user
echo *************************************
pause
goto menu

:: Function to safely add a user
:aggiungi
set /p user= Inserisci il nome utente da aggiungere: 
net user %user% >nul 2>&1
if %errorlevel%==0 (
    echo L'utente "%user%" esiste gia. Aggiungere un altro nome.
    pause
    goto menu
)
set /p password= Inserisci la password per "%user%": 
net user %user% %password% /add
if %errorlevel%==0 (
    echo Utente "%user%" aggiunto con successo!
) else (
    echo Errore nell'aggiungere l'utente "%user%".
)
pause
goto menu

:: Function to safely delete a user
:elimina
set /p user= Inserisci il nome utente da eliminare: 
net user %user% >nul 2>&1
if %errorlevel%==2 (
    echo L'utente "%user%" non esiste.
    pause
    goto menu
)
echo Eliminando l'utente "%user%"...
net user %user% /delete
if %errorlevel%==0 (
    echo Utente "%user%" eliminato con successo!
) else (
    echo Errore nell'eliminare l'utente "%user%".
)
pause
goto menu

:: Function to change password for a user
:cambia_password
set /p user= Inserisci il nome utente: 
set /p password= Inserisci la nuova password: 
echo Cambiando la password per "%user%"...
net user %user% %password%
if %errorlevel%==0 (
    echo Password per l'utente "%user%" cambiata con successo!
) else (
    echo Errore nel cambiare la password per l'utente "%user%".
)
pause
goto menu

:: Function to display detailed user information
:info_utente
set /p user= Inserisci il nome utente: 
echo *************************************
echo Informazioni dettagliate per "%user%":
echo *************************************
net user %user%
echo *************************************
pause
goto menu

:: Function to enable or disable a user
:abilita_disabilita
set /p user= Inserisci il nome utente: 
set /p scelta= Vuoi abilitare (1) o disabilitare (2) l'utente? 
if "%scelta%"=="1" (
    echo Abilitando l'utente "%user%"...
    net user %user% /active:yes
    if %errorlevel%==0 (
        echo Utente "%user%" abilitato con successo.
    ) else (
        echo Errore nel abilitare l'utente "%user%".
    )
) else if "%scelta%"=="2" (
    echo Disabilitando l'utente "%user%"...
    net user %user% /active:no
    if %errorlevel%==0 (
        echo Utente "%user%" disabilitato con successo.
    ) else (
        echo Errore nel disabilitare l'utente "%user%".
    )
) else (
    echo Scelta non valida.
)
pause
goto menu

:: Opening user profile folder
:apri_cartella
set /p user= Inserisci il nome utente: 
set folderpath=C:\Users\%user%
if exist "%folderpath%" (
    start explorer "%folderpath%"
    echo Cartella del profilo utente aperta con successo.
) else (
    echo La cartella "%folderpath%" non esiste.
)
pause
goto menu

:: Function to check group membership
:verifica_gruppo
set /p user= Inserisci il nome utente: 
set /p gruppo= Inserisci il nome del gruppo: 
echo Controllo appartenenza al gruppo "%gruppo%" per l'utente "%user%":
net localgroup %gruppo% | findstr /i "%user%" >nul
if %errorlevel%==0 (
    echo Utente presente nel gruppo.
) else (
    echo Utente NON presente nel gruppo.
)
pause
goto menu

:: Function to block a user
:blocca_utente
set /p user= Inserisci il nome utente da bloccare: 
echo Bloccando l'utente "%user%"...
wmic useraccount where name="%user%" set Lockout=True
if %errorlevel%==0 (
    echo Utente "%user%" bloccato con successo.
) else (
    echo Errore nel bloccare l'utente "%user%".
)
pause
goto menu

:: Function to unblock a user
:sblocca_utente
set /p user= Inserisci il nome utente da sbloccare: 
echo Sbloccando l'utente "%user%"...
wmic useraccount where name="%user%" set Lockout=False
if %errorlevel%==0 (
    echo Utente "%user%" sbloccato con successo.
) else (
    echo Errore nel sbloccare l'utente "%user%".
)
pause
goto menu

:: Function to add a user to a group
:aggiungi_gruppo
set /p user= Inserisci il nome utente: 
set /p gruppo= Inserisci il nome del gruppo: 
echo Aggiungendo "%user%" al gruppo "%gruppo%"...
net localgroup %gruppo% %user% /add
if %errorlevel%==0 (
    echo Utente aggiunto al gruppo con successo.
) else (
    echo Errore nell'aggiungere l'utente al gruppo.
)
pause
goto menu

:: Function to remove a user from a group
:rimuovi_gruppo
set /p user= Inserisci il nome utente: 
set /p gruppo= Inserisci il nome del gruppo: 
echo Rimuovendo "%user%" dal gruppo "%gruppo%"...
net localgroup %gruppo% %user% /delete
if %errorlevel%==0 (
    echo Utente rimosso dal gruppo con successo.
) else (
    echo Errore nel rimuovere l'utente dal gruppo.
)
pause
goto menu

:: Function to create a local group
:crea_gruppo
set /p gruppo= Inserisci il nome del nuovo gruppo: 
echo Creando il gruppo "%gruppo%"...
net localgroup %gruppo% /add
if %errorlevel%==0 (
    echo Gruppo "%gruppo%" creato con successo.
) else (
    echo Errore nella creazione del gruppo.
)
pause
goto menu

:: Function to delete a local group
:elimina_gruppo
set /p gruppo= Inserisci il nome del gruppo da eliminare: 
echo Eliminando il gruppo "%gruppo%"...
net localgroup %gruppo% /delete
if %errorlevel%==0 (
    echo Gruppo "%gruppo%" eliminato con successo.
) else (
    echo Errore nell'eliminare il gruppo.
)
pause
goto menu

:: Function to list all groups on the system
:visualizza_gruppi
echo *************************************
echo Visualizzando i gruppi esistenti...
echo *************************************
net localgroup
echo *************************************
pause
goto menu

:: Function to set password to expire
:password_scade
set /p user= Inserisci il nome utente: 
echo Impostando la password per "%user%" per scadere...
wmic useraccount where name="%user%" set PasswordExpires=True
if %errorlevel%==0 (
    echo Password impostata per scadere con successo.
) else (
    echo Errore nell'impostare la password.
)
pause
goto menu

:: Function to set password to never expire
:password_non_scade
set /p user= Inserisci il nome utente: 
echo Impostando la password per "%user%" per non scadere...
wmic useraccount where name="%user%" set PasswordExpires=False
if %errorlevel%==0 (
    echo Password impostata per non scadere con successo.
) else (
    echo Errore nell'impostare la password.
)
pause
goto menu

:: Function to force user to change password at next login
:forza_cambio_password
set /p user= Inserisci il nome utente: 
echo Forzando "%user%" a cambiare la password al prossimo login...
net user %user% /logonpasswordchg:yes
if %errorlevel%==0 (
    echo Utente forzato a cambiare la password con successo.
) else (
    echo Errore nel forzare il cambio password.
)
pause
goto menu

:: Function to prevent user from changing password
:non_cambiare_password
set /p user= Inserisci il nome utente: 
echo Impedendo a "%user%" di cambiare la password...
net user %user% /passwordchg:no
if %errorlevel%==0 (
    echo Utente non può cambiare la password con successo.
) else (
    echo Errore nell'impostare il blocco.
)
pause
goto menu

:: Function to set user description
:imposta_descrizione
set /p user= Inserisci il nome utente: 
set /p descrizione= Inserisci la descrizione per "%user%": 
echo Impostando la descrizione per "%user%"...
wmic useraccount where name="%user%" set Description="%descrizione%"
if %errorlevel%==0 (
    echo Descrizione impostata con successo.
) else (
    echo Errore nell'impostare la descrizione.
)
pause
goto menu

:: Function to set user's full name
:imposta_nome_completo
set /p user= Inserisci il nome utente: 
set /p fullname= Inserisci il nome completo per "%user%": 
echo Impostando il nome completo per "%user%"...
net user %user% /fullname:"%fullname%"
if %errorlevel%==0 (
    echo Nome completo impostato con successo.
) else (
    echo Errore nell'impostare il nome completo.
)
pause
goto menu

:: Function to set user's home directory
:imposta_home_dir
set /p user= Inserisci il nome utente: 
set /p homedir= Inserisci il percorso della directory home per "%user%": 
echo Impostando la directory home per "%user%"...
wmic useraccount where name="%user%" set HomeDirectory="%homedir%"
if %errorlevel%==0 (
    echo Directory home impostata con successo.
) else (
    echo Errore nell'impostare la directory home.
)
pause
goto menu

:: Function to view active user sessions
:visualizza_sessioni
echo *************************************
echo Visualizzando le sessioni utente attive...
echo *************************************
query user
echo *************************************
pause
goto menu

:: Function to disconnect a user session
:disconnetti_sessione
set /p session= Inserisci l'ID della sessione da disconnettere: 
echo Disconnettendo la sessione ID %session%...
logoff %session%
if %errorlevel%==0 (
    echo Sessione disconnessa con successo.
) else (
    echo Errore nel disconnettere la sessione.
)
pause
goto menu

:: Function to force password reset
:forza_reset_password
set /p user= Inserisci il nome utente: 
echo Forzando il reset della password per "%user%"...
net user %user% /reset
if %errorlevel%==0 (
    echo Reset password forzato con successo.
) else (
    echo Errore nel forzare il reset della password.
)
pause
goto menu

:: Function to show user's password status
:mostra_stato_password
set /p user= Inserisci il nome utente: 
echo Stato della password per "%user%":
net user %user%
pause
goto menu

:: Function to create a user with a complex password
:crea_utente_complesso
set /p user= Inserisci il nome utente da creare: 
set /p password= Inserisci una password complessa per "%user%": 
echo Creando l'utente "%user%" con una password complessa...
net user %user% %password% /add /passwordchg:yes /passwordreq:yes
if %errorlevel%==0 (
    echo Utente creato con successo.
) else (
    echo Errore nella creazione dell'utente.
)
pause
goto menu

:: Function to enable audit for a user
:abilita_audit
set /p user= Inserisci il nome utente per abilitare l'audit: 
echo Abilitando audit per l'utente "%user%"...
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
if %errorlevel%==0 (
    echo Audit abilitato con successo.
) else (
    echo Errore nell'abilitare l'audit.
)
pause
goto menu

:: Function to disable audit for a user
:disabilita_audit
set /p user= Inserisci il nome utente per disabilitare l'audit: 
echo Disabilitando audit per l'utente "%user%"...
auditpol /set /subcategory:"Logon" /success:disable /failure:disable
if %errorlevel%==0 (
    echo Audit disabilitato con successo.
) else (
    echo Errore nel disabilitare l'audit.
)
pause
goto menu

:: Function to display user's profile path
:mostra_percorso_profilo
set /p user= Inserisci il nome utente: 
echo Percorso del profilo per "%user%":
wmic useraccount where name="%user%" get ProfilePath
pause
goto menu

:: Function to change user's full name
:cambia_nome_completo
set /p user= Inserisci il nome utente: 
set /p fullname= Inserisci il nuovo nome completo per "%user%": 
echo Cambiando il nome completo per "%user%"...
net user %user% /fullname:"%fullname%"
if %errorlevel%==0 (
    echo Nome completo cambiato con successo.
) else (
    echo Errore nel cambiare il nome completo.
)
pause
goto menu

:: Function to display user's last login
:mostra_ultimo_login
set /p user= Inserisci il nome utente: 
echo Ultimo login per "%user%":
wmic useraccount where name="%user%" get LastLogin
pause
goto menu

:: Function to reset user's password
:resetta_password
set /p user= Inserisci il nome utente: 
set /p password= Inserisci la nuova password per "%user%": 
echo Resettando la password per "%user%"...
net user %user% %password%
if %errorlevel%==0 (
    echo Password resettata con successo.
) else (
    echo Errore nel resettare la password.
)
pause
goto menu

:: Function to activate user account
:attiva_account
set /p user= Inserisci il nome utente da attivare: 
echo Attivando l'account per "%user%"...
net user %user% /active:yes
if %errorlevel%==0 (
    echo Account attivato con successo.
) else (
    echo Errore nell'attivare l'account.
)
pause
goto menu

:: Function to deactivate user account
:disattiva_account
set /p user= Inserisci il nome utente da disattivare: 
echo Disattivando l'account per "%user%"...
net user %user% /active:no
if %errorlevel%==0 (
    echo Account disattivato con successo.
) else (
    echo Errore nel disattivare l'account.
)
pause
goto menu

:: Function to force screen lock for a user
:forza_blocco_schermo
set /p user= Inserisci il nome utente: 
echo Forzando il blocco dello schermo per "%user%"...
tscon %user% /lock
if %errorlevel%==0 (
    echo Schermo bloccato con successo.
) else (
    echo Errore nel bloccare lo schermo.
)
pause
goto menu

:: Function to schedule user disconnection
:schedula_disconnessione
set /p user= Inserisci il nome utente: 
set /p tempo= Inserisci il tempo in minuti per disconnettere "%user%": 
echo Schedulando la disconnessione di "%user%" tra %tempo% minuti...
shutdown /l /f /t %tempo% /c "Disconnessione programmata per l'utente %user%"
if %errorlevel%==0 (
    echo Disconnessione schedulata con successo.
) else (
    echo Errore nella schedulazione.
)
pause
goto menu

:: Function to set session time limit for a user
:imposta_limite_tempo
set /p user= Inserisci il nome utente: 
set /p tempo= Inserisci il limite di tempo in minuti: 
echo Impostando un limite di tempo di %tempo% minuti per "%user%"...
wmic useraccount where name="%user%" set MaxPasswordAge=%tempo%
if %errorlevel%==0 (
    echo Limite di tempo impostato con successo.
) else (
    echo Errore nell'impostare il limite di tempo.
)
pause
goto menu

:: Function to display user's password policies
:visualizza_politiche_password
set /p user= Inserisci il nome utente: 
echo Politiche password per "%user%":
net user %user%
pause
goto menu

:: Function to configure Remote Desktop access for a user
:configura_rdp
set /p user= Inserisci il nome utente: 
echo Configurando l'accesso Remote Desktop per "%user%"...
net localgroup "Remote Desktop Users" %user% /add
if %errorlevel%==0 (
    echo Accesso Remote Desktop configurato con successo.
) else (
    echo Errore nella configurazione dell'accesso Remote Desktop.
)
pause
goto menu

:: Function to set disk quota for a user
:imposta_quota_disco
set /p user= Inserisci il nome utente: 
set /p quota= Inserisci la quota disco in MB per "%user%": 
echo Impostando una quota disco di %quota% MB per "%user%"...
fsutil quota modify C: %quota% %user%
if %errorlevel%==0 (
    echo Quota disco impostata con successo.
) else (
    echo Errore nell'impostare la quota disco.
)
pause
goto menu

:: Function to enable or disable password change
:abilita_disabilita_cambio_password
set /p user= Inserisci il nome utente: 
set /p scelta= Vuoi abilitare (1) o disabilitare (2) il cambiamento password?
if "%scelta%"=="1" (
    echo Abilitando il cambiamento password per "%user%"...
    net user %user% /passwordchg:yes
    if %errorlevel%==0 (
        echo Cambiamento password abilitato con successo.
    ) else (
        echo Errore nell'abilitare il cambiamento password.
    )
) else if "%scelta%"=="2" (
    echo Disabilitando il cambiamento password per "%user%"...
    net user %user% /passwordchg:no
    if %errorlevel%==0 (
        echo Cambiamento password disabilitato con successo.
    ) else (
        echo Errore nel disabilitare il cambiamento password.
    )
) else (
    echo Scelta non valida.
)
pause
goto menu

:: Function to block all login courses for a user
:blocca_corsi_login
set /p user= Inserisci il nome utente: 
echo Bloccando tutti i corsi di login per "%user%"...
wmic useraccount where name="%user%" set Lockout=True
if %errorlevel%==0 (
    echo Corsi di login bloccati con successo.
) else (
    echo Errore nel bloccare i corsi di login.
)
pause
goto menu

:: Function to unblock all login courses for a user
:sblocca_corsi_login
set /p user= Inserisci il nome utente: 
echo Sbloccando tutti i corsi di login per "%user%"...
wmic useraccount where name="%user%" set Lockout=False
if %errorlevel%==0 (
    echo Corsi di login sbloccati con successo.
) else (
    echo Errore nel sbloccare i corsi di login.
)
pause
goto menu

:: Function to enable or disable automatic execution for a user
:abilita_esecuzione_automatica
set /p user= Inserisci il nome utente: 
set /p scelta= Vuoi abilitare (1) o disabilitare (2) l'esecuzione automatica?
if "%scelta%"=="1" (
    echo Abilitando l'esecuzione automatica per "%user%"...
    reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "AutoRun" /t REG_SZ /d "C:\Path\To\Your\Program.exe" /f
    if %errorlevel%==0 (
        echo Esecuzione automatica abilitata con successo.
    ) else (
        echo Errore nell'abilitare l'esecuzione automatica.
    )
) else if "%scelta%"=="2" (
    echo Disabilitando l'esecuzione automatica per "%user%"...
    reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "AutoRun" /f
    if %errorlevel%==0 (
        echo Esecuzione automatica disabilitata con successo.
    ) else (
        echo Errore nel disabilitare l'esecuzione automatica.
    )
) else (
    echo Scelta non valida.
)
pause
goto menu

:: Function to set login script for a user
:imposta_script_login
set /p user= Inserisci il nome utente: 
set /p script= Inserisci il percorso dello script di login: 
echo Impostando lo script di login per "%user%"...
wmic useraccount where name="%user%" set ScriptPath="%script%"
if %errorlevel%==0 (
    echo Script di login impostato con successo.
) else (
    echo Errore nell'impostare lo script di login.
)
pause
goto menu

:: Function to remove login script for a user
:rimuovi_script_login
set /p user= Inserisci il nome utente: 
echo Rimuovendo lo script di login per "%user%"...
wmic useraccount where name="%user%" set ScriptPath=""
if %errorlevel%==0 (
    echo Script di login rimosso con successo.
) else (
    echo Errore nel rimuovere lo script di login.
)
pause
goto menu

:: Function to view user's environment variables
:visualizza_variabili_env
set /p user= Inserisci il nome utente: 
echo Visualizzando le variabili d'ambiente per "%user%"...
runas /user:%user% "cmd /c set"
pause
goto menu

:: Function to modify user's environment variables
:modifica_variabili_env
set /p user= Inserisci il nome utente: 
set /p var= Inserisci il nome della variabile: 
set /p valore= Inserisci il valore della variabile: 
echo Modificando la variabile "%var%" per "%user%"...
reg add "HKEY_USERS\S-1-5-21-...\Environment" /v "%var%" /t REG_SZ /d "%valore%" /f
:: Nota: Sostituisci "S-1-5-21-..." con il SID corretto dell'utente
if %errorlevel%==0 (
    echo Variabile modificata con successo.
) else (
    echo Errore nella modifica della variabile.
)
pause
goto menu

:: Function to restore default environment variables
:ripristina_variabili_env
set /p user= Inserisci il nome utente: 
echo Ripristinando le variabili d'ambiente predefinite per "%user%"...
:: Questo richiede di sapere quali variabili ripristinare; un esempio generico:
reg delete "HKEY_USERS\S-1-5-21-...\Environment" /f
:: Nota: Sostituisci "S-1-5-21-..." con il SID corretto dell'utente
if %errorlevel%==0 (
    echo Variabili d'ambiente ripristinate con successo.
) else (
    echo Errore nel ripristinare le variabili d'ambiente.
)
pause
goto menu

:: Exit function
:uscire
echo Uscita dal programma...
pause
exit

