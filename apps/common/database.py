import psycopg2
import os
from datetime import datetime, timedelta, timezone

POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgres://postgres.ojwsyjjtrjzfeageboot:WTgdKXKynwKEU9eM@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
)

conn = psycopg2.connect(POSTGRES_URL)
conn.autocommit = True  # 建議加上，避免需要手動 commit

def ensure_user_exists(user_id, display_name=None):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE line_user_id = %s", (user_id,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO users (line_user_id, display_name) VALUES (%s, %s)", (user_id, display_name))

def get_user_uuid(user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE line_user_id = %s", (user_id,))
        result = cur.fetchone()
        return result[0] if result else None
            
def insert_transactions(user_id, category, amount, message, display_name=None, record_type='expense'):
    ensure_user_exists(user_id, display_name)
    user_uuid = get_user_uuid(user_id)
    if user_uuid:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions (user_id, category, amount, message, type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_uuid, category, amount, message or category, record_type, datetime.now()))

            
def get_last_records(user_id, limit=5):
    user_uuid = get_user_uuid(user_id)  # 把 LINE user ID 轉成真正的資料庫 ID
    if not user_uuid:
        return []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT category, amount, created_at 
            FROM transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (user_uuid, limit))
        rows = cur.fetchall()
        return [
            {"category": row[0], "amount": row[1], "created_at": row[2]}
            for row in rows
        ]
        
def delete_record(user_id, index):
    user_uuid = get_user_uuid(user_id)
    if not user_uuid:
        return False

    with conn.cursor() as cur:
        # 先找出該使用者的第 index 筆最新紀錄
        cur.execute("""
            SELECT id FROM transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1 OFFSET %s
        """, (user_uuid, index - 1))  # index 從 1 開始

        result = cur.fetchone()
        if not result:
            return False  # 找不到紀錄

        expense_id = result[0]

        # 刪除該筆紀錄
        cur.execute("DELETE FROM transactions WHERE id = %s", (expense_id,))
        return True

def get_weekly_summary(user_id):
    user_uuid = get_user_uuid(user_id)
    if not user_uuid:
        return []

    # ➤ 明確指定為 UTC 時區，讓 datetime 是「aware」
    today = datetime.now(timezone.utc)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    print("start_of_week =", start_of_week)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT created_at
            FROM transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_uuid,))
        latest = cur.fetchone()
        if latest:
            latest_created_at = latest[0]
            print("latest_created_at =", latest_created_at)
            print("是否比 start_of_week 晚：", latest_created_at >= start_of_week)

        cur.execute("""
            SELECT type, SUM(amount)
            FROM transactions
            WHERE user_id = %s AND created_at >= %s
            GROUP BY type
        """, (user_uuid, start_of_week))
        rows = cur.fetchall()

        return {row[0]: row[1] for row in rows}