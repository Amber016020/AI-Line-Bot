from linebot.v3.messaging import (
    ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.messaging.models import GetProfileResponse
from db.database import ensure_user_exists, insert_expense
from utils.parser import parse_expense_message


def handle_text_message(event, configuration):
    user_id = event.source.user_id
    message = event.message.text.strip()

    # 取得使用者名稱（失敗時設為 None）
    try:
        with ApiClient(configuration) as api_client:
            profile: GetProfileResponse = MessagingApi(api_client).get_profile(user_id)
            display_name = profile.display_name
    except:
        display_name = None

    ensure_user_exists(user_id, display_name)

    # 嘗試解析「記帳指令」
    parsed = parse_expense_message(message)
    if parsed:
        category, amount = parsed
        insert_expense(user_id, category, amount, message)
        reply_text = f"已記錄：{category} {amount} 元 ✅"
    else:
        reply_text = f"你傳的是：{message}"

    # 回覆使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
