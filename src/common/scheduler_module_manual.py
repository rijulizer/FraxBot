import os
import schedule
import time
import yaml

from data import DataIngestion
from common import mongodb_connect, send_notification
python_path = os.environ.get('PYTHONPATH')


if __name__=="__main__":
    #Read config time and time zone
    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)
    #Set default time values from config
    try:
        print("Manually Calling Data Ingestion...")
        DataIngestion()
        print("Manually Calling Send Notification...")
        send_notification()
    except Exception as error:
        print("An exception occurred:", type(error).__name__)