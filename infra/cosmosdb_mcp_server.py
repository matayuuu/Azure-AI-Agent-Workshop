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


def to_json(data):
    return json.dumps(data, ensure_ascii=False, default=str)


def get_cosmos_container():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB_NAME)
    return db.get_container_client(COSMOS_CONTAINER_NAME)


# --- CosmosDB Tools ---
@mcp.tool(description="""
    商品ごと、もしくは全体のレビューを集計します。

    :param product_id (int, Optional): 商品ID。指定しない場合は全商品が対象。
    :rtype: str

    :return: JSON形式でレビューの集計結果（product_id, review_count, avg_rating, pos_count, neg_countなど）。
    :rtype: str
    """)
async def get_review_summary(product_id: Optional[int] = None) -> str:
    container = get_cosmos_container()
    query = "SELECT c.product_id, c.rating, c.recommend, c.tags FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    # フィルタ
    if product_id is not None:
        items = [i for i in items if i.get("product_id") == product_id]
    if not items:
        return to_json({"review_count": 0, "avg_rating": None, "pos_count": 0, "neg_count": 0})
    review_count = len(items)
    avg_rating = sum(i["rating"] for i in items) / review_count
    pos_count = sum(1 for i in items if i["rating"] >= 4)
    neg_count = sum(1 for i in items if i["rating"] <= 2)
    return to_json({
        "product_id": product_id,
        "review_count": review_count,
        "avg_rating": round(avg_rating, 2),
        "pos_count": pos_count,
        "neg_count": neg_count,
    })

@mcp.tool(description="""
    レビュー評価が高い順に商品ランキング（上位10件）を取得します。

    :return: JSON形式で product_id, avg_rating, review_count のリストを返します。
    :rtype: str
    """)
async def get_top_products_by_review() -> str:
    container = get_cosmos_container()
    query = "SELECT c.product_id, c.rating FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    # 商品ごとに集計
    from collections import defaultdict
    d = defaultdict(list)
    for i in items:
        if i.get("product_id") is not None:
            d[i["product_id"]].append(i["rating"])
    result = []
    for pid, ratings in d.items():
        avg_rating = sum(ratings) / len(ratings)
        result.append({"product_id": pid, "avg_rating": round(avg_rating,2), "review_count": len(ratings)})
    # 上位10件
    top10 = sorted(result, key=lambda x: (-x["avg_rating"], -x["review_count"]))[:10]
    return to_json(top10)

@mcp.tool(description="""
    最近使われているタグやワードランキングを集計して返します。

    :param top_n (int, Optional): 上位いくつまで返すか。デフォルト10。
    :rtype: str

    :return: JSON形式で tag, count のリストを返します。
    :rtype: str
    """)
async def get_trending_tags(top_n: int = 10) -> str:
    container = get_cosmos_container()
    query = "SELECT c.tags FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    from collections import Counter
    all_tags = []
    for i in items:
        if i.get("tags"):
            all_tags.extend(i["tags"])
    counts = Counter(all_tags)
    return to_json([{"tag": tag, "count": count} for tag, count in counts.most_common(top_n)])

@mcp.tool(description="""
    商品ごとまたは日付ごとにポジティブ/ネガティブレビューの比率を返します。

    :param by (str, Optional): 'product' または 'date' で集計粒度を切り替え（デフォルト 'product'）。
    :rtype: str

    :return: JSON形式で粒度単位（product_id or date）ごとにポジ/ネガ比率リスト。
    :rtype: str
    """)
async def get_pos_neg_ratio(by: str = "product") -> str:
    container = get_cosmos_container()
    query = "SELECT c.product_id, c.review_date, c.rating FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    from collections import defaultdict
    res = defaultdict(lambda: {"pos": 0, "neg": 0, "total": 0})
    if by == "date":
        keyfunc = lambda x: x.get("review_date")
    else:
        keyfunc = lambda x: x.get("product_id")
    for i in items:
        key = keyfunc(i)
        if key is None: continue
        if i["rating"] >= 4:
            res[key]["pos"] += 1
        elif i["rating"] <= 2:
            res[key]["neg"] += 1
        res[key]["total"] += 1
    result = []
    for k, v in res.items():
        ratio = v["pos"] / v["total"] if v["total"] else 0
        result.append({
            "key": k,
            "pos_count": v["pos"],
            "neg_count": v["neg"],
            "total": v["total"],
            "pos_ratio": round(ratio, 2),
        })
    return to_json(result)

@mcp.tool(description="""
    指定期間でレビュー件数が急増・急減した商品を検出します。

    :param start_date (str): 集計開始日（YYYY-MM-DD）
    :param end_date (str): 集計終了日（YYYY-MM-DD）
    :param threshold (int, Optional): 急増・急減とみなす件数変動のしきい値。デフォルト5。
    :rtype: str

    :return: JSON形式で商品ごとに増減したレビュー数のリスト。
    :rtype: str
    """)
async def get_review_spike_products(start_date: str, end_date: str, threshold: int = 5) -> str:
    container = get_cosmos_container()
    # 全件取得して日付で2分割
    query = "SELECT c.product_id, c.review_date FROM c"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    from collections import defaultdict
    before = defaultdict(int)
    after = defaultdict(int)
    for i in items:
        d = i.get("review_date")
        if not d or not i.get("product_id"): continue
        if d < start_date:
            before[i["product_id"]] += 1
        elif d <= end_date:
            after[i["product_id"]] += 1
    results = []
    for pid in set(list(before.keys()) + list(after.keys())):
        diff = after[pid] - before[pid]
        if abs(diff) >= threshold:
            results.append({"product_id": pid, "diff": diff, "before": before[pid], "after": after[pid]})
    return to_json(results)


# --- サーバ起動 ---
if __name__ == "__main__":
    asyncio.run(mcp.run(transport="http", host="0.0.0.0", port=8000))
