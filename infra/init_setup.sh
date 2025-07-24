#!/bin/bash

set -e

# ===== 変数定義 =====
RESOURCE_GROUP_NAME="azure-ai-agent-workshop"
LOCATION="westus"                     
PG_SERVER_NAME="pgserver"
PG_DB_NAME="ecdb"
PG_ADMIN_USER="ecadmin"
PG_ADMIN_PASS="YourP@ssword123!"         
COSMOS_ACCOUNT_NAME="cosmos"
COSMOS_DB_NAME="twitterdb"
COSMOS_CONTAINER_NAME="tweets"
COSMOS_PARTITION_KEY="/tweet_id"

# Python依存パッケージのインストール
echo "== pip install dependencies =="
pip install -r ./requirements.txt

# ===== リソースグループ作成 =====
echo "== リソースグループ作成 =="
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

# ===== Cosmos DBプロバイダー登録＆完了待ち =====
echo "== Cosmos DBプロバイダーの登録 =="
az provider register --namespace Microsoft.DocumentDB
while true; do
  STATUS=$(az provider show --namespace Microsoft.DocumentDB --query "registrationState" -o tsv)
  echo "registrationState: $STATUS"
  if [ "$STATUS" = "Registered" ]; then break; fi
  sleep 30
done

# ===== PostgreSQL Flexible Server作成 =====
echo "== PostgreSQL Flexible Server作成 =="
az postgres flexible-server create \
  --name $PG_SERVER_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --location $LOCATION \
  --admin-user $PG_ADMIN_USER \
  --admin-password $PG_ADMIN_PASS \
  --database-name $PG_DB_NAME \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --version 15 \
  --public-access Enabled

az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP_NAME \
  --name $PG_SERVER_NAME \
  --rule-name allowall \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255

# ===== Cosmos DB for NoSQL 作成 =====
echo "== Cosmos DB for NoSQL 作成 =="
az cosmosdb create \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --locations regionName=$LOCATION failoverPriority=0 \
  --kind GlobalDocumentDB

# データベース作成
az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --name $COSMOS_DB_NAME

# コンテナ（コレクション）作成
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --database-name $COSMOS_DB_NAME \
  --name $COSMOS_CONTAINER_NAME \
  --partition-key-path $COSMOS_PARTITION_KEY \
  --throughput 400

# ===== Cosmos DB (NoSQL) のキー取得 =====
COSMOS_KEY=$(az cosmosdb keys list \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --type keys \
  --query "primaryMasterKey" -o tsv)

COSMOS_URI="https://${COSMOS_ACCOUNT_NAME}.documents.azure.com:443/"

echo "Cosmos NoSQL URI: $COSMOS_URI"
echo "Cosmos NoSQL KEY: $COSMOS_KEY"

# ===== PostgreSQLサーバーFQDNの取得 =====
PG_HOST=$(az postgres flexible-server show \
  --name $PG_SERVER_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --query "fullyQualifiedDomainName" -o tsv)

echo "PostgreSQL HOST: $PG_HOST"

# ===== DB・コンテナにデータ投入 =====
echo "# --- PostgreSQL テーブル作成＆CSV投入 ---"
python ./infra/import_csv_to_postgres.py "$PG_HOST" "$PG_DB_NAME" "$PG_ADMIN_USER" "$PG_ADMIN_PASS" "./infra/sample_data/csv"

echo "# --- Cosmos DB (NoSQL) へtweets.json投入 ---"
python ./infra/import_jsonl_to_cosmos.py "$COSMOS_URI" "$COSMOS_KEY" "$COSMOS_DB_NAME" "$COSMOS_CONTAINER_NAME" "./infra/sample_data/jsonl"

echo "done"
echo "== 準備完了！=="
