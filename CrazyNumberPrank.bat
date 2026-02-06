@echo off
color 0A
:loop
set /a r=%random% %% 1000
echo %random%%r%%random%%r%%random%
goto loop

