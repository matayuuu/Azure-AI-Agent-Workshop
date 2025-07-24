#!/bin/bash

set -x 
# set -e # ログ出力（デバック時）

# ==== 変数定義 ====
RANDOM_INT=$(shuf -i 1-9999 -n 1)
LOCATION="westus"  
RESOURCE_GROUP_NAME="azure-ai-agent-workshop-$RANDOM_INT"

# PostgreSQL/CosmosDB
PG_SERVER_NAME="pgserver-3aw-$RANDOM_INT"
PG_DB_NAME="ecdb"
PG_ADMIN_USER="ecadmin"
PG_ADMIN_PASS="YourP@ssword123!"
COSMOS_ACCOUNT_NAME="cosmos-3aw-$RANDOM_INT"
COSMOS_DB_NAME="twitterdb"
COSMOS_CONTAINER_NAME="tweets"
COSMOS_PARTITION_KEY="/tweet_id"
COSMOS_DB_THROUGHPUT=400

# AI Foundry
AI_FOUNDRY_NAME="foundry-3aw-$RANDOM_INT"
AI_PROJECT_NAME="${AI_FOUNDRY_NAME}-proj"
AI_MODEL_DEPLOYMENT_NAME="gpt-4.1"

# ==== リソースグループ作成 ====
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

# ==== Bicep でデプロイ ====
az deployment group create \
  --resource-group $RESOURCE_GROUP_NAME \
  --name main \
  --template-file ./infra/main.bicep \
  --parameters \
      location=$LOCATION \
      pgServerName=$PG_SERVER_NAME \
      pgDbName=$PG_DB_NAME \
      pgAdminUser=$PG_ADMIN_USER \
      pgAdminPassword=$PG_ADMIN_PASS \
      cosmosAccountName=$COSMOS_ACCOUNT_NAME \
      cosmosDbName=$COSMOS_DB_NAME \
      cosmosContainerName=$COSMOS_CONTAINER_NAME \
      cosmosPartitionKey=$COSMOS_PARTITION_KEY \
      cosmosDbThroughput=$COSMOS_DB_THROUGHPUT \
      aiFoundryName=$AI_FOUNDRY_NAME \
      aiProjectName=$AI_PROJECT_NAME \
      aiModelDeploymentName=$AI_MODEL_DEPLOYMENT_NAME \
  --no-prompt --debug

# ==== DB 接続情報取得 ====
PG_HOST=$(az postgres flexible-server show \
  --name "$PG_SERVER_NAME" \
  --resource-group "$RESOURCE_GROUP_NAME" \
  --query "fullyQualifiedDomainName" -o tsv)

COSMOS_KEY=$(az cosmosdb keys list \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP_NAME \
  --type keys \
  --query "primaryMasterKey" -o tsv)
COSMOS_URI="https://${COSMOS_ACCOUNT_NAME}.documents.azure.com:443/"

echo "PG_HOST: $PG_HOST"
echo "COSMOS_URI: $COSMOS_URI"
echo "COSMOS_KEY: $COSMOS_KEY"

# ==== DB へデータ投入 ====
echo "# --- PostgreSQL テーブル作成＆CSV投入 ---"
python ./infra/import_csv_to_postgres.py "$PG_HOST" "$PG_DB_NAME" "$PG_ADMIN_USER" "$PG_ADMIN_PASS" "./infra/sample_data/csv"

echo "# --- Cosmos DB (NoSQL) へtweets.json投入 ---"
python ./infra/import_jsonl_to_cosmos.py "$COSMOS_URI" "$COSMOS_KEY" "$COSMOS_DB_NAME" "$COSMOS_CONTAINER_NAME" "./infra/sample_data/jsonl"

echo "done"
echo "== 準備完了！=="
