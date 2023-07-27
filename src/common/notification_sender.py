import requests
from pprint import pprint
from pymongo import MongoClient
from time import sleep
# from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
import yaml
# from data.database_connection import connect
from telethon.sync import TelegramClient#, events
import time
import schedule
import os
from datetime import datetime

from common import get_wallet_position, mongodb_connect

print("Inside notification_sender.py...")

# python_path = r"D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src"
python_path = os.environ.get('PYTHONPATH')
(db, pairs, user_positions, user_notifications, telegram_metadata, subscription) = mongodb_connect()
print(python_path+os.sep+"common_config.yml")
config_stream = open(python_path+os.sep+"common_config.yml",'r')
# config_stream = open("../common_config.yml",'r')
config = yaml.load(config_stream, Loader=yaml.BaseLoader)

API_ID = config['telegram']['api_id']
API_HASH = config['telegram']['api_hash']
BOT_TOKEN = config['telegram']['bot_token']
session_name = "sessions/Bot"
URL = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)

if not os.path.exists(os.getcwd()+os.sep+"sessions"):
    os.mkdir(os.getcwd()+os.sep+"sessions")
    # with open(os.getcwd()+os.sep+"sessions"+os.sep+'Bot.session', 'w') as fp:
    #     pass

client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)


def send_notification():
    print("Inside send_notification() ...")
    with client :
        # Send a message to your bot
        query = subscription.find()
        # iterate over wallet_ids
        print("Sending Notifications...")
        for users in query:
            user_id = int(users["user_id"])
            wallets = users["wallets"]
            client.send_message(user_id, 'Daily notifications for your wallet(s) are here!')   
            for wallet_id in wallets:
                # try:
                # get the listy of messages to display
                msg_user_notif = get_wallet_position(user_notifications, wallet_id,"notification")
                for msg in msg_user_notif:
                    client.send_message(user_id, msg,parse_mode='html')
    return

if __name__ == '__main__':

    (db, pairs, user_positions, user_notifications, telegram_metadata, subscription) = mongodb_connect()
    send_notification()