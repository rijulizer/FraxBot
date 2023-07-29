import sys
# sys.path.append('d:\\FRAX_project\\FraxBot\\src\\')
# sys.path.append(r'D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src')

import requests
from pprint import pprint
from pymongo import MongoClient
import time
from time import sleep
from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
import yaml
import schedule
import numpy as np
import pandas as pd
import os
from common import mongodb_connect

python_path = os.environ.get('PYTHONPATH')

def datetime_from_timestamp(timestamp):
    try:
        timestamp = int(timestamp)
        dt_object = datetime.fromtimestamp(timestamp)
        return str(dt_object)
    except ValueError:
        print("Invalid timestamp. Please provide a valid Unix timestamp (seconds since January 1, 1970).")
        return None

def query_subgraph(query: str):
    print("Querying Subgraph...")
    """"Query the subgraph with apost request"""
    request = requests.post('https://api.thegraph.com/subgraphs/name/frax-finance-data/fraxlend-subgraph---mainnet',
                            '',
                            json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed. HTTP return code is - {request.status_code}")
    

class DataIngestion:
    def __init__(self):
        self.round_decimals = 2
        self.query_pairs_dailyhistory = """
            {
            pairs {
                address
                name
                symbol
                maxLTV
                
                asset{
                name
                symbol
                decimals
                }
                collateral {
                id
                name
                symbol
                decimals
                }
                dailyHistory(first: 1, orderBy: timestamp, orderDirection: desc) {
                id
                exchangeRate
                totalAssetAmount
                totalAssetShare
                totalCollateral
                totalBorrowAmount
                totalBorrowShare
                interestPerSecond
                
                timestamp
                }
            }
            }
            """
        self.query_users_positions = """{{
            users({0}) {{
            id
            positions{{
                pair{{
                id
                }}
                borrowedAssetShare
                lentAssetShare
                depositedCollateralAmount
                timestamp
            }}
            }}
        }}
        """
        # Run steps
        # connect MDB collectioons
        (_, pairs, user_positions, user_notifications, _, _) = mongodb_connect()
        
        print("[Step-1]: getting and ingesting daily history...\n")
        self.pdf_pairs_dailyhistory, self.data_pairs_dailyhistory = self.get_pairs_dailyhistory(pairs)
        print("[Step-2]: getting and ingesting user positions...\n")
        self.data_users_positions = self.get_user_positions(user_positions)
        print("[Step-3]: Creating and ingesting user notifications...\n")
        self.data_notifications = self.create_notification_data(self.data_users_positions, self.pdf_pairs_dailyhistory, user_notifications)
        print("[DI Process Completed]")
    
    def simplify_dailyHistory(self, data_list_dict: list[dict], key: str):
        """
        Converts the daily History key to a dict() from a list(dict())
        """
        print("De-listing daily history value...")
        for data_dict in data_list_dict:
            # Extract the single dictionary from the list (if present)
            if isinstance(data_dict.get(key), list) and len(data_dict[key]) == 1:
                data_dict[key] = data_dict[key][0]
            else:
                raise AttributeError(f"Pairs data data {key} format is wrong")
        print('---------------------------------- Function: simplify_dailyHistory -------------------------------------')
        return data_list_dict
    
    def filter_zero_positions(self, pos: dict) ->bool:
        if abs(int(pos['borrowedAssetShare'])) +  abs(int(pos['lentAssetShare']))+ abs(int(pos['depositedCollateralAmount'])) ==0:
            return False
        else:
            return True
    
    def get_pairs_dailyhistory(self, pairs_collections):
        """Query the pairs daily histrory and update the data into database and created pandas DF for fater IR"""
        print("Staring getting pairs data...")
        try:
            results_pairs_dailyhistory = query_subgraph(self.query_pairs_dailyhistory)
        except Exception as error:
            # handle the exception
            print("An exception occurred:", type(error).__name__)
        if results_pairs_dailyhistory['data']:
            if results_pairs_dailyhistory['data']['pairs']:
                data_pairs_dailyhistory = results_pairs_dailyhistory['data']['pairs']
                # returns a list of dictoinary
                # de-list daily history
                data_pairs_dailyhistory = self.simplify_dailyHistory(data_pairs_dailyhistory, "dailyHistory")
                print("Iterating over pairs...")
                for pair_info_dict in data_pairs_dailyhistory:
                    
                    # Extract decimals
                    pair_asset_decimal = int(pair_info_dict["asset"]["decimals"])
                    pair_col_decimal = int(pair_info_dict["collateral"]["decimals"])
                    assert (pair_asset_decimal!= 0 and pair_col_decimal !=0), "Decimals cant be zero"

                    # extract total bprrow/ lend amounts
                    total_borrow_amt_raw = int(pair_info_dict["dailyHistory"]["totalBorrowAmount"])
                    total_col_amt_raw = int(pair_info_dict["dailyHistory"]["totalCollateral"])
                    total_asset_amt_raw = int(pair_info_dict["dailyHistory"]["totalAssetAmount"])
                    # calcualte features
                    total_borrow_amt_scaled = round(total_borrow_amt_raw/ 10**pair_asset_decimal, self.round_decimals)
                    total_col_amt_scaled= round(total_col_amt_raw/ 10**pair_col_decimal, self.round_decimals)
                    total_asset_amt_scaled = round(total_asset_amt_raw/ 10**pair_asset_decimal, self.round_decimals)

                    pair_info_dict["show_pair_symbol"] = f"{pair_info_dict['collateral']['symbol']}/{pair_info_dict['asset']['symbol']}"
                    
                    # calculate exchange rate 
                    # exchange rate  = 1 /(exchangeRate/ collateral_decimals) # UNIT FRAX
                    ex_rate_init = int(pair_info_dict["dailyHistory"]["exchangeRate"])/ 10**pair_col_decimal
                    if ex_rate_init == 0:
                        ex_rate_scaled = None
                    else:
                        ex_rate_scaled = round(1/ex_rate_init, self.round_decimals)
                    # calcualte Borrow APR  & Lend APR 
                    interest_per_year = round((int(pair_info_dict["dailyHistory"]["interestPerSecond"])/ 10**pair_asset_decimal) * 60 * 60 * 24 * 365,
                                            self.round_decimals)
                    # borrow_APR = (interestPerSecond / 10**pair_asset_decimal) * * 60 * 60 * 24 * 365 #UNIt - %
                    borrow_APR = interest_per_year *100
                    # lend_APR = (borrow_APR / totalAssetAmount) * totalBorrowAmount #UNIt - %
                    if total_asset_amt_scaled ==0:
                        lend_APR = None
                    else:
                        lend_APR = round((borrow_APR / total_asset_amt_scaled) * total_borrow_amt_scaled, self.round_decimals)
                    # borrow_APR > lend_APR
                    # Add features to the dictionary
                    pair_info_dict["dailyHistory"]["total_borrow_amt_scaled"] = total_borrow_amt_scaled
                    pair_info_dict["dailyHistory"]["total_col_amt_scaled"] = total_col_amt_scaled
                    pair_info_dict["dailyHistory"]["total_asset_amt_scaled"] = total_asset_amt_scaled
                    pair_info_dict["dailyHistory"]["ex_rate_scaled"] = ex_rate_scaled
                    pair_info_dict["dailyHistory"]["borrow_APR"] = borrow_APR
                    pair_info_dict["dailyHistory"]["lend_APR"] = lend_APR

                    time = int(pair_info_dict["dailyHistory"]["timestamp"])
                    pair_info_dict["dailyHistory"]["date_time"] = datetime_from_timestamp(time) 
                # convert to pandas dataframe for faster IR
                print("Creatinig pandas dataframe...")
                pdf_pairs_dailyhistory = pd.json_normalize(data_pairs_dailyhistory, sep='_')
                print("Running MongoDB operations on pairs_collections...")
                pairs_collections.drop()
                pairs_collections.insert_many(data_pairs_dailyhistory)
                
        print('---------------------------------- Function: get_pairs_dailyhistory -------------------------------------')
        return pdf_pairs_dailyhistory, data_pairs_dailyhistory
    
    def get_user_positions(self, user_positions_collection) -> list[dict]: 
        """Query the grapgh data and get the user positions as list of dictionaries"""
        query_user_chunk_num =1000
        # initially start with the first 200 users
        results_users_positions = query_subgraph(self.query_users_positions.format(f"first: {query_user_chunk_num}"))
        if results_users_positions['data']:
            if results_users_positions['data']['users']:
                data_users_positions = results_users_positions['data']['users']
        print("initial length of data_users_positions -", len(data_users_positions))
        # then itererate over 200 users and skip

        skip_users = query_user_chunk_num
        while(True):
            print(f"Condition - skip: {skip_users}")
            #TODO: modify this logic when number of users get more than 2000, cuurently skip:200 return only 100 user ids 
            results_users_positions = query_subgraph(self.query_users_positions.format(f"skip: {skip_users}"))
            skip_users+=query_user_chunk_num
            if results_users_positions['data']:
                if results_users_positions['data']['users']:
                    data_users_positions_skip = results_users_positions['data']['users']
                    print("length of data_users_positions_skip-", len(data_users_positions_skip))
                    if len(data_users_positions_skip)==0:
                        break
                    else:
                        data_users_positions.extend(data_users_positions_skip)
                else:
                    break
            else:
                break

        print("total length of data_users_positions -", len(data_users_positions))
        print("Running MongoDB operations on user_positions_collection...")
        user_positions_collection.drop()
        user_positions_collection.insert_many(data_users_positions)
        print('---------------------------------- Function: get_user_positions -------------------------------------')
        return data_users_positions
    
    def create_notification_data(self, data_users_positions, pdf_pairs_dailyhistory, db_collection):
        # def create_user_notifications(data_users_positions, pdf_pairs_dailyhistory):
        data_notifications = []
        # iterate over the users
        for user_pos in data_users_positions:
            notif_user_pos = {}
            # add user to new dict
            notif_user_pos = {'wallet_id': user_pos['id'],
                              'hlink_etherscanner': f"https://etherscan.io/address/{user_pos['id']}",
                              'hlink_fraxfacts': f"https://facts.frax.finance/fraxlend/users/{user_pos['id']}"
            }
            

            # iterate over the different positions
            notif_postions = [] 
            if user_pos['positions']:
                for pos in user_pos['positions']:
                    if self.filter_zero_positions(pos):
                        notif_pos= {}
                        # get the id of each pair
                        pos_pair_id = pos['pair']['id']
                        # get the information of the partiular pair
                        pdf_pair_info = pdf_pairs_dailyhistory[pdf_pairs_dailyhistory['address']==pos_pair_id]
                        # extract pair-level features 
                        pair_asset_decimal = int(pdf_pair_info["asset_decimals"].values[0])
                        pair_col_decimal = int(pdf_pair_info["collateral_decimals"].values[0])
                        col_unit = pdf_pair_info["collateral_symbol"].values[0]
                        pair_symbol = pdf_pair_info["show_pair_symbol"].values[0]
                        pair_max_LTV = float(pdf_pair_info["maxLTV"].values[0])/ 10**5
                        pair_ex_rate = float(pdf_pair_info["dailyHistory_ex_rate_scaled"].values[0])
                        total_col_amt_scaled = int(pdf_pair_info["dailyHistory_total_col_amt_scaled"].values[0])
                        pair_borrow_APR = float(pdf_pair_info["dailyHistory_borrow_APR"].values[0])
                        pair_lend_APR = float(pdf_pair_info["dailyHistory_lend_APR"].values[0]) 
                        pos_datetime = datetime_from_timestamp(int(pos['timestamp']))

                        # create a new dictionary
                        notif_pos = {
                            'pos_datetime': pos_datetime,
                            'pair_id': pos_pair_id,
                            'pair_symbol': pair_symbol,
                            'collateral_symbol': col_unit,
                            'pair_ex_rate': pair_ex_rate,
                            'pair_borrow_APR': pair_borrow_APR,
                            'pair_lend_APR': pair_lend_APR,
                            }
                        
                        # calculate features

                        # calcualte borrowed amount, shares are not scaled that why take raw features so that the scales cancel out
                        try:
                            total_b_amt_per_share = int(pdf_pair_info["dailyHistory_totalBorrowAmount"].values[0])/int(pdf_pair_info["dailyHistory_totalBorrowShare"].values[0])
                            # borrow_amount =((borrowedAssetShare/10** pair_asset_decimal) * (totalBorrowAmount/totalBorrowShare)) # Unit FRAX
                            user_borrow_amt_scaled = round((int(pos["borrowedAssetShare"])/10**pair_asset_decimal) * total_b_amt_per_share, self.round_decimals)
                            # convert to dollar format: 100000  -> 1,000,000
                            user_borrow_amt_scaled = f'{user_borrow_amt_scaled:,}'
                        except (ZeroDivisionError, TypeError):
                            user_borrow_amt_scaled = None

                        # calculate deposited collateral amount #UNIT col_symbol
                        user_dep_col_amt_scaled = round((int(pos["depositedCollateralAmount"])/ 10**pair_col_decimal) , self.round_decimals)
                        # convert to dollar format: 100000  -> 1,000,000
                        user_dep_col_amt_scaled = f'{user_dep_col_amt_scaled:,}'
                        # calcualte lent amount
                        try:
                            total_l_amt_per_share = int(pdf_pair_info["dailyHistory_totalAssetAmount"].values[0]) / int(pdf_pair_info["dailyHistory_totalAssetShare"].values[0])
                            # lent_amount =((borrowedAssetShare/10** pair_asset_decimal) * (totalAssetAmount/totalAssetShare)) # Unit FRAX
                            user_lent_amt_scaled = round((int(pos["lentAssetShare"])/ 10**pair_asset_decimal) * total_l_amt_per_share, self.round_decimals)
                            # convert to dollar format: 100000  -> 1,000,000
                            user_lent_amt_scaled = f'{user_lent_amt_scaled:,}'
                        except (ZeroDivisionError, TypeError):
                            user_lent_amt_scaled = None
                        # calculate current LTV
                        # user_borrow_amt_scaled / (user_col_amt_scaled * ex_rate(pair level)) # unit is percentage
                        try:
                            user_current_LTV = round((user_borrow_amt_scaled/ (total_col_amt_scaled * pair_ex_rate)) *100, 2)
                        except (ZeroDivisionError, TypeError):
                            user_current_LTV = None
                        # calculate Liquidation price 
                        # LP = user_borrow_amt_scaled / (user_col_amt_scaled * max_LTV) #Unit FRAX
                        try:
                            user_liquidation_price_scaled = round(user_borrow_amt_scaled / (user_dep_col_amt_scaled * pair_max_LTV), self.round_decimals)
                            # convert to dollar format: 100000  -> 1,000,000
                            user_liquidation_price_scaled = f'{user_liquidation_price_scaled:,}'
                        except (ZeroDivisionError, TypeError):
                            user_liquidation_price_scaled = None
                        notif_pos["user_borrow_amt_scaled"] = user_borrow_amt_scaled
                        notif_pos["user_dep_col_amt_scaled"] = user_dep_col_amt_scaled
                        notif_pos["user_lent_amt_scaled"] = user_lent_amt_scaled
                        notif_pos["user_current_LTV"] = user_current_LTV
                        notif_pos["user_liquidation_price_scaled"] = user_liquidation_price_scaled
                        notif_postions.append(notif_pos)
                        
            notif_user_pos['positions'] = notif_postions

            data_notifications.append(notif_user_pos)
        # TODO: modify data update logic for each user-positions
        print("Running MongoDB operations on user_notifications_collection...")
        db_collection.drop()  
        db_collection.insert_many(data_notifications)
        print('---------------------------------- Function: create_notification_data -------------------------------------')
        return data_notifications


if __name__ == '__main__':
    try:
        print("Initializing Data Ingestion \n...")

        data_ingest = DataIngestion()

    except Exception as error:
        print("An exception occurred in DATA INGESTION MODULE:", type(error).__name__)

