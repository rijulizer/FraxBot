import sys
import os
# sys.path.append(r'D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src')
# sys.path
python_path = os.environ.get('PYTHONPATH')
print(python_path)
sys.path.append(python_path)

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
from common import get_wallet_position
# get monogdb collections
(db, pairs, user_positions, user_notifications, telegram_metadata, subscription) = mongodb_connect()

# debug
super_user_id = None#"6278581231" # must be a string

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
        if tracker.sender_id: #for debugging and development
            user_id  = str(tracker.sender_id) 
        else:
            user_id = super_user_id

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
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

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

class ActionDefaultFallback(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] fallback action....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        buttons = [{"title": "Current Positions" , "payload": "/get_current_wallet_status"},
                   {"title": "Subscribe", "payload": "/subscribe_daily_updates"},
                   {"title": "View Subscriptions", "payload": "/get_list_of_existing_subscibed_wallets"},
                   {"title": "Unsubscribe","payload": "/unsubscribe"},
                   {"title": "Exit", "payload": "/goodbye"}]

        dispatcher.utter_message(text= u'''Sorry I could not understand your request!\n
        Currently I can help you with the following -
        \t• View the current status of your positions
        \t• Subscribe to get daily updates about your positions
        \t• Get list of already subscribed wallets
        \t• Un-subscribe an wallet''', buttons=buttons, button_type="vertical")
        
        return []
    
class ActionUnsubHandler(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_unsubscribe_handler"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_unsubscribe_handler....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        # define default values
        return_text = "You haven't subscribed any wallets yet"
        wallet_buttons = None
        # when false add a followup Action
        events = [SlotSet("slot_unsub_wallets", False), FollowupAction("utter_continue_or_exit")]

        if tracker.get_slot("slot_old_user"):
            # old user flow
            # get user id from tracke
            if tracker.sender_id: #for debugging and development
                user_id  = str(tracker.sender_id) 
            else:
                user_id = super_user_id
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
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        # get user id from tracker
        if tracker.sender_id: #for debugging and development
            user_id  = str(tracker.sender_id) 
        else:
            user_id = super_user_id
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

class ActionGetSublist(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_get_sublist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_get_sublist....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        # define default values
        return_text = "You haven't subscribed any wallets yet"
        
        # process if only old_user as new user wont have subscribed wallets
        if tracker.get_slot("slot_old_user"):
            # old user flow
            # get user id from tracker
            if tracker.sender_id: #for debugging and development
                user_id  = str(tracker.sender_id) 
            else:
                user_id = super_user_id

            subscribed_wallets = get_subscribed_wallets(subscription, user_id)
            if subscribed_wallets:
                sub_list_str = "\n‣  ".join(subscribed_wallets)

                return_text = f"You have subscribed the following wallets -\n‣  {sub_list_str}" #TODO: Modify for better looking text
        dispatcher.utter_message(text=return_text)

        if tracker.latest_message["intent"]["name"]=="subscribe_daily_updates":
            # if the intent is subscribe return further subscription actions
            event =[]
            buttons = [
                {"title": "Yes" , "payload": "/affirm"},
                {"title": "No", "payload": "/deny"},
                ]
            dispatcher.utter_message(text= "Would you like to subscibe a new wallet -", buttons=buttons)#, button_type="vertical")
        
        
        else:
            # if the intent is to just get the subscription list or anhthing else utter_continue_or_exit
            event = [FollowupAction("utter_continue_or_exit")]
        return event

class ActionSubscribe(Action):
    """This action introduces the Bot features and provides options to carryforward conversation in terms of buttons"""
    def name(self) -> Text:
        return "action_subscribe_wallet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_subscribe_wallet....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        # get user id from tracker
        if tracker.sender_id: #for debugging and development
            user_id  = str(tracker.sender_id) 
        else:
            user_id = super_user_id

        sub_wallet = tracker.slots["slot_wallet_id"]
        print(f" [debug] sub_wallet - {sub_wallet}")

        subscribed_wallets = get_subscribed_wallets(subscription, user_id)
        # Append the selected wallet to the list of subscibed wallets
        try:
            modified_wallet_list = subscribed_wallets.copy()
            modified_wallet_list.append(sub_wallet)
            modified_wallet_list = list(set(modified_wallet_list))
        except:
            modified_wallet_list = subscribed_wallets.copy()
            modified_wallet_list = list(set(modified_wallet_list))

        print(f" [debug] modified_wallet_list - {modified_wallet_list}")
        if subscribed_wallets:
            # if the user has existing wallets then update the list of wallets
            update_wallets_for_subscription(subscription, user_id, modified_wallet_list)
        else:
            # else add a new entry to the Subscription collection
            add_wallets_for_subscription(subscription, user_id, modified_wallet_list)

        dispatcher.utter_message(text=f"The wallet {sub_wallet} is added to your subscription list")
        # if the the wallet is subscribed set the old_user as True
        # for new user in the same session this will be indicative that the user is not new anymore
        return [SlotSet("slot_old_user", True), FollowupAction("utter_continue_or_exit")]

class ActionGetPositionHandler(Action):

    def name(self) -> Text:
        return "action_get_position_handler"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_get_position_handler....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        #  for new users or users who dont have subscribed wallets - 
        wallet_buttons = None
        return_text = "Please type a new wallet to get the current positions"
        if tracker.sender_id: #for debugging and development
            user_id  = str(tracker.sender_id) 
        else:
            user_id = super_user_id

        subscribed_wallets = get_subscribed_wallets(subscription, user_id)
    
        if tracker.get_slot("slot_old_user") and subscribed_wallets:
            # if old user and has subscription list then offer more options
            wallet_buttons = [{"title": wallet , "payload": wallet} for wallet in subscribed_wallets]
            # wallet_buttons.append({"title": "Add New Wallet" , "payload": "/add_new_wallet"})
            return_text = "Please select a wallet from existing subscribed wallets or type a new wallet"
            # #set slot true if there are wallets to unsubscribe
            # events = [SlotSet("slot_unsub_wallets", True)]
        dispatcher.utter_message(text=return_text, buttons=wallet_buttons, button_type="vertical")
        return []
    
class ActionGetPosition(Action):

    def name(self) -> Text:
        return "action_get_position"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print('\n [Action] action_get_position....')
        print(" [debug] SLOTS:", tracker.slots)
        print(" [debug] Latest Intent:", tracker.latest_message["intent"]["name"])

        # get user id from tracker
        if tracker.sender_id: #for debugging and development
            user_id  = str(tracker.sender_id) 
        else:
            user_id = super_user_id
        position_wallet = tracker.slots["slot_wallet_id"]
        print(f" [debug] position_wallet - {position_wallet}")
        # TODO: Implement get_wallet_position():
        position_data = get_wallet_position(user_notifications, position_wallet,"current status")
        subscribed_wallets = get_subscribed_wallets(subscription, user_id)
        slot_wallet_has_position = False
        slot_wallet_subscribed = False
        # default action listen
        listen_event = ActionExecuted("action_listen")
        if position_data:
            # the wallet is in the database and returend the positions
            # check if the wallet is already subscribed
            slot_wallet_has_position = True
            if position_wallet in subscribed_wallets:
                # the wallet not in database
                slot_wallet_subscribed = True
                # dispatcher.utter_message(text= f"Here is your current wallet positions - {str(position_data)}")
                # dispatcher.utter_message(text=f"Your wallet has {len(position_data)} positions.")
                for msg in position_data:
                    dispatcher.utter_message(text=msg)
                listen_event = None 
            else:
                # dispatcher.utter_message(text= f"Here is your current wallet positions - {str(position_data)}")
                # dispatcher.utter_message(text=f"Your wallet has {len(position_data)} positions.")
                for msg in position_data:
                    dispatcher.utter_message(text=msg)
                buttons = [
                    {"title": "Yes" , "payload": "/affirm"},
                    {"title": "No", "payload": "/deny"},
                    ]
                dispatcher.utter_message(text= f"Would you like to subscribe wallet {str(position_wallet)}-", buttons=buttons)
                # listen_event = ActionExecuted("action_listen")

        else:
            dispatcher.utter_message(text="This wallet does not have positions")
            # the wallet not in database
            buttons = [
                {"title": "Yes" , "payload": "/affirm"},
                {"title": "No", "payload": "/deny"},
                ]
            dispatcher.utter_message(text= "Would you like to try another wallet -", buttons=buttons)
            # listen_event = ActionExecuted("action_listen")
        
        events = [SlotSet("slot_wallet_has_position", slot_wallet_has_position), SlotSet("slot_wallet_subscribed",slot_wallet_subscribed)]
        # if listen_event:
        #     events.append(listen_event)
        return events


