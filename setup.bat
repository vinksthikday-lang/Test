@echo off
echo 🤖 Advanced Discord Bot Setup
echo =============================

echo 📝 Checking Docker...
docker --version
if %errorlevel% neq 0 (
    echo ❌ Docker not found. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo 📁 Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs

echo 🚀 Building and starting services...
docker-compose up --build -d

echo ✅ Setup completed!
echo 📊 Web Dashboard: http://localhost:5000
echo 🐳 Check running containers with: docker ps
pause