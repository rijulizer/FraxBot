# Importing the libraries
import configparser
from telethon import TelegramClient, events
import sqlite3
from datetime import datetime
import json 
import requests
import time
import urllib
from telebot import types
import pandas as pd
from tabulate import tabulate
from prettytable import PrettyTable
from bson.objectid import ObjectId

print("Initializing configurations...")
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

API_ID = config.get('default','api_id') 
API_HASH = config.get('default','api_hash')
BOT_TOKEN = config.get('default','bot_token')
session_name = "sessions/Bot"
URL = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)

# def notify_update():
from pymongo import MongoClient


def notify_subscribers(wallet_id):
    print("\n\nFetching list of subscribers for wallet {wallet_id}...\n\n")

    fetched = list(db.subscription.find({'wallet_address': wallet_id}))
    fetched = [d.values() for d in fetched]

    print(f"\n\tFetched subscriber list: {fetched}")

    return fetched

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def format_date(messageTime):
    messageTime = datetime.fromtimestamp(messageTime) # datetime format
    messageTime = messageTime.strftime('%Y-%m-%d %H:%M:%S') # formatted datetime    
    TimeStamp = str(messageTime)
    return (TimeStamp)

def format_updates(result):
    message_id, user_id, update_id, is_bot, first_name, last_name, username, date, user_account_type, message, language = None, None, None, None, None, None, None, None, None, None, None
    if 'update_id' in result.keys():
        update_id = result['update_id']
    if 'message' in result.keys():
        if 'message_id' in result['message'].keys():
            message_id = result['message']['message_id']
        if 'from' in result['message'].keys():
            if 'id' in result['message']['from'].keys():
                user_id = result['message']['from']['id']
            if 'is_bot' in result['message']['from'].keys():
                is_bot = result['message']['from']['is_bot']
            if 'first_name' in result['message']['from'].keys():
                first_name = result['message']['from']['first_name']
            if 'last_name' in result['message']['from'].keys():
                last_name = result['message']['from']['last_name']
            if 'username' in result['message']['from'].keys():
                username = result['message']['from']['username']
            if 'language_code' in result['message']['from'].keys():
                language = result['message']['from']['language_code']
        if 'date' in result['message'].keys():
            date = format_date(int(result['message']['date']))
        if 'chat' in result['message'].keys():
            user_account_type = result['message']['chat']['type']
        if 'text' in result['message'].keys():
            message = result['message']['text']
    return ((message_id, user_id, update_id, is_bot, first_name, last_name, username, date, user_account_type, message, language))
    
def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates():
    url = URL + "getUpdates"
    js = get_json_from_url(url)
    values = format_updates(js['result'][-1])
    return values

def update_metadata(wallet_id=None):
    print('\n\nCalling update function...\n\n')
    values = get_updates()
    print(f'\n\nVALUES: {values}\nLength of values: {len(values)}')
    days = 0
    freq = 0

    record =   {"message_id" : values[0],
            "user_id": values[1],
            "update_id": values[2], 
            "is_bot": values[3], 
            "first_name": values[4], 
            "last_name": values[5], 
            "username": values[6], 
            "date": values[7],
            "user_account_type": values[8], 
            "message": values[9], 
            "language": values[10],
            "queried_wallet": wallet_id,
            "frequency": 0
            }

    user_id = values[1]

    print(f'User id to be queried: {user_id}, {type(user_id)}')

    query = list(db.metadata.find({'queried_wallet': wallet_id}))

    print(f'\n\nQUERY: {query}')
    if len(query)>0:
        query_date = query[-1]["date"]
        freq = query[-1]["frequency"]
        print(f"Time of last query to this wallet: {query_date}")
        current_time = datetime.now()
        messageTime = current_time.strftime('%Y-%m-%d %H:%M:%S') 
        messageTime = datetime.strptime(messageTime, '%Y-%m-%d %H:%M:%S') 
        query_date = datetime.strptime(query_date, '%Y-%m-%d %H:%M:%S') 
        print(type(query_date),type(messageTime))

        days =  (messageTime - query_date).days

        print(f'Date difference = {days}, Frequency = {freq}')     

    
    if days!=None and days>=0 and days<=2:
        if values[9].count('/start')==0:
            if freq==None:
                freq = 1
            else:
                freq += 1
            print(f'Updated Frequency = {freq}')
        
        record['frequency'] = freq
        
    db.metadata.insert_one(record)

    return ((freq==3, user_id))
    
def subscription(wallet_id,user_id,doc_id):
    "\nCalling Subscription ..."

    res = list(db.subscription.find({'wallet_id': wallet_id, 'user_id':user_id, 'doc_id':doc_id}))
    if len(res)==0:
        record = {
            "wallet_id":wallet_id,
            "user_id":user_id,
            "doc_id":doc_id
        }
        db.subscription.insert_one(record)
        status = True
    else:
        status = False
    return (status)

# Start the bot session
client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    sender = await event.get_sender()
    SENDER = sender.id
    print(SENDER)

    text = '''Hello, I'm here to help you monitor the FRAX database!\n\n 
    To <b>View</b> the last entry for a wallet id, use format \n<i>/select {wallet_id}\n\n
    To <b>subscribe</b> to a specific wallet, use format\n<i>/subscribe {wallet_id}\n\n
    To <b>unsubscribe</b> to a specific wallet, use format\n<i>/unsubscribe {wallet_id}\n\n
    '''

    update_metadata()
    await client.send_message(SENDER, text, parse_mode='html')
    # with client:
    #     client.loop.run_until_complete(send_notification(SENDER,text))
    
    return

@client.on(events.NewMessage(pattern="(?i)/subscribe"))
async def subscribe(event):
    sender = await event.get_sender()
    SENDER = sender.id
    print(SENDER)
    try:
        list_of_words = event.message.text.split(" ")

        if len(list_of_words)==2:
            wallet_id = list_of_words[1]

            res = list(db.wallets.find({'wallet_address': wallet_id}))
            if len(res)==0:
                
                text = f"Could not find a wallet with id {wallet_id} to subscribe!"
                await client.send_message(SENDER, text, parse_mode='html')
                # with client:
                #     client.loop.run_until_complete(send_notification(SENDER,text))
            else:
                doc_id = str(res[-1]['_id'])

                record = {"wallet_id":wallet_id,"user_id":SENDER,"doc_id":doc_id} 
                db.subscription.insert_one(record)

                update_metadata()

               
                text = f"You have <b>successfully subscribed</b> to wallet {wallet_id}"
                await client.send_message(SENDER, text, parse_mode='html')
                # with client:
                #     client.loop.run_until_complete(send_notification(SENDER,text))
        else:
            
            text = "Please mention the wallet id to which you want to subscribe!"
            await client.send_message(SENDER, text, parse_mode='html')
            # with client:
            #     client.loop.run_until_complete(send_notification(SENDER,text))
    except Exception as e:
        print("\n",e,"\n")
        text = u"<b>Conversation Terminated \U0001F480</b>"
        await client.send_message(SENDER, text, parse_mode='html')        
        # with client:
        #     client.loop.run_until_complete(send_notification(SENDER,text))
    return

@client.on(events.NewMessage(pattern="(?i)/unsubscribe"))
async def unsubscribe(event):
    sender = await event.get_sender()
    SENDER = sender.id
    print(SENDER)
    try:
        list_of_words = event.message.text.split(" ")

        if len(list_of_words)==2:
            wallet_id = list_of_words[1]

            res = list(db.subscription.find({'wallet_id': wallet_id,'user_id':SENDER}))
            if len(res)==0:
                
                text = f"You are not subscribed to wallet {wallet_id}!"
                await client.send_message(SENDER, text, parse_mode='html')
                # with client:
                #     client.loop.run_until_complete(send_notification(SENDER,text))
            else:
                db.subscription.delete_many({'wallet_id':wallet_id,'user_id':SENDER})

                update_metadata()

                text = f"You have <b>successfully unsubscribed</b> to wallet {wallet_id}"
                await client.send_message(SENDER, text, parse_mode='html')
                # with client:
                #     client.loop.run_until_complete(send_notification(SENDER,text))
        else:
            text = "Please mention the wallet id to which you want to unsubscribe!"
            await client.send_message(SENDER, text, parse_mode='html')
            # with client:
            #     client.loop.run_until_complete(send_notification(SENDER,text))
    except Exception as e:
        print("\n",e,"\n")
        text = u"<b>Conversation Terminated \U0001F480</b>"
        await client.send_message(SENDER, text, parse_mode='html')
        # with client:
        #     client.loop.run_until_complete(send_notification(SENDER,text))
    return

def create_message_select_query(ans):
    print('\n\nCreating reply to Select query...')

    df = pd.DataFrame(columns=['column','value'])
    df['column'] = list(ans.keys())
    df['value'] = list(ans.values())

    print('='*50)

    df = df[df['column']!='_id']
    print(df.to_string())


    message=df.to_string(index=False, header=False,col_space=15, na_rep="Unknown",justify="right")

    print(message)

    return message



@client.on(events.NewMessage(pattern="(?i)/select"))
async def select(event):
    # try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id

        list_of_words = event.message.text.split(" ")
        wallet_id = list_of_words[1]

        print(f'Wallet_id passed during Select: {wallet_id}') 

        res = list(db.wallets.find({'wallet_address': wallet_id}))

        print(f'\n\nResult: {res}\n\n')

        doc_id = str(res[-1]['_id'])

        print(f'Document id: {doc_id}')

        if(res):
            print('Select query returned values')
            text = "<b>Received 📖 Information about orders:</b>\n\n"+create_message_select_query(res[-1]) 
            await client.send_message(SENDER, text, parse_mode='html')
            # with client:
            #     client.loop.run_until_complete(send_notification(SENDER,text))

        else:
            text = "No orders found inside the database."
            await client.send_message(SENDER, text, parse_mode='html')
            # with client:
            #     client.loop.run_until_complete(send_notification(SENDER,text))
        
        print('\n\nUpdate Metadata...')
        subscription_flag, user_id = update_metadata(wallet_id)
        print(f'SUBSCRIPTION FLAG = {subscription_flag}')
        if subscription_flag:
            subscription_status = subscription(wallet_id, user_id, doc_id)
            if subscription_status:
                text = u"\n\nI am so happy to see your interest in my work! \U0001f600 I am putting you down for FREE SUBSCRIPTION!\n To end this subscription, please enter /unsubscribe {wallet id}"
                await client.send_message(SENDER, text, parse_mode='html')
                # with client:
                #     client.loop.run_until_complete(send_notification(SENDER,text))
                
        return

# async def send_notification(sender,msg):
#     print("Trying to send notification...")    

#     await client.send_message(sender, msg, parse_mode='html')

    # client.disconnect()

if __name__ == '__main__':
    try:
        connection_string = "mongodb+srv://meghachakravorty:jgOokbXraHxWjHHx@cluster0.h1o4nlj.mongodb.net/"

        db_client = MongoClient(connection_string, connect=False)

        db = db_client['frax']

        client.run_until_disconnected()

    except Exception as error:
        print('Cause: {}'.format(error))


