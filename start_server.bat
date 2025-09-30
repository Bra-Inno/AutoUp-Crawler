@echo off
echo 🚀 启动热榜爬虫服务器...
echo ====================================

cd /d "d:\codes\Python\hotlist-crawler"

echo 📦 激活Python环境并安装依赖...
pip install -r requirements.txt

echo.
echo 🌐 启动FastAPI服务器...
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause