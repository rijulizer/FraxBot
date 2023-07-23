from datetime import datetime
import pymongo
from pymongo import MongoClient
import yaml
import os
import numpy as np
import pandas as pd

def get_subscribed_wallets(collection_db, user_id: str):
    """
    Get the wallets subscribed by an user_id
    """
    sub_dict = collection_db.find_one({"user_id": user_id})
    if sub_dict:
        wallets = sub_dict['wallets']
        if not isinstance(wallets, list):
            wallets = [wallets]

    else:
        wallets = []
    return wallets

def add_wallets_for_subscription(collection_db, user_id: str, new_wallets: list):

    #update subscription
    collection_db.insert_one(
        {
        "user_id": user_id,
        "wallets": new_wallets
        }
        )
    return None

def update_wallets_for_subscription(collection_db, user_id: str, new_wallets: list):

    #update subscription
    collection_db.update_one(
        {"user_id": user_id},
        {"$set":{"wallets": new_wallets}}
        )
    return None
    
def format_date(messageTime):
    
    messageTime = datetime.fromtimestamp(messageTime) # datetime format
    messageTime = messageTime.strftime('%Y-%m-%d %H:%M:%S') # formatted datetime    
    TimeStamp = str(messageTime)
    return (TimeStamp)

def format_telegram_metadata(result):
    (
        message_id,
        user_id, 
        update_id, 
        is_bot, 
        first_name, 
        last_name, 
        username, 
        date, 
        user_account_type, 
        message, 
        language
     ) = (
            None,
            None, 
            None, 
            None, 
            None, 
            None, 
            None, 
            None, 
            None, 
            None, 
            None
     )
    flag_data_none = False
    if result:
        flag_data_none = True
        if 'update_id' in result.keys():
            update_id = result['update_id']
        if 'message' in result.keys():
            if 'message_id' in result['message'].keys():
                message_id = result['message']['message_id']
            if 'from' in result['message'].keys():
                if 'id' in result['message']['from'].keys():
                    user_id = str(result['message']['from']['id'])
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
    return(flag_data_none,
        {
            "message_id" : message_id,
            "user_id" : str(user_id), 
            "update_id" : update_id, 
            "is_bot" : is_bot, 
            "first_name" : first_name, 
            "last_name" : last_name, 
            "username": username, 
            "date": date, 
            "user_account_type": user_account_type, 
            "message": message, 
            "language": language
            }
        )
    
def upload_channel_metadata(collection_db, metadata):
    collection_db.insert_one(metadata)
    print("[MongoDB] Metadata uploaded...")
    return

def check_returning_user(collection_db, user_id: str):
    """
    Get the wallets subscribed by an user_id
    """
    returning_user = False
    sub_dict = collection_db.find_one({"user_id": user_id})
    if sub_dict:
        returning_user = True

    return returning_user

def get_wallet_position(collection_db, wallet_id: str):

    print("Trying to fetch wallet position...")
    # get information for each wallet id
    res = collection_db.find_one({'wallet_id': wallet_id})
    if res:
        str_position_values = []
        if res['positions']:
            # position_values = """"""
            str_position_values.append(f"This wallet- {wallet_id} has {len(res['positions'])} valid position(s) - ")
            for pos in res['positions']:
                str_position_values.append(f'''\n
Pair Id:  {pos["pair_id"]},
Pair Symbol:  {pos["pair_symbol"]},
Exchange Rate:  {pos["pair_ex_rate"]} FRAX,
Borrow APR:  {pos["pair_borrow_APR"]} %,
Lend APR:  {pos["pair_lend_APR"]} %,
Borrwed Amount:  {pos["user_borrow_amt_scaled"]} FRAX,
Deposited Collateral:  {pos["user_dep_col_amt_scaled"]} {pos["collateral_symbol"]},
Lent Amount:  {pos["user_lent_amt_scaled"]} FRAX,
Current LTV:  {pos["user_current_LTV"]} %,
Liquidation Price:  {pos["user_liquidation_price_scaled"]} FRAX,
Last Updated on: {pos["pos_datetime"]}
    ''')
        else:
            str_position_values.append(f"This wallet - {wallet_id} has no valid positions.\n")

        str_hyper_links = f"""\nFor more information, visit-
etherscan - {res['hlink_etherscanner']}
facts-frax-finance - {res['hlink_fraxfacts']}
"""
        str_position_values.append(str_hyper_links)


    else:
        str_position_values = None
    return str_position_values

