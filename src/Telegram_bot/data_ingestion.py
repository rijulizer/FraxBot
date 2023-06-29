import requests
from pprint import pprint
from pymongo import MongoClient
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler

def query_subgraph(query: str):
    print("Inside query_subgraph function!")
    """"Query the subgraph with apost request"""
    request = requests.post('https://api.thegraph.com/subgraphs/name/frax-finance-data/fraxlend-subgraph---mainnet',
                            '',
                            json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed. HTTP return code is - {request.status_code}")
    
def segregate_data(query):
    print("Inside segregate_data function")
    
    result = query_subgraph(query)
    
    for query_ele in result['data']['pairs']:
        print('*'*50)
        pair_document = {"address": query_ele["address"],
                    "asset_decimals": query_ele["asset"]["decimals"],
                    "asset_name": query_ele["asset"]["name"],
                    "asset_symbol": query_ele["asset"]["symbol"],
                    "collateral_id": query_ele['collateral']["id"],
                    "collateral_name": query_ele['collateral']["name"],
                    "collateral_symbol": query_ele['collateral']["symbol"],
                    'dailyHistory_exchangeRate': query_ele["dailyHistory"][0]['exchangeRate'],
                    'dailyHistory_id': query_ele["dailyHistory"][0]['id'],
                    'dailyHistory_interestPerSecond': query_ele["dailyHistory"][0]['interestPerSecond'],
                    'dailyHistory_lastAccrued': query_ele["dailyHistory"][0]['lastAccrued'],
                    'dailyHistory_timestamp': query_ele["dailyHistory"][0]['timestamp'],
                    'dailyHistory_totalAssetAmount': query_ele["dailyHistory"][0]['totalAssetAmount'],
                    'dailyHistory_totalAssetShare': query_ele["dailyHistory"][0]['totalAssetShare'],
                    'dailyHistory_totalBorrowAmount': query_ele["dailyHistory"][0]['totalBorrowAmount'],
                    'dailyHistory_totalBorrowShare': query_ele["dailyHistory"][0]['totalBorrowShare'],
                    'dailyHistory_totalCollateral': query_ele["dailyHistory"][0]['totalCollateral'],
                    'dailyHistory_totalFeesAmount': query_ele["dailyHistory"][0]['totalFeesAmount'],
                    'dailyHistory_totalFeesShare': query_ele["dailyHistory"][0]['totalFeesShare'],
                    'dailyHistory_utilization': query_ele["dailyHistory"][0]['utilization'],
                    'name': query_ele["name"]
                    }
        print(pair_document)

        res = list(db.pair_characteristics.find({'collateral_symbol': pair_document["collateral_symbol"]}))
        print('\n\n',res,'\n\n')
        if len(res)==0:
            db.pair_characteristics.insert_one(pair_document)
        else:
            db.pair_characteristics.update_many({'collateral_symbol': pair_document["collateral_symbol"]},{'$set': pair_document})
        
        for position in query_ele['positions']:
            print('-'*50)
            positions_document = {"user_id": position['user']['id'],
                                'collateral_symbol': query_ele['collateral']["symbol"],
                                'collateral_name': query_ele['collateral']["name"],
                                'borrowedAssetShare': position['borrowedAssetShare'],
                                'depositedCollateralAmount': position['depositedCollateralAmount'],
                                'lentAssetShare': position['lentAssetShare'],
                                'timestamp': position['timestamp']
                                }
            print(positions_document)
            print('-'*50)   

            pos_res = list(db.positions.find({'collateral_symbol': pair_document["collateral_symbol"], 'user_id': position['user']['id']}))
            if len(pos_res)==0:
                db.positions.insert_one(positions_document)
            else:
                db.positions.update_many({'collateral_symbol': pair_document["collateral_symbol"], 'user_id': position['user']['id']},{'$set': positions_document})
    
    # job_id.remove()
    # scheduler.shutdown(wait = False)
    return         

if __name__ == '__main__':
    query = """
    {
    pairs {
        address
        name
        asset{
        name
        symbol
        decimals
        }
        collateral {
        id
        name
        symbol
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
        utilization
        totalFeesAmount
        totalFeesShare
        lastAccrued
        timestamp
        }
        positions(first: 2, orderBy: borrowedAssetShare, orderDirection: desc) {
        user {
            id
        }
        borrowedAssetShare
        depositedCollateralAmount
        lentAssetShare
        timestamp
        }
    }
    }
    """
    try:
        connection_string = "mongodb+srv://meghachakravorty:jgOokbXraHxWjHHx@cluster0.h1o4nlj.mongodb.net/"

        db_client = MongoClient(connection_string, connect=False)

        db = db_client['frax']

        scheduler = BlockingScheduler()
        scheduler.add_job(segregate_data, 'interval', seconds = 30*60, args = [query])
        scheduler.start()
    except Exception as error:
        print('Cause: {}'.format(error))