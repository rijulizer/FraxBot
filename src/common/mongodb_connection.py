import pymongo
from pymongo import MongoClient
import yaml
import os
python_path = os.environ.get('PYTHONPATH')
# python_path = r"D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src"
def mongodb_connect():
    """Connects to mongodb atlas and returns different collections"""

    print("Initializing configurations...")
    # Load config file
    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)

    mongoDb_uri = config['mongo_db']['uri']

    print("Connecting to MongoDB Client...")
    client = MongoClient(mongoDb_uri,
                        tls=True,
                        tlsCertificateKeyFile=os.getcwd()+os.sep+"mongodb_user_certificate.pem")
                        # os.getcwd()+os.sep+"mongodb_user_certificate.pem")

    print("Getting data collections...")

    db = client[config['mongo_db']['database']]
    pairs = db[config['mongo_db']['pairs_schema']]
    user_positions = db[config['mongo_db']['user_positions_schema']]
    user_notifications = db[config['mongo_db']['user_notifications_schema']]
    telegram_metadata = db[config['mongo_db']['telegram_metadata_schema']]
    subscription = db[config['mongo_db']['subscription_schema']]
    
    return (db, pairs, user_positions, user_notifications, telegram_metadata, subscription)

if __name__ == '__main__':
    # try:
        # print("Initializing Data Ingestion \n...")
#         # connect MDB collectioons
    (db, pairs, user_positions, user_notifications, telegram_metadata, subscription) = mongodb_connect()
#         # manually run 
        # data_ingest = DataIngestion()

    # except Exception as error:
        # print("An exception occurred:", type(error).__name__)