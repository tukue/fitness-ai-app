# Set environment variables for CI testing
$env:GITHUB_ACTIONS = "true"
$env:FLASK_ENV = "testing"
$env:SECRET_KEY = "github-actions-test-key"
$env:DATABASE_URL = "sqlite:///:memory:"
$env:HUGGINGFACE_API_KEY = "dummy-key-for-testing"

# Install dependencies like in CI
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install flake8 pytest

# Run linting
Write-Host "`nRunning Flake8 checks..." -ForegroundColor Green
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
Write-Host "`nRunning Pytest..." -ForegroundColor Green
python -m pytest tests/ -v
