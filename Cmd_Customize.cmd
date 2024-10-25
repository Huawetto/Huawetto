@echo off
:: Set the text (1=blue) and background (4=red)
color 38
start cmd /k "color 3D"

:: Available color codes:
:: 0 = Black       8 = Gray
:: 1 = Blue        9 = Light Blue
:: 2 = Green       A = Light Green
:: 3 = Aqua        B = Light Aqua
:: 4 = Red         C = Light Red
:: 5 = Purple      D = Light Purple
:: 6 = Yellow      E = Light Yellow
:: 7 = White       F = Bright White

:: Example combinations:
:: color 02  -> Black background, Light Green text
:: color 4F  -> Red background, Bright White text
:: color EC  -> Yellow background, Light Red text
