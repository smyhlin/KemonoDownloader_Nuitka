@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo KemonoDownloader onefile build starting
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtual environment already exists.
)

echo [2/5] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [3/5] Updating pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to update pip/setuptools/wheel.
    pause
    exit /b 1
)

echo [4/5] Installing requirements...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements.txt.
        pause
        exit /b 1
    )
) else (
    echo [WARN] requirements.txt not found, skipping.
)

echo [5/5] Installing Nuitka...
python -m pip install --upgrade nuitka ordered-set zstandard
if errorlevel 1 (
    echo [ERROR] Failed to install Nuitka.
    pause
    exit /b 1
)

echo.
echo Building onefile executable...
python -m nuitka --mode=onefile --windows-console-mode=disable --enable-plugin=pyqt6 --windows-icon-from-ico=assets\icons\KemonoDownloader.ico --include-data-dir=src/kemonodownloader/resources=kemonodownloader/resources --include-data-dir=assets=assets --output-dir=build src/kemonodownloader
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build finished successfully.
echo Output:
echo build\kemonodownloader.exe
echo ========================================
pause