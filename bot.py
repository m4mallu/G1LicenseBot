from datetime import datetime
from pyrogram import Client
from config import Config

app = Client(
    "G1_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins={
                "root": "plugins"
            }
)

print("The bot has been started at {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
app.run()