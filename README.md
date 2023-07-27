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

## Folder structure

└── FraxBot
    ├── LICENSE
    ├── README.md
    ├── docker
    │   ├── action_server_dockerfile
    │   ├── rasa_dockerfile
    │   └── scheduler_dockerfile
    ├── mongodb_user_certificate.pem
    ├── requirements-core.txt
    ├── requirements-dev.txt
    ├── requirements.txt
    ├── requirements_actions.txt
    └── src
        ├── RASA
        │   ├── actions
        │   │   ├── __init__.py
        │   │   ├── actions.py
        │   │   └── fallback.yml
        │   ├── config.yml
        │   ├── credentials.yml
        │   ├── data
        │   │   ├── nlu.yml
        │   │   ├── rules.yml
        │   │   └── stories.yml
        │   ├── docker_endpoints.yml
        │   ├── domain.yml
        │   ├── endpoints.yml
        │   ├── graph.html
        │   ├── models
        │   ├── rasa_custom_telegram_channel.py
        │   ├── sessions
        │   │   ├── Bot.session
        │   │   └── Bot.session-journal
        │   ├── story_graph.dot
        │   └── tests
        │       └── test_stories.yml
        ├── common
        │   ├── __init__.py
        │   ├── mongodb_connection.py
        │   ├── notification_sender.py
        │   ├── notification_sender_old.py
        │   ├── querydb_actions.py
        │   ├── scheduler_module.py
        │   ├── test_mongodb_connections.ipynb
        │   ├── test_notification_sender.ipynb
        │   └── test_query_db_actions.ipynb
        ├── common_config.yml
        └── data
            ├── __init__.py
            ├── data_ingestion_module.py
            ├── data_ingestion_old.py
            ├── query_subgraph.ipynb
            ├── test_data_ingestion.ipynb
            └── test_data_ingestion_module.ipynb

## Local execution
<details>
<summary>Set up the environment</summary>

This code base has been developed and validated in ```Python 3.9```
*Clone the repo and navigate to the **FraxBot** folder for the next steps
*Create a python virtual environment
```bash
python -m venv bot_venv
source bot_venv/bin/activate
```
*After creating the virtual environment, install the required packages, as listed in *requirements.txt*
```bash
pip install -r requirements.txt
```
</details>
<details>
<summary>Setting up Rasa</summary>

1. To create the bot, go to ```Bot Father```, enter ```/newbot``` and follow the instructions.
2. Add the bot token as **"access_token"** and your bot name as **"verify"** 

* Use Ngrok to expose the local server 5005 (default Rasa server) to the Internet
```bash
ngrok http 5005
```
* Add the Telegram credentials to **credentials.yml**. The URL that Telegram should send messages to will look like ```http://<host>:<port>/webhooks/telegram/webhook```, replacing the **<host>** and **<port>** with the appropriate values from the running Rasa server via Ngrok. 
* Navigate to the **RASA** folder and run Rasa server on one terminal
```bash
rasa run
```
5. Ensure that Rasa action server is up on another terminal
```bash
rasa run actions
```
6. Navigate to **common** folder and run **data_ingestion.py** to extract latest data about Frax
```bash
python data_ingestion.py
```
7. Similarly, from ```common``` folder, run notification_sender.py to send daily updates to users who have subscribed to Frax wallet(s)
```bash
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
</details>
<details> 
<summary>Generating API id and hash for Telegram Application</summary>
1. Log in to your Telegram core: https://my.telegram.org.
2. Go to "API development tools" and fill out the form (Ensure that you are providing a few lines for description. In place of URL, you can add ```https://api.telegram.org/bot{bot_token}/``` or choose to leave it blank)
3. After submitting the form, you will get basic addresses as well as the **api_id** and **api_hash** parameters required for user authorization.

*Note: For the moment each number can only have one api_id connected to it.*
</details>

## Manual Deployment in Azure VM
<details>
<summary>Step 1: Set up an Azure Linux Virtual Machine</summary>
</details>
<details>
<summary>Step 2: Set up the Bot</summary>
* Navigate to the folder where you have cloned the bot repository
</details>
<details>
<summary>Step 3: Deploy the Scheduler for Data Ingestion and Notifications</summary>

* Build the Docker image for the scheduler using the provided scheduler Dockerfile located at ./FraxBot/docker/scheduler_dockerfile.
```bash
docker build -t <image_name> -f <path_of_scheduler_dockerfile> .
```

* Create and start the container in detached mode. Customize the environment variables according to requirements.
```bash
docker run -d -e SCHEDULER_NOTIFICATION_TIME=<time_in_%H:%M_format> -e SCHEDULER_TIME_ZONE=<Continent/City> -e SCHEDULER_TIME_INTERVAL=<time_in_minutes> --name <container_name> <image_name>
```
Replace the placeholders with the following:

**<time_in_%H:%M_format>:** The time (in 24-hrs format) when the bot should send notifications (e.g., "09:30")

**<Continent/City>:** The corresponding time zone for the notifications (e.g., America/New_York)

**<time_in_minutes>:** The time interval in minutes after which the database is refreshed (e.g., 60)

**<container_name>:** The desired name for the Docker container (e.g., my_scheduler_container)

**<image_name>:** The name of the Docker image you built earlier
</details>
<details>
<summary>Step 4: Deploy Rasa Action Server</summary>

* Build the Docker image for running the Rasa action server on port 5055 using the provided action server Dockerfile located at ./FraxBot/docker/action_server_dockerfile.
```bash
docker build -t <image_name> -f <action_server_dockerfile> .
```
Replace **<image_name>** with the desired name for the Docker image, and **<action_server_dockerfile>** with the path to the action server Dockerfile.

* Create and start the container in detached mode with the name **"action_server"**, making sure to map the host port to port 5055 (default port for rasa action server)
```bash
docker run -d -p <host_port>:5055 --name action_server <image_name>
```
Replace **<host_port>** with the desired port number on the host machine where Rasa action server will be accessed.

_Check if the action server is up by visiting ```http://<azure_vm_ip>:<port>```, where "azure_vm_ip" is the IP address of the Azure Linux VM, and "port" is the host port specified in the previous command.
_
</details>
<details>
<summary>Step 5: Deploy Ngrok</summary>

These steps will deploy Ngrok on Docker, enabling access to and interaction with the Rasa Core service from the host machine.

* Create a Docker network that will connect the Rasa Core to Ngrok.
```bash
docker network create <network_name>
```
Replace **<network_name>** with a suitable name for the network.

* Create and start a container using the pre-built Ngrok Docker image, ***ngrok/ngrok:alpine***. This container will forward HTTP traffic from its port 5005 to the host system's port, where the Rasa Core service will be running. The ```-d``` flag runs the container in the background, and the ```--rm``` flag ensures the container is removed automatically after stopping.
```bash
docker run --rm --detach -e NGROK_AUTHTOKEN=$AUTH_TOKEN --network <network_name> --name ngrok ngrok/ngrok:alpine http rasa_core:5005
```
Replace **<network_name>** with the name of the Docker network created in the previous step. Ensure that the **AUTH_TOKEN** variable is defined with the Ngrok authentication token before running this command.

* Obtain the name of the tunneled HTTPS host from Ngrok by ```visiting https://dashboard.ngrok.com/tunnels/agents```

</details>
<details>
<summary>Step 6: Deploy Rasa Core</summary>

These steps will deploy Rasa Core and connect it with the Ngrok container, allowing external access to the Rasa Core service via the tunneled HTTPS host. The action server will also be linked to Rasa Core for handling custom actions.

* Add the tunneled HTTPS host obtained from Ngrok dashboard to the **credentials.yml**. This allows Rasa Core to connect with external services securely.

* In the **endpoints.yml**, set the "action_endpoint" to ```http://<azure_ip>:5055/webhook```. This tells Rasa Core where to find the action server for handling custom actions.

* Build the Docker image for running Rasa Core on port 5005. Use the provided Rasa Dockerfile located at ./FraxBot/docker/rasa_dockerfile. If you want to train a new Rasa model, pass "true" as build argument "TRAIN"; otherwise, pass "false".
```bash
docker build --build-arg TRAIN="false" -t <image_name> -f <path_of_rasa_dockerfile> .
```
Replace **<image_name>** with the desired name for the Docker image and **<path_of_rasa_dockerfile>** with the path to the Rasa Dockerfile.

* Create and start a container in detached mode, ensuring to map the host port to port 5005 (the default port for Rasa Core). Make sure Rasa is attached to the Docker network with Ngrok. Set the name of the Rasa Core container to "rasa_core".
```bash
docker run -d -p <host_port>:5005 -v .:$(pwd)/src/RASA --network <network_name> --name rasa_core <image_name>
```
Replace **<host_port>** with the port number on the host machine where you want to access Rasa Core, <network_name> with the name of the Docker network you created for Ngrok, and <image_name> with the name of the Docker image you built in the previous step.

</details>

