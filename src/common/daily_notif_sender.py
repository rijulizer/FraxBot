import requests
from pprint import pprint
from pymongo import MongoClient
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
import yaml
# from database_connection import connect
from telethon.sync import TelegramClient#, events
import time
from mongodb_connection import mongodb_connect
import schedule
from querydb_actions import get_wallet_position

db, telegram_metadata, subscription, pairs, wallet = mongodb_connect()

config_stream = open("../common_config.yml",'r')
config = yaml.load(config_stream, Loader=yaml.BaseLoader)

API_ID = config['telegram']['api_id']
API_HASH = config['telegram']['api_hash']
BOT_TOKEN = config['telegram']['bot_token']
session_name = "sessions/Bot"
URL = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)



client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)


def send_notification():
    with client:
        # Send a message to your bot
        query = subscription.find()
        for q in query:
            print(q)
            user_id = int(q["user_id"])
            wallets = q["wallets"]
            for wallet_id in wallets:
                client.send_message(user_id, 'Daily notifications for your wallet(s) are here!')
                msg = get_wallet_position(wallet, wallet_id)
                client.send_message(user_id,msg)


# Schedule the notification to be sent every day at a specific time
# schedule.every(60*60).seconds.do(send_notification)

s = schedule.every().day.at("23:30:00", "America/New_York").do(send_notification)
print("\n",s.next_run)

# Start an infinite loop to run the scheduler
while True:
    schedule.run_pending()
    time.sleep(300)