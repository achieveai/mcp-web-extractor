@echo off
REM Publishing script for mcp-web-extractor (Windows)

setlocal enabledelayedexpansion

echo MCP Trafilatura Publishing Script
echo ==================================
echo.

REM Check if version argument provided
if "%~1"=="" (
    echo Usage: publish.bat ^<version^> [--test]
    echo Example: publish.bat 0.1.0 --test
    exit /b 1
)

set VERSION=%~1
set TEST_MODE=%~2

REM Check Python
echo Checking prerequisites...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
echo [OK] Python found

REM Install/upgrade build tools
echo.
echo Installing/upgrading build tools...
python -m pip install -U pip build twine >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install build tools
    exit /b 1
)
echo [OK] Build tools ready

REM Update version in pyproject.toml
echo.
echo Updating version to %VERSION%...
powershell -Command "(Get-Content pyproject.toml) -replace '^version = \".*\"', 'version = \"%VERSION%\"' | Set-Content pyproject.toml"
echo [OK] Version updated in pyproject.toml

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul
for /d %%i in (*.egg-info) do rmdir /s /q "%%i" 2>nul
for /d %%i in (src\*.egg-info) do rmdir /s /q "%%i" 2>nul
echo [OK] Clean build environment

REM Build the package
echo.
echo Building package...
python -m build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    exit /b 1
)
echo [OK] Package built successfully

REM Check the package
echo.
echo Verifying package...
python -m twine check dist\*
if %errorlevel% neq 0 (
    echo [ERROR] Package verification failed
    exit /b 1
)
echo [OK] Package verification passed

REM List built files
echo.
echo Built files:
dir dist

REM Handle test vs production publishing
if "%TEST_MODE%"=="--test" (
    echo.
    echo [WARNING] TEST MODE - Publishing to TestPyPI
    echo.
    
    if "%TESTPYPI_TOKEN%"=="" (
        echo [WARNING] TESTPYPI_TOKEN not set. You'll need to enter credentials manually.
        echo Get your token from: https://test.pypi.org/manage/account/token/
    ) else (
        set TWINE_USERNAME=__token__
        set TWINE_PASSWORD=%TESTPYPI_TOKEN%
    )
    
    echo Uploading to TestPyPI...
    python -m twine upload -r testpypi dist\*
    
    echo.
    echo [OK] Published to TestPyPI!
    echo.
    echo Test installation with:
    echo   pip install -i https://test.pypi.org/simple/ mcp-web-extractor==%VERSION% --extra-index-url https://pypi.org/simple
    echo.
    echo Or with uvx:
    echo   uvx --index-url https://test.pypi.org/simple/ mcp-web-extractor
    
) else (
    echo.
    echo [WARNING] PRODUCTION MODE - Publishing to PyPI
    echo.
    
    REM Confirmation prompt
    set /p CONFIRM=Are you sure you want to publish v%VERSION% to PyPI? (y/N): 
    if /i not "!CONFIRM!"=="y" (
        echo [WARNING] Publishing cancelled
        exit /b 1
    )
    
    if "%PYPI_TOKEN%"=="" (
        echo [WARNING] PYPI_TOKEN not set. You'll need to enter credentials manually.
        echo Get your token from: https://pypi.org/manage/account/token/
    ) else (
        set TWINE_USERNAME=__token__
        set TWINE_PASSWORD=%PYPI_TOKEN%
    )
    
    echo.
    echo Uploading to PyPI...
    python -m twine upload dist\*
    
    echo.
    echo [OK] Published to PyPI!
    echo.
    echo Package available at: https://pypi.org/project/mcp-web-extractor/%VERSION%/
    echo.
    echo Install with:
    echo   pip install mcp-web-extractor
    echo.
    echo Or run directly with:
    echo   uvx mcp-web-extractor
    echo.
    echo Don't forget to:
    echo   1. Create a git tag: git tag -a v%VERSION% -m "Release version %VERSION%"
    echo   2. Push the tag: git push origin v%VERSION%
    echo   3. Create a GitHub release
)

echo.
echo [OK] Publishing complete!

endlocal