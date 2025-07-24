FROM mcr.microsoft.com/devcontainers/python:3.11

# psql (PostgreSQL client)のインストール
RUN apt-get update && \
    apt-get install -y postgresql-client

# mongoimport (MongoDB client)のインストール
RUN apt-get install -y mongodb-clients

# azure-cli のインストール可能
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash