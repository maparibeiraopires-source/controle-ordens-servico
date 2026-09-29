@echo off
setlocal
cd /d "%~dp0"

title CONTROLE DE ORDENS DE SERVICO - 2026

if not exist "app.py" (
    echo.
    echo ERRO: app.py nao foi encontrado nesta pasta.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO ao criar o ambiente virtual.
        echo Verifique se o Python esta instalado.
        pause
        exit /b 1
    )
)

echo.
echo Verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO ao instalar as dependencias.
    pause
    exit /b 1
)

echo.
echo Abrindo o Dashboard...
echo.
".venv\Scripts\python.exe" -m streamlit run app.py

pause
