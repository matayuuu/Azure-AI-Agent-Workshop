import os
import json
import asyncio
import asyncpg
from dotenv import load_dotenv
from fastmcp import FastMCP
from azure.cosmos import CosmosClient

load_dotenv()

# PostgreSQL 接続情報
PG_CONFIG = {
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "database": os.getenv("PGDATABASE"),
    "host": os.getenv("PGHOST"),
    "port": int(os.getenv("PGPORT", 5432)),
}

# CosmosDB 接続情報
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME", "twitterdb")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "tweets")

# MCP サーバ定義
mcp = FastMCP(
    name="Retail Shop + Twitter Analytics",
    instructions="PostgreSQLの各種マスター、注文、ユーザー情報と、CosmosDBに格納されたツイート分析データを、ツールとして提供します。"
)

# PostgreSQL 共通ヘルパ
async def get_conn():
    return await asyncpg.connect(**PG_CONFIG)

def to_json(data):
    return json.dumps(data, ensure_ascii=False, default=str)

# --- PostgreSQL Tools ---
@mcp.tool(description="全カテゴリ一覧を取得")
async def get_all_categories() -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM categories")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="全商品一覧（カテゴリで絞り込み可）")
async def get_products(category_id: int = None) -> str:
    conn = await get_conn()
    try:
        if category_id:
            rows = await conn.fetch("SELECT * FROM products WHERE category_id = $1", category_id)
        else:
            rows = await conn.fetch("SELECT * FROM products")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="特定ユーザーの注文一覧を取得")
async def get_orders_by_user(user_id: int) -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM orders WHERE user_id = $1", user_id)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="注文詳細を取得")
async def get_order_details(order_id: int) -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM order_details WHERE order_id = $1", order_id)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="在庫状況を取得")
async def get_inventory(product_id: int) -> str:
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM inventory WHERE product_id = $1", product_id)
        return to_json(dict(row) if row else {})
    finally:
        await conn.close()

@mcp.tool(description="ユーザー一覧を取得")
async def get_users() -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM users")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="配送状況を取得")
async def get_shipping_status(order_id: int) -> str:
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM shipping_status WHERE order_id = $1", order_id)
        return to_json(dict(row) if row else {})
    finally:
        await conn.close()

# --- CosmosDB (tweets) Tools ---
def get_cosmos_container():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB_NAME)
    return db.get_container_client(COSMOS_CONTAINER_NAME)

@mcp.tool(description="全ツイート件数取得")
async def get_tweet_count() -> str:
    container = get_cosmos_container()
    count = container.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
    return to_json({"count": list(count)[0]})

@mcp.tool(description="tweet_idでツイートを検索")
async def get_tweet_by_id(tweet_id: str) -> str:
    container = get_cosmos_container()
    items = container.query_items(
        query="SELECT * FROM c WHERE c.tweet_id = @tweet_id",
        parameters=[{"name": "@tweet_id", "value": tweet_id}],
        enable_cross_partition_query=True
    )
    return to_json(list(items))

@mcp.tool(description="ユーザーごとのツイート数ランキング（上位10件）")
async def get_top_users_by_tweet() -> str:
    container = get_cosmos_container()
    query = """
    SELECT c.user.screen_name AS screen_name, COUNT(1) AS tweet_count
    FROM c
    GROUP BY c.user.screen_name
    ORDER BY tweet_count DESC
    OFFSET 0 LIMIT 10
    """
    items = container.query_items(query, enable_cross_partition_query=True)
    return to_json(list(items))

# さらに必要に応じて CosmosDB のパーティションキーや特定フィールドで集計・分析系ツールも追加できます

# --- サーバ起動 ---
if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async(host="0.0.0.0", port=8000))
