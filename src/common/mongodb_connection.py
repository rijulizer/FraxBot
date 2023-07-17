import pymongo
from pymongo import MongoClient
import yaml
import os

def mongodb_connect():
    """Connects to mongodb atlas and returns different collections"""

    print("Initializing configurations...")
    # Load config file
    config_stream = open("../common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)

    mongoDb_uri = config['mongo_db']['uri']

    print("Connecting to MongoDB Client...")
    client = MongoClient(mongoDb_uri,
                        tls=True,
                        tlsCertificateKeyFile="../../mongodb_user_certificate.pem")

    print("Getting data collections...")

    db = client[config['mongo_db']['database']]
    pairs = db[config['mongo_db']['pairs_schema']]
    telegram_metadata = db[config['mongo_db']['telegram_metadata_schema']]
    wallet_positions = db[config['mongo_db']['wallets_schema']]
    subscription = db[config['mongo_db']['subscription_schema']]
    
    return (db, telegram_metadata, subscription, pairs, wallet_positions)
