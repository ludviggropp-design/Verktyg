@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"

if not exist ".venv" (
  echo Forsta gangen du kor detta - forbereder verktyget.
  echo Det tar en liten stund, gor ingenting nu...
  echo.
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo Kunde inte hitta Python. Kontrollera att Python ar installerat
    echo och att rutan "Add python.exe to PATH" kryssades i vid installationen.
    echo Se installationsguiden och gor om steg 1, forsok sedan igen.
    echo.
    pause
    exit /b 1
  )
  call ".venv\Scripts\activate.bat"
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Nagot gick fel vid installationen. Kontrollera din internetuppkoppling
    echo och forsok igen.
    echo.
    pause
    exit /b 1
  )
) else (
  call ".venv\Scripts\activate.bat"
)

echo Soker efter namningar av Uppsalahem...
echo.
python -m monitor.main

echo.
echo Oppnar rapporten i webblasaren...
start "" "%cd%\data\report.html"

echo.
echo Klart! Rapporten oppnas i din webblasare.
echo Det har fonstret kan du stanga nar du vill.
pause
