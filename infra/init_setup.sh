#!/bin/bash

set -e

# ===== 変数定義 =====
RANDOM_INT=$(shuf -i 1-9999 -n 1)
RESOURCE_GROUP_NAME="azure-ai-agent-workshop-$RANDOM_INT"
LOCATION="japaneast"                     # 必要に応じて変更
PG_SERVER_NAME="pgserver$RANDOM_INT"
PG_DB_NAME="ecdb"
PG_ADMIN_USER="ecadmin"
PG_ADMIN_PASS="YourP@ssword123!"         # 必ず変更！
COSMOS_ACCOUNT_NAME="cosmos$RANDOM_INT"
COSMOS_DB_NAME="twitterdb"
COSMOS_COLLECTION_NAME="tweets"

# ===== リソースグループ作成 =====
echo "== リソースグループ作成 =="
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

# ===== Cosmos DBリソースプロバイダー登録＆完了待ち =====
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

# FWルール（全開放・検証用途のみ！本番はIP制限推奨）
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP_NAME \
  --name $PG_SERVER_NAME \
  --rule-name allowall \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255

# ===== Cosmos DB (MongoDB API)作成 =====
echo "== Cosmos DB for MongoDB作成 =="
az cosmosdb create \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --locations regionName=$LOCATION failoverPriority=0 \
  --capabilities EnableMongo \
  --kind MongoDB

# Cosmos DBデータベース作成
az cosmosdb mongodb database create \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --name $COSMOS_DB_NAME

# Cosmos DBコレクション作成
az cosmosdb mongodb collection create \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --database-name $COSMOS_DB_NAME \
  --name $COSMOS_COLLECTION_NAME \
  --throughput 400

# ===== Cosmos DB (MongoDB) 接続文字列の取得 =====
COSMOS_CONN_STR=$(az cosmosdb keys list \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv)

echo "Cosmos MongoDB URI: $COSMOS_CONN_STR"

# ===== PostgreSQLサーバーFQDNの取得 =====
PG_HOST=$(az postgres flexible-server show \
  --name $PG_SERVER_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --query "fullyQualifiedDomainName" -o tsv)

echo "PostgreSQL HOST: $PG_HOST"

echo ""
echo "== 次の手順でDB・コレクションにデータ投入 =="

echo "# --- PostgreSQL テーブル作成＆CSV投入 ---"
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -f create_tables.sql"
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy categories FROM './sample_data/csv/categories.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy products FROM './sample_data/csv/products.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy inventory FROM './sample_data/csv/inventory.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy users FROM './sample_data/csv/users.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy orders FROM './sample_data/csv/orders.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy order_details FROM './sample_data/csv/order_details.csv' CSV HEADER;\""
echo "psql -h $PG_HOST -U $PG_ADMIN_USER -d $PG_DB_NAME -c \"\\copy shipping_status FROM './sample_data/csv/shipping_status.csv' CSV HEADER;\""
echo ""
echo "# --- Cosmos DB (MongoDB) へtweets.json投入 ---"
echo "mongoimport --uri \"$COSMOS_CONN_STR\" --collection $COSMOS_COLLECTION_NAME --file ./sample_data/json/tweets.json --jsonArray"
echo ""
echo "== 準備完了！=="