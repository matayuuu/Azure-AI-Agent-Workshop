import sys
import glob
import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey

def main(endpoint, key, db_name, container_name, jsonl_dir):
    client = CosmosClient(endpoint, key)
    db = client.create_database_if_not_exists(db_name)
    container = db.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/tweet_id"),
        offer_throughput=400
    )

    # --- 1. 既存全データ削除（全件削除） ---
    # --- 1. 既存全データ削除（全件削除） ---
    print("Deleting all existing documents in container for truncate-insert...")
    deleted = 0
    skipped = 0
    for item in container.read_all_items():
        pk = item.get("tweet_id")
        if pk is not None:
            container.delete_item(item, partition_key=pk)
            deleted += 1
        else:
            print(f"Skipped (no partition key): {item.get('id')}")
            skipped += 1
    print(f"All documents deleted: {deleted}, skipped: {skipped}")

    # --- 2. 新規投入 ---
    for jsonl_file in glob.glob(f"{jsonl_dir}/*.jsonl"):
        inserted = 0
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                # id必須
                if "id" not in doc:
                    doc["id"] = str(doc.get("tweet_id", str(uuid.uuid4())))
                else:
                    doc["id"] = str(doc["id"])
                # パーティションキーはstr
                if "tweet_id" in doc:
                    doc["tweet_id"] = str(doc["tweet_id"])
                container.upsert_item(doc)
                inserted += 1
        print(f"Inserted {inserted} docs from {jsonl_file}")

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python import_jsonl_to_cosmos.py <COSMOS_ENDPOINT> <COSMOS_KEY> <DB_NAME> <CONTAINER_NAME> <JSONL_DIR>")
        sys.exit(1)
    main(*sys.argv[1:])
