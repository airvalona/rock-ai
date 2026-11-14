Write-Host "=== Installing rock.ai (Autonomous 24/7 Multi-Agent Fleet) ===" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3 is required. Please install Python 3.10+ from python.org or Microsoft Store."
    exit 1
}

python -m pip install --upgrade pip
pip install -e .

Write-Host "=== rock.ai installed successfully! ===" -ForegroundColor Green
Write-Host "Run 'rock onboard' to configure your agent fleet." -ForegroundColor Yellow
