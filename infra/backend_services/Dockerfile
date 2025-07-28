FROM python:3.11-slim

WORKDIR /app

# 必要なファイルをコピー
COPY . /app

# 必要なパッケージインストール
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# .envはビルド時には不要（ランタイムでマウント or 環境変数で渡す）
# EXPOSEは不要（Container Appsは常に 80/443）

CMD ["python", "pg_mcp_server.py"]