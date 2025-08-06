import psycopg2
import os

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

def insert_expense(user_id, category, amount, message):
    user_uuid = get_user_uuid(user_id)
    if user_uuid:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses (user_id, category, amount, message, created_at) VALUES (%s, %s, %s, %s, %s)",
                (user_uuid, category, amount, message, datetime.utcnow())
            )