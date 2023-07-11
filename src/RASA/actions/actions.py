import sys
sys.path.append('d:\\FRAX_project\\FraxBot\\src\\')
# sys.path

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted
from datetime import datetime
import pymongo
from pymongo import MongoClient
import yaml
import os
import numpy as np
import pandas as pd

from common import mongodb_connect

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
    if result:
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
    return(
        {
            "message_id" : message_id,
            "user_id" : user_id, 
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
    
def upload_metadata(metadata):
    (_, telegram_metadata, _, _, _) = mongodb_connect()
    telegram_metadata.insert_one(metadata)
    print("[MongoDB] Metadata uploaded...")
    return

# class ActionHelloWorld(Action):

#     def name(self) -> Text:
#         return "action_hello_world"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         print("run  - action_hello_world")
#         dispatcher.utter_message(text="Hello World!")

#         return []

class ActionSessionStart(Action):
    """
    This action gets called automatically at the begining of a new session and gets user/channel metadat and stores it
    in the meta data DB. It further sets a slot to specify if the user is new or returning.
    """

    def name(self) -> Text:
        return "action_session_start"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('[Action] action_session_start....')

        # get session started metadata
        metadata = tracker.get_slot("session_started_metadata")
        telegram_metadata = format_telegram_metadata(metadata)#tracker.latest_message["metadata"])
        upload_metadata(telegram_metadata)

        # Todo: check DB 
        evt_slotset = SlotSet(key = "slot_old_user", value = "True")
        
        print("\n [Action] tracker.latest_message:\n",tracker.latest_message)
        print("\n\n [Action] tracker.slots:\n",tracker.slots)

        # the session should begin with a `session_started` event and an `action_listen`
        # as a user message follows
        return [SessionStarted(), ActionExecuted("action_listen"), evt_slotset]
    
class ActionBotIntro(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_bot_intro"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('[Action] action_bot_intro....')

        buttons = [{"title": "Current Positions" , "payload": "/get_current_wallet_status"},
                   {"title": "Subscribe", "payload": "/subscribe_daily_updates"},
                   {"title": "View Subscriptions", "payload": "/get_list_of_existing_subscibed_wallets"},
                   {"title": "Unsubscribe","payload": "/unsubscribe"},
                   {"title": "Exit", "payload": "/goodbye"}]

        if tracker.latest_message["intent"]["name"]=="greet":
            dispatcher.utter_message(text= u"Welcome! I am Frax Bot \U0001f600 \nCurrently I can help you with the following - \n\t• View the current status of your positions \n\t• Subscribe to get daily updates about your positions  \n\t• Get list of already subscribed wallets \n\t• Un-subscribe an wallet" , buttons=buttons, button_type="vertical")
        elif tracker.latest_message["intent"]["name"]=="continue":
            dispatcher.utter_message(text= u"Great! What should we do next? \n\t• View the current status of your positions \n\t• Subscribe to get daily updates about your positions  \n\t• Get list of already subscribed wallets \n\t• Un-subscribe an wallet" , buttons=buttons, button_type="vertical")
        return []

class ActionGetData(Action):
    """Debugging purpose"""

    def name(self) -> Text:
        return "action_get_data"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        print('[Action] action_get_data....')
        tck = tracker.latest_message
        print("\nLATEST MESSAGE:\n",tracker.latest_message)
        print("\nSLOTS:\n",tracker.slots)
        print("\nLatest_message_TEXT:\n",tracker.latest_message['text'])
        print("\nLatest_message_METADATA:\n",tracker.latest_message['metadata'])

        # dispatcher.utter_message(text=f"Could you tell me the id of the wallet you are interested in?")

        return []


# class ActionGetWalletId(Action):

#     def name(self) -> Text:
#         return "action_get_wallet_id"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         print('\nFetching your wallet id...')
#         metadata = format_updates(tracker.latest_message["metadata"])
#         upload_metadata(metadata)
#         # telegram_metadata.insert_one(metadata)

#         tck = tracker.latest_message
#         sender_id = tracker.sender_id
#         wallet_id = tracker.slots["wallet_id"]
#         task = tracker.slots["task"]
        
#         print("\nLATEST MESSAGE:\n",tracker.latest_message)
#         print("\n\nSLOTS:\n",tracker.slots)
#         print("\nTEXT:\n",tracker.latest_message['text'])

#         # fn = metadata['first_name']
#         # wallet_id = SlotSet("wallet_id", tracker.latest_message['text'])
#         text = decide_action(wallet_id,task,sender_id)
#         # dispatcher.utter_message(text=f"Your wallet id is {tracker.latest_message['text']}.\n Until next time my friend!")
#         dispatcher.utter_message(text=text)
#         return []

# def decide_action(wallet_id, task,sender_id):
#     if task=="view_wallet":
#         return(select(wallet_id))
#     elif task=="subscribe":
#         return(subscribe(wallet_id,sender_id))    
#     elif task=="unsubscribe":
#         return(unsubscribe(wallet_id,sender_id))
#     else:
#         return("Subscription function is WIP")
    
# # def format_date(messageTime):
# #     messageTime = datetime.fromtimestamp(messageTime) # datetime format
# #     messageTime = messageTime.strftime('%Y-%m-%d %H:%M:%S') # formatted datetime    
# #     TimeStamp = str(messageTime)
# #     return (TimeStamp)

# def subscribe(wallet_id, sender_id):
#     db, pairs, telegram_metadata, wallet, subscription = connect()
#     success_flag = False

#     res = list(wallet.find({'user_id': wallet_id}))
#     if len(res)==0:
        
#         text = f"Could not find a wallet with id {wallet_id} to subscribe!"

#     else:
#         doc_id = str(res[-1]['_id'])

#         record = {"wallet_id":wallet_id,"user_id":sender_id,"mongo_doc_id":doc_id} 
#         subscription.insert_one(record)
        
#         text = f"You have successfully subscribed to wallet {wallet_id}"
#         success_flag = True

#     return (text)


# def unsubscribe(wallet_id, sender_id):
#     db, pairs, telegram_metadata, wallet, subscription = connect()
#     success_flag = False
#     res = list(subscription.find({'wallet_id': wallet_id,'user_id':sender_id}))
#     if len(res)==0:
#         text = f"You are not subscribed to wallet {wallet_id}!"
#     else:
#         subscription.delete_many({'wallet_id':wallet_id,'user_id':sender_id})
#         text = f"You have successfully unsubscribed to wallet {wallet_id}"
#         success_flag = True
#     return (text)

# def create_message_select_query(ans):
#     print('\n\nCreating reply to Select query...')

#     df = pd.DataFrame(columns=['column','value'])
#     df['column'] = list(ans.keys())
#     df['value'] = list(ans.values())

#     print('='*50)

#     df = df[df['column']!='_id']
#     print(df.to_string())

#     # df["value"] = df["value"].str.wrap(10)

#     message=df.to_string(index=False, header=False,col_space=15, na_rep="Unknown",justify="right")

#     print(message)

#     return message



# def select(wallet_id):
#     print( "="*25 + " Select "+ "="*25)
#     print(f'Wallet_id passed during Select: {wallet_id}') 
#     success_flag = False
#     db, pairs, telegram_metadata,wallet,subscription = connect()
#     res = list(wallet.find({'user_id': wallet_id}))

#     print(f'\n\nResult: {res}\n\n')

#     doc_id = str(res[-1]['_id'])

#     print(f'Document id: {doc_id}')

#     if(res):
#         print('Select query returned values')
#         text = "Received 📖 Information about your wallet:"+create_message_select_query(res[-1])
#         success_flag = True
#     else:
#         text = "No orders found inside the database."
            
#     return (text)

