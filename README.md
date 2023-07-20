# Frax Bot 

## About Frax Bot
Frax Bot is a ```Telegram bot powered by RASA``` that provides convenient access to the status of Frax wallets. Users can effortlessly ```view the current status of their Frax wallet``` and subscribe to receive daily notifications about subscribed wallet(s). ```Managing subscriptions``` is a breeze, allowing users to ```subscribe``` and ```unsubscribe``` from multiple wallets at any time. Frax Bot ensures a seamless conversational experience by tracking user history, identifying returning users, and keeping a record of subscribed wallets.

```Rasa for the win``` - Rasa bots utilize trained models to understand user inputs, predict intents, extract entities, and determine the appropriate actions or responses. The bot can maintain context and carry out a meaningful conversation by tracking the dialogue history and considering previous user inputs. With Rasa in backend, Frax Bot endaevours to engage with users in real-time conversations, responding to their inputs and guiding them through the dialogue flow.

Frax bot is also ```user-friendly``` as it provides the users with ```options``` at every stage, depending on their requests and earlier interactions with the bot. User can select appropriate options to steer the conversation in the intended direction and accomplish their task. The user can also ```type in their request``` in stead of choosing any option prompted by the bot. The bot will try to map the request to the right (or most similar) task and proceed the conversation. Thus, Frax bot is able to achieve ``flexibility`` without losing its ```simplicity```.

## Bot functionalities

* **View current status of a wallet** - Users can choose to view current status of new wallets or wallets they have already subscribed. If the wallet id provided by the user is erroneous, they should follow prompts to provide a new wallet id.

* **Subscribe** - Users can easily subscribe to any available Frax wallet by providing its wallet id to Frax Bot. To prevent duplication, Frax Bot assists users by displaying their current subscription list before requesting a new wallet ID. This ensures that users can avoid subscribing to the same wallet multiple times and streamlines their experience.

* **Unsubscribe** - Users have the flexibility to unsubscribe from specific wallets to prevent receiving unnecessary notifications. Frax Bot simplifies the process by presenting users with a list of their subscriptions, allowing them to choose the wallet they wish to unsubscribe from. This streamlined workflow eliminates manual effort of acquiring the wallet id, thus providing users with a hassle-free experience.

* **Get Subscription list** - Managing subscriptions is also very simple with Frax Bot. Users can view their current subscription list by selecting the suitable options prompted by the bot. This enables them to make informed decisions about subscribing or unsubscribing to wallets.

* **Send Notifications** - Users with active subscriptions to Frax wallets receive daily notifications regarding their wallet position status. These notifications are delivered reliably, even if the user's Telegram app is not currently open. If a subscribed wallet no longer exists, the user will stop receiving notifications for it. However, if the wallet is restored, the user will resume receiving notifications for that wallet.

## Data

**Frax Data** - Frax Bot efficiently ingests Frax data via GraphQL queries, segregates and stores it in MongoDB. Scheduled to run hourly, the data ingestion process ensures users receive the most up-to-date information about their Frax wallets. Telegram metadata is stored at the start of each session. Moreover, MongoDB maintains a subscription collection, effectively tracking users' wallet subscriptions. Leveraging these databases, Frax Bot retrieves relevant data based on user requests.

**Rasa Bot - Training Data** - NLU training data consists of user utterances grouped by intent, along with entities representing structured information within the messages. These entities provide the necessary details for the bot to fulfill the intent. The provided nlu.yml file contains commonly used data to train the underlying Rasa model. Enhancing the bot's performance is possible by collecting more diverse data or enabling it to learn from conversations during inference.

## Set up the environment

This code base has been developed and validated in ```Python 3.9```

- Clone the repo and move to the FraxBot folder for the next steps
- Create a python virtual environment
```
python -m venv bot_venv
source bot_venv/bin/activate
```
- After creating the virtual environment, install the required packages, as listed in *requirements.txt*
```
pip install -r requirements.txt
```
### Setting up Rasa

1. To create the bot, go to ```Bot Father```, enter ```/newbot``` and follow the instructions. 

2. In this project, the Rasa server is set up to run on `http://localhost:5005`. To expose the local server to the Internet, use -
```
ngrok http 5005
```
3. Add the Telegram credentials to your ```credentials.yml```. The URL that Telegram should send messages to will look like `http://<host>:<port>/webhooks/telegram/webhook`, replacing the host and port with the appropriate values from your running Rasa server via ngrok. Add the ```bot token``` as ```access_token``` and your bot name as ```verify``` 

4. From ```RASA``` folder, run Rasa server on one terminal
```
rasa run
```
5. Similarly, from ```RASA``` folder, run Rasa action server on another terminal
```
rasa run actions
```
6. From ```common``` folder, run data_ingestion.py to extract latest data about Frax
```
python data_ingestion.py
```
7. Similarly, from ```common``` folder, run notification_sender.py to send daily updates to users who have subscribed to Frax wallet(s)
```
python notification_sender.py
```
8. Set up the relevant information in ```common_config.yml```

    * **mongo_db**:
        * **uri**: *URl for access to Frax database in MongoDB Atlas*
        * **database**: *Name of database in MongoDB Atlas*
        * **wallets_schema**: *Name of Collection that stores Wallet position information*
        * **subscription_schema**: *Name of Collection that maps Frax wallets to Telegram users*
        * **pairs_schema**: *Name of Collection that stores Pairs information, retrieved from Frax*
        * **telegram_metadata_schema**: *Name of Collection that stores Telegram metadata for Frax Bot users*
    * **telegram**:
        * **api_id**: *API id of your registered Telegram application*
        * **api_hash**: *API hash of your registered Telegram application*        
        * **bot_token**: *Bot token, obtained from Bot Father*

### Generating API id and hash for Telegram Application
1. Log in to your Telegram core: https://my.telegram.org.
2. Go to "API development tools" and fill out the form (Ensure that you are providing a few lines for description. In place of URL, you can add ```https://api.telegram.org/bot{bot_token}/``` or choose to leave it blank)
3. After submitting the form, you will get basic addresses as well as the **api_id** and **api_hash** parameters required for user authorization.

*Note: For the moment each number can only have one api_id connected to it.*

## Folder structure

```bash
├── common
│   ├── sessions
│   ├── __init__.py
│   ├── data_ingestion.py
│   ├── mongodb_connection.py
|   ├── notification_sender.py
|   ├── querydb_actions.py
├── RASA
│   ├── actions
│   │   ├── __init__.py
|   |   ├── actions.py
│   ├── data
|   |   ├── nlu.yml
|   |   ├── rules.yml
|   |   ├── stories.yml
│   ├── models
|   |   ├── tests
│   ├── tests
|   |   ├── test_stories.yml
|   ├── config.yml
|   ├── credentials.yml
|   ├── domain.yml
|   ├── endpoints.yml
|   ├── graph.html
|   ├── rasa_custom_telegram_channel.py
|   ├── story_graph.dot    
├── mongo_db_user_certificate.pem
├── common_config.yml
├── requirements.txt
├── LICENSE
└── .gitignore
```
