# AI-Line-Bot 💬🤖

AI-Line-Bot 是一個結合 LINE Messaging API 與 PostgreSQL 的智慧型記帳機器人。使用者可透過對話輸入記帳訊息（例如：「早餐 60」），系統會自動解析、儲存並建立個人化記帳紀錄。

---

## 📦 專案結構

AI-Line-Bot/
│
├── app.py # Flask 應用主程式，處理 LINE webhook
├── requirements.txt # Python 套件依賴列表
├── .gitignore # Git 忽略清單
│
├── apps/
│ ├── common/
│ │ └── database.py # 連線 PostgreSQL，包含新增使用者與記帳功能
│ └── handlers/
│ └── message_handler.py # (預留) 未來處理訊息分類與 AI 回應
│
├── .vscode/ # 開發用 VSCode 設定（可忽略）
└── pycache/ # Python 快取檔（已排除 Git）

yaml
複製程式碼

---

## 🚀 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
建立 .env 環境變數（範例）
env
複製程式碼
POSTGRES_URL=postgres://<user>:<password>@<host>:<port>/<database>?sslmode=require
你可以將 POSTGRES_URL 改為你在 Supabase 上建立的資料庫連線字串。

🧠 功能說明
📥 使用者進入聊天室時自動記錄基本資料

🧾 輸入類似「午餐 100」即可自動寫入記帳系統

🧠 （開發中）加入 AI 模組，如「幫我看哪天花最多」等功能

🔐 使用 Supabase PostgreSQL 資料庫作為儲存後端

📚 資料表設計（簡略）
users：儲存 LINE 使用者資訊（line_user_id, display_name）

expenses：儲存記帳紀錄（category, amount, message, created_at）

🛠 開發中項目
 分類訊息處理邏輯（message_handler.py）

 加入 NLP 模組協助情境分析

 增加查詢與報表功能（如統計圖表、花費分析）

📤 部署建議
可部署於 Render、Fly.io、Railway 或 GCP VM

記得設定 POSTGRES_URL 與 LINE 的 access token / secret

若部署為 webhook，需使用 HTTPS 並註冊於 LINE Messaging API

🧑‍💻 作者
佳融 Wu — GitHub