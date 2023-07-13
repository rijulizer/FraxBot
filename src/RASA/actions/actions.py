import sys
sys.path.append('d:\\FRAX_project\\FraxBot\\src\\')
# sys.path

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, FollowupAction


# import pymongo
# from pymongo import MongoClient
# import yaml
# import os

from common import mongodb_connect
from common import get_subscribed_wallets, add_wallets_for_subscription, update_wallets_for_subscription
from common import format_telegram_metadata, upload_channel_metadata, check_returning_user

# get monogdb collections
(db, telegram_metadata, subscription, pairs, wallet) = mongodb_connect()

# debug
super_user_id = 6278581239

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
        print('\n [Action] action_session_start....')
        print(" [debug] SLOTS:", tracker.slots)
        # check DB if the user is a returning user 
        user_id  = super_user_id #R tracker.sender_id
        if user_id:
            returning_user = check_returning_user(telegram_metadata, user_id)
        else: 
            returning_user = True # Null users_ids are considered returning user
        #set slot true if its a returning user
        evt_slotset = SlotSet("slot_old_user", returning_user)

        if user_id:
            # Upload metadata if non null user_id
            # get session started metadata
            metadata = tracker.get_slot("session_started_metadata")
            flag_data_none, channel_metadata = format_telegram_metadata(metadata)#tracker.latest_message["metadata"])
            if flag_data_none:
                upload_channel_metadata(telegram_metadata, channel_metadata)

        # the session should begin with a `session_started` event and an `action_listen`
        # as a user message follows
        return [SessionStarted(), evt_slotset, ActionExecuted("action_listen")] 
    
class ActionBotIntro(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_bot_intro"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_bot_intro....')
        print(" [debug] SLOTS:", tracker.slots)

        buttons = [{"title": "Current Positions" , "payload": "/get_current_wallet_status"},
                   {"title": "Subscribe", "payload": "/subscribe_daily_updates"},
                   {"title": "View Subscriptions", "payload": "/get_list_of_existing_subscibed_wallets"},
                   {"title": "Unsubscribe","payload": "/unsubscribe"},
                   {"title": "Exit", "payload": "/goodbye"}]

        if tracker.latest_message["intent"]["name"]=="greet":
            dispatcher.utter_message(text= u"Welcome! I am Frax Bot \U0001f600 \nCurrently I can help you with the following - \n\t• View the current status of your positions \n\t• Subscribe to get daily updates about your positions \n\t• Get list of already subscribed wallets \n\t• Un-subscribe an wallet" , buttons=buttons, button_type="vertical")
        else : #tracker.latest_message["intent"]["name"]=="continue":
            dispatcher.utter_message(text= u"Great! What should we do next? \n\t• View the current status of your positions \n\t• Subscribe to get daily updates about your positions \n\t• Get list of already subscribed wallets \n\t• Un-subscribe an wallet" , buttons=buttons, button_type="vertical")
        return []

# class ActionGetData(Action):
#     """Debugging purpose"""

#     def name(self) -> Text:
#         return "action_get_data"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         print('[Action] action_get_data....')
#         tck = tracker.latest_message
#         print("\nLATEST MESSAGE:\n",tracker.latest_message)
#         print("\nSLOTS:\n",tracker.slots)
#         print("\nLatest_message_TEXT:\n",tracker.latest_message['text'])
#         print("\nLatest_message_METADATA:\n",tracker.latest_message['metadata'])

#         # dispatcher.utter_message(text=f"Could you tell me the id of the wallet you are interested in?")

#         return []

class ActionUnsubHandler(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_unsubscribe_handler"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_unsubscribe_handler....')
        print(" [debug] SLOTS:", tracker.slots)

        # define default values
        return_text = "You haven't subscribed any wallets yet"
        wallet_buttons = None
        # when false add a followup Action
        events = [SlotSet("slot_unsub_wallets", False), FollowupAction("utter_continue_or_exit")]

        if tracker.get_slot("slot_old_user"):
            # old user flow
            # get user id from tracke
            user_id  = super_user_id #R tracker.sender_id
            subscribed_wallets = get_subscribed_wallets(subscription, user_id)
            if subscribed_wallets:
                wallet_buttons = [{"title": wallet , "payload": wallet} for wallet in subscribed_wallets]
                return_text = "Please select a wallet to unsubscribe"
                #set slot true if there are wallets to unsubscribe
                events = [SlotSet("slot_unsub_wallets", True)]

        dispatcher.utter_message(text=return_text, buttons=wallet_buttons, button_type="vertical")
        return events
    
class ActionUnsubWallet(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_unsubscribe_wallet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_unsubscribe_wallet....')
        print(" [debug] SLOTS:", tracker.slots)

        # get user id from tracker
        user_id  = super_user_id #R tracker.sender_id
        unsub_wallet = tracker.slots["slot_wallet_id"]
        print(f" [debug] unsub_wallet - {unsub_wallet}")

        subscribed_wallets = get_subscribed_wallets(subscription, user_id)
        # remove the selected wallet from list of subscibed wallets
        try:
            modified_wallet_list = subscribed_wallets.copy()
            modified_wallet_list.remove(unsub_wallet)
        except:
            modified_wallet_list = subscribed_wallets.copy()
        print(f" [debug] modified_wallet_list - {modified_wallet_list}")

        update_wallets_for_subscription(subscription, user_id, modified_wallet_list)

        dispatcher.utter_message(text=f"The wallet {unsub_wallet} is removed from subscription")
        return [FollowupAction("utter_continue_or_exit")]

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

