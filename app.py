import re
import apps.common.database as db
from linebot.v3.messaging.models import TextMessage
from flask import Flask, request, abort
import apps.handlers.call_openai_chatgpt as ai  # 如果在其他檔案


from linebot.v3 import (
    WebhookHandler
)

from linebot.v3.exceptions import (
    InvalidSignatureError
)

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    BroadcastRequest,
    MulticastRequest,
    TextMessage,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    URIAction,
    MessageAction,
    DatetimePickerAction,
    ConfirmTemplate,
    ButtonsTemplate,
    CarouselTemplate,
    CarouselColumn,
    ImageCarouselColumn,
    ImageCarouselTemplate,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
    CameraAction,
    CameraRollAction,
    LocationAction
)

from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    PostbackEvent,
    TextMessageContent,
)


app = Flask(__name__)

configuration = Configuration(access_token='o1dZ2R+gv4EkUiLP+7Lv5+xIr0MnLJ/tdMg/IescjfCrofovaEYQUvkoMDvDskKSZfvNH//UAHI0WoJZwsV/CcNGJSVUUlpkYbKXIZeNWSpt1rl4mWMuhz+7YjTfMWBOipJLAhSO9vUGrtpsMYiTkgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f69252e18675847b29e034ee84645423')


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Webhook handling error: {e}")
        abort(400)

    return 'OK'

# 加入好友事件
@handler.add(FollowEvent)
def handle_follow(event):
    # 取得使用者的 LINE ID
    user_id = event.source.user_id

    # 取得使用者暱稱
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        profile = line_bot_api.get_profile(user_id)

        display_name = profile.display_name

    # 存進資料庫
    db.ensure_user_exists(user_id, display_name)

    print(f'User joined: {display_name} ({user_id})')


# 訊息事件
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        text = event.message.text.strip()
        user_id = event.source.user_id
        
        if event.message.text == 'postback':
            buttons_template = ButtonsTemplate(
                title='Postback Sample',
                text='Postback Action',
                actions=[
                    PostbackAction(label='Postback Action', text='Postback Action Button Clicked!', data='postback'),
                ]
            )
            template_message = TemplateMessage(
                alt_text='Postback Sample',
                template=buttons_template
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
        if event.message.text == '記帳':
            confirm_template = ConfirmTemplate(
                text='請問這筆是支出還是收入？',
                actions=[
                    MessageAction(label='支出', text='支出'),
                    MessageAction(label='收入', text='收入')
                ]
            )

            template_message = TemplateMessage(
                alt_text='請選擇支出或收入',
                template=confirm_template
            )

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
            
        elif event.message.text == '查帳':
            records = db.get_last_records(user_id)  # 取得最近 5 筆
            
            if not records:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text='目前沒有任何記帳紀錄。')]
                    )
                )
                return
            actions = [
                PostbackAction(label=f'刪除第{i+1}筆', data=f'delete_{i+1}')
                for i in range(len(records))
            ]
            buttons_template = ButtonsTemplate(
                title='最近記帳紀錄',
                text='\n'.join([f'{i+1}. {r["category"]} {r["amount"]}' for i, r in enumerate(records)]),
                actions=actions[:4]  # 最多 4 個按鈕
            )
            template_message = TemplateMessage(alt_text='查帳紀錄', template=buttons_template)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
        elif event.message.text == '本週總結':
            summary = db.get_weekly_summary(user_id)
            income = summary.get('income', 0)
            expense = summary.get('expense', 0)
            balance = income - expense

            msg = (
                f'📊 本週總結\n'
                f'收入：{income} 元\n'
                f'支出：{expense} 元\n'
                f'結餘：{balance} 元'
            )

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text=msg,
                            quick_reply=get_main_quick_reply()  # ✅ 附上主選單
                        )
                    ]
                )
            )
        
        # 4. 處理「早餐 60」這類直接輸入的記帳內容
        else:
            match = re.match(r'^(.+?)\s+(\d+)$', text)
            if match:
                category = match.group(1)
                amount = int(match.group(2))
                db.insert_expense(user_id=user_id, category=category, amount=amount, message=text)

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=f'已記錄：{category} {amount} 元')]
                    )
                )
            # 4. 處理 AI 問答
            elif is_ai_question(text):  # 先判斷是否為 AI 問句
                response = handle_ai_question(user_id, text)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=response, quick_reply=get_main_quick_reply())]
                    )
                )

    #handle_text_message(event, configuration)
    
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if data == 'postback':
            print('Postback event is triggered')
        elif data.startswith('delete_'):
            index = int(data.split('_')[1])
            db.delete_record(user_id, index)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f'已刪除第 {index} 筆紀錄')]
                )
            )
            
def get_main_quick_reply():
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(label='記帳', text='記帳')),
            QuickReplyItem(action=MessageAction(label='查帳', text='查帳')),
            QuickReplyItem(action=MessageAction(label='本週總結', text='本週總結')),
        ]
    )
    
def handle_ai_question(user_id, user_question):
    # 從資料庫取得最近一週的記帳資料
    transactions = db.get_user_transactions(user_id, days=7)

    if not transactions:
        return "這週還沒有任何記帳資料喔～"

    # 轉成 prompt 給 OpenAI
    context = "\n".join([f"{t['category']}: {t['amount']} 元" for t in transactions])
    
    prompt = (
        f"以下是使用者最近 7 天的支出紀錄：\n{context}\n"
        f"使用者問：「{user_question}」\n"
        "請根據上述紀錄，用一段簡短清楚的話回答問題。"
    )

    return ai.call_openai_chatgpt(prompt)

def is_ai_question(text):
    keywords = ['花最多', '平均', '省錢', '建議', '多少', '幫我看']
    return any(kw in text for kw in keywords)

    
if __name__ == "__main__":
    app.run()