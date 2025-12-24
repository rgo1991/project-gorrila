# Fix httpx compatibility issue
Write-Host "Fixing httpx compatibility..." -ForegroundColor Yellow

# Uninstall current httpx
Write-Host "Uninstalling httpx..." -ForegroundColor Cyan
pip uninstall httpx -y

# Install compatible version
Write-Host "Installing httpx 0.27.0..." -ForegroundColor Cyan
pip install httpx==0.27.0

# Verify
Write-Host "Verifying installation..." -ForegroundColor Cyan
python -c "import httpx; print('httpx version:', httpx.__version__)"

Write-Host "`nDone! You can now run: python execution\web_app.py" -ForegroundColor Green

