from flask import Flask, request, abort

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
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

app = Flask(__name__)

configuration = Configuration(access_token='o1dZ2R+gv4EkUiLP+7Lv5+xIr0MnLJ/tdMg/IescjfCrofovaEYQUvkoMDvDskKSZfvNH//UAHI0WoJZwsV/CcNGJSVUUlpkYbKXIZeNWSpt1rl4mWMuhz+7YjTfMWBOipJLAhSO9vUGrtpsMYiTkgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f69252e18675847b29e034ee84645423')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    handle_text_message(event, configuration)

if __name__ == "__main__":
    app.run()