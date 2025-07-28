import os
import json
import asyncio
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
from fastmcp import FastMCP
from azure.cosmos import CosmosClient

load_dotenv()

# PostgreSQL 接続情報
PG_CONFIG = {
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASS"),
    "database": os.getenv("PG_DB"),
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PGPORT", 5432)),
}

# CosmosDB 接続情報
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = os.getenv("COSMOS_DB", "twitterdb")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER", "tweets")

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
@mcp.tool(description="""
    全カテゴリ一覧を取得します。

    :return: JSON形式でカテゴリの一覧を返します。
    :rtype: str
    """)
async def get_all_categories() -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM categories")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    指定カテゴリの全商品一覧を取得します。

    :param category_id (int): 商品カテゴリID（必須）
    :rtype: str

    :return: JSON形式で商品の一覧を返します。
    :rtype: str
    """)
async def get_products(category_id: int) -> str:
    conn = await get_conn()
    try:
        if category_id:
            rows = await conn.fetch("SELECT * FROM products WHERE category_id = $1", category_id)
        else:
            rows = await conn.fetch("SELECT * FROM products")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    特定ユーザーの注文一覧を取得します。

    :param user_id (int): ユーザーID
    :rtype: str

    :return: JSON形式で注文の一覧を返します。
    :rtype: str
    """)
async def get_orders_by_user(user_id: int) -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM orders WHERE user_id = $1", user_id)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    注文詳細を取得します。

    :param order_id (int): 注文ID
    :rtype: str

    :return: JSON形式で注文詳細情報を返します。
    :rtype: str
    """)
async def get_order_details(order_id: int) -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM order_details WHERE order_id = $1", order_id)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    指定商品の在庫状況を取得します。

    :param product_id (int): 商品ID
    :rtype: str

    :return: JSON形式で在庫情報を返します。
    :rtype: str
    """)
async def get_inventory(product_id: int) -> str:
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM inventory WHERE product_id = $1", product_id)
        return to_json(dict(row) if row else {})
    finally:
        await conn.close()

@mcp.tool(description="""
    全ユーザー一覧を取得します。

    :return: JSON形式でユーザーの一覧を返します。
    :rtype: str
    """)
async def get_users() -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM users")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    配送状況を取得します。

    :param order_id (int): 注文ID
    :rtype: str

    :return: JSON形式で配送状況を返します。
    :rtype: str
    """)
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

@mcp.tool(description="""
    全ツイート件数を取得します。

    :return: JSON形式でツイート件数を返します。
    :rtype: str
    """)
async def get_tweet_count() -> str:
    container = get_cosmos_container()
    count = container.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
    return to_json({"count": list(count)[0]})

@mcp.tool(description="""
    ユーザーごとのツイート数ランキング（上位10件）を取得します。

    :return: JSON形式でscreen_nameとtweet_countのリストを返します。
    :rtype: str
    """)
async def get_top_users_by_tweet() -> str:
    container = get_cosmos_container()
    # 必要な情報だけ取得
    query = "SELECT c.user.screen_name AS screen_name FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    # Pythonで集計
    from collections import Counter
    counts = Counter(item["screen_name"] for item in items if item.get("screen_name"))
    # ランキング形式で返す
    top10 = [{"screen_name": name, "tweet_count": count} for name, count in counts.most_common(10)]
    return to_json(top10)


# さらに必要に応じて CosmosDB のパーティションキーや特定フィールドで集計・分析系ツールも追加できます

@mcp.tool(description="""
    指定期間でツイートの多かった商品ランキング（上位10件）を取得します。

    :param start_date (str): 集計開始日（YYYY-MM-DD）
    :param end_date (str): 集計終了日（YYYY-MM-DD）
    :rtype: str

    :return: JSON形式でproduct_id, product_name, tweet_countのリストを返します。
    :rtype: str
    """)
async def get_top_products_by_tweets_period(
    start_date: str,
    end_date: str
) -> str:
    container = get_cosmos_container()
    # ISO8601 文字列（例："2025-07-01T00:00:00Z"）に変換
    start_iso = datetime.fromisoformat(start_date).strftime("%Y-%m-%dT00:00:00Z")
    end_iso = datetime.fromisoformat(end_date).strftime("%Y-%m-%dT23:59:59Z")
    # クエリ発行
    query = """
    SELECT c.product_id, c.product_name, c.created_at
    FROM c
    WHERE c.created_at >= @start AND c.created_at <= @end
    """
    items = list(container.query_items(
        query=query,
        parameters=[
            {"name": "@start", "value": start_iso},
            {"name": "@end", "value": end_iso}
        ],
        enable_cross_partition_query=True
    ))
    # 商品ごとに集計
    from collections import Counter
    key = lambda x: x.get("product_id") or x.get("product_name")
    counts = Counter(key(item) for item in items if key(item))
    # 上位10件
    top10 = []
    for pid, count in counts.most_common(10):
        product_name = next((item.get("product_name") for item in items if key(item) == pid), None)
        top10.append({
            "product_id": pid,
            "product_name": product_name,
            "tweet_count": count
        })
    return to_json(top10)

# --- サーバ起動 ---
if __name__ == "__main__":
    asyncio.run(mcp.run(transport="sse", host="0.0.0.0", port=8000))
