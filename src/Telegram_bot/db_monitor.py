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
import asyncio
import time
from pymongo import MongoClient
from bson.objectid import ObjectId
# import script_mongodb

# print("Initializing configurations...")
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

API_ID = config.get('default','api_id') 
API_HASH = config.get('default','api_hash')
BOT_TOKEN = config.get('default','bot_token')
session_name = "sessions/Bot"
URL = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)

# client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)
connection_string = "mongodb+srv://meghachakravorty:jgOokbXraHxWjHHx@cluster0.h1o4nlj.mongodb.net/"

db_client = MongoClient(connection_string, connect=False)

# Access database
db = db_client['frax']

def create_message_select_query(ans):
    print('\n\nCreating reply to Select query...')
    # ans['_id']=str(ans['_id'])
    # print(ans)

    df = pd.DataFrame(columns=['column','value'])
    df['column'] = list(ans.keys())
    df['value'] = list(ans.values())

    print('='*50)
    # df = pd.DataFrame(ans)

    df = df[df['column']!='_id']
    print(df.to_string())

    # df.drop(['_id'], axis=1,inplace=True)

    # df = df.T

    # message = "<b>Received 📖 Information about orders:</b>\n\n"

    message=df.to_string(index=False, header=False,col_space=15, na_rep="Unknown",justify="right")

    print(message)

    return message

def change_stream(change):
    print("Inside change stream function...")
    operation = change['operationType']
    if change['operationType']=='insert':
        return (operation,None,None)
        # wallet_id_sub,change_string = change_stream_insert(change)
    elif change['operationType']=='update':
        wallet_id_sub,change_string = change_stream_update(change)
    elif change['operationType']=='replace':
        wallet_id_sub,change_string = change_stream_replace(change)
    elif change['operationType']=='delete':
        wallet_id_sub,change_string = change_stream_delete(change)
    return (operation,wallet_id_sub,change_string)

def change_stream_insert(change):
    print('Change stream insert identified')
    val = change['fullDocument']
    wallet_id_sub = val['wallet_address']
    change_string = f"New data has been added to your subscribed wallet {wallet_id_sub}\n <b>Inserted 📖 Information:</b>\n\n"+create_message_select_query(val)
    return (wallet_id_sub,change_string)

def change_stream_replace(change): 
    print('Change stream replace identified')
    val = change['fullDocument']
    wallet_id_sub = val['wallet_address']
    change_string = f"Your subscribed wallet {wallet_id_sub} has been updated\n <b>Updated 📖 Information:</b>\n\n"+create_message_select_query(val)
    return (wallet_id_sub,change_string)

def change_stream_update(change): 
    print('Change stream update identified')
    doc_id = change["documentKey"]["_id"]
    wallet_id_sub, change_string = get_updated_wallet_details(doc_id)
    change_string = f"Your subscribed wallet {wallet_id_sub} has been updated\n <b>Updated 📖 Information:</b>\n\n" + change_string
    return (wallet_id_sub,change_string)

def get_updated_wallet_details(doc_id):
    print('\n\nFetching updated wallet details...\n')
    print(f'\nDoc id: {doc_id}')
    lst = list(db.wallets.find({'_id': ObjectId(doc_id)}))
    print(lst)
    # lst = [l['wallet_id'] for l in lst]
    # print(f'Wallet ids that may have been deleted: {list(set(lst))[0]}')
    wallet_id_sub = lst[-1]["wallet_address"]
    msg = create_message_select_query(lst[-1])
    return(wallet_id_sub,msg)

def change_stream_delete(change):
    print('Change stream delete identified')
    doc_id = change["documentKey"]["_id"]
    print(f'\nDocumentKey: {doc_id}')
    wallet_id_sub = get_deleted_wallet_id(str(doc_id))
    change_string = f"Your subscribed wallet {wallet_id_sub} has been deleted"
    return (wallet_id_sub,change_string) 

def get_deleted_wallet_id(doc_id):
    print(f'\nDoc id: {doc_id}')
    lst = list(db.subscription.find({'doc_id': doc_id}))
    print(lst)
    lst = [l['wallet_id'] for l in lst]
    print(f'Wallet ids that may have been deleted: {list(set(lst))[0]}')
    if len(list(set(lst)))==1:
        return(list(set(lst))[0])
    else:
        print('Could not determine deleted wallet id')
        return(None)

def notify_subscribers(wallet_id):
    print(f"\n\nFetching list of subscribers for wallet {wallet_id}...\n\n")
    # sql_command = f"Select user_id From Subscription Where wallet_id=(?);"
    # crsr.execute(sql_command, [wallet_id])
    # fetched = crsr.fetchall()
    fetched = []
    for i in db.subscription.find({'wallet_id': wallet_id}):
        # print(i)
        fetched.append([i["wallet_id"], i["user_id"],i["doc_id"]])
    # fetched = [list(x)[1:] for x in db.subscription.find({'wallet_address': wallet_id})]
    # fetched = [d.values() for d in fetched]

    print(f"\n\tFetched subscriber list: {fetched}")

    # fetched = [(sid[0],wallet_id) for sid in list(set(fetched))]
    # for sid in list(set(fetched)):
    #     print(type(sid))
    #     print(sid[0])
        # notification(sid[0],wallet_id)
    # print(fetched)
    return fetched

def main():
    # try:        
        with db.wallets.watch() as stream:
            print('change stream established...')
            # time.sleep(60)
            while stream.alive:
                change = stream.try_next()

                if change is not None:
                    print("Change document: %r" % (change,))
                    operation,wallet_id_sub,change_string = change_stream(change)
                    if operation in ['delete','update','replace']:
                        notif_lst = notify_subscribers(wallet_id_sub)

                        for notif in notif_lst:
                            print(f"\nNeed to notify:\n{notif}")
                            # print(notif[0],type(notif[1]),)
                            if operation=='delete':
                                db.subscription.delete_many({'wallet_id':notif[0],'user_id':notif[1],'doc_id':notif[2]})
                                change_string += "\nYour subscription to the wallet has ended!\n"
                            # send_notification(int(notif[1]),change_string)
                        # client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)
                        with TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN) as client:
                            client.loop.run_until_complete(send_notification(client, int(notif[1]),change_string))
                            # client.send_message(notif[0], change_string+"\nYour subscription to the wallet has ended!\n", parse_mode='html')
                            # client.send_message(SENDER, text, parse_mode='html')
                

                time.sleep(10)
                continue
        return

async def send_notification(client, sender,msg):
    print("Trying to send notification...")
    # def notify_update():
    

    await client.send_message(sender, msg, parse_mode='html')

    client.disconnect()
    # return


if __name__ == "__main__":
    # The context manager will release the resource
    # (i.e. call client.disconnect) for us when the
    # block exits.
    main()
    # with client:
        # client.loop.run_until_complete(send_notification())

# async def run():
#     await main()

# asyncio.run(run())