import os
import json
import asyncio
import asyncpg
from typing import Optional
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
    全ユーザー一覧を取得します。

    :return: JSON形式でユーザーの一覧を返します。
    :rtype: str
    """)
async def get_all_users() -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch("SELECT * FROM users")
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    指定カテゴリIDで絞り込んだ商品の一覧を取得します。

    :param category_id (int): 商品カテゴリID（必須）
    :rtype: str

    :return: JSON形式で商品の一覧を返します。
    :rtype: str
    """)
async def get_products_by_category(category_id: int) -> str:
    conn = await get_conn()
    try:
        rows = await conn.fetch(
            "SELECT * FROM products WHERE category_id = $1", category_id
        )
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
    指定した期間（開始日～終了日）でカテゴリ別の売上集計（上位10件）を取得します。

    :param start_date (str): 集計開始日（YYYY-MM-DD）
    :param end_date (str): 集計終了日（YYYY-MM-DD）
    :rtype: str

    :return: JSON形式でカテゴリID,カテゴリ名,売上金額のリストを返します。
    :rtype: str
    """)
async def get_sales_by_category(
    start_date: str,
    end_date: str
) -> str:
    conn = await get_conn()
    try:
        sql = """
            SELECT
                c.category_id,
                c.category_name,
                SUM(od.price * od.quantity) AS total_sales
            FROM order_details od
            JOIN products p ON od.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE TO_DATE(o.order_date, 'YYYY-MM-DD') >= TO_DATE($1, 'YYYY-MM-DD')
              AND TO_DATE(o.order_date, 'YYYY-MM-DD') <= TO_DATE($2, 'YYYY-MM-DD')
            GROUP BY c.category_id, c.category_name
            ORDER BY total_sales DESC
            LIMIT 10
        """
        rows = await conn.fetch(sql, start_date, end_date)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

@mcp.tool(description="""
    指定した期間（開始日～終了日）で商品別の売上集計（上位10件）を取得します。

    :param start_date (str): 集計開始日（YYYY-MM-DD）
    :param end_date (str): 集計終了日（YYYY-MM-DD）
    :rtype: str

    :return: JSON形式でproduct_id, product_name, total_salesのリストを返します。
    :rtype: str
    """)
async def get_sales_by_product(
    start_date: str,
    end_date: str
) -> str:
    conn = await get_conn()
    try:
        sql = """
            SELECT
                p.product_id,
                p.product_name,
                SUM(od.price * od.quantity) AS total_sales
            FROM order_details od
            JOIN products p ON od.product_id = p.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE TO_DATE(o.order_date, 'YYYY-MM-DD') >= TO_DATE($1, 'YYYY-MM-DD')
              AND TO_DATE(o.order_date, 'YYYY-MM-DD') <= TO_DATE($2, 'YYYY-MM-DD')
            GROUP BY p.product_id, p.product_name
            ORDER BY total_sales DESC
            LIMIT 10
        """
        rows = await conn.fetch(sql, start_date, end_date)
        return to_json([dict(r) for r in rows])
    finally:
        await conn.close()

# --- サーバ起動 ---
if __name__ == "__main__":
    asyncio.run(mcp.run(transport="http", host="0.0.0.0", port=8000))
