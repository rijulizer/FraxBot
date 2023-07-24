import sys

# sys.path.append('d:\\FRAX_project\\FraxBot\\src\\')
# sys.path.append(r'D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src')

import os
import schedule
import time
import yaml
import pytz
from datetime import datetime,timedelta

from data import DataIngestion
from common import mongodb_connect, send_notification
python_path = os.environ.get('PYTHONPATH')


def time_conversion(scheduler_time):
    '''Function to convert UTC time to time mentioned in common_config according to time zone '''
    # print("Inside time conversion function...")
    ist_tz = pytz.timezone(scheduler_time_zone)
    # print("Inside time conversion function... (2)")

    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Convert UTC time to IST time
    ist_now = utc_now.astimezone(ist_tz)
    # print("Inside time conversion function... (3)")

    hms_modified = [0,0,0,0]
    hms = scheduler_time.split(":")
    # print("Hour-minutes-second: ",hms)
    
    for i in range(len(hms)):
        hms_modified[i] = int(hms[i])
    # print("Hour-minutes-second modified: ",hms_modified)

    data_ingestion_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])
    # notification_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])
    print(data_ingestion_time)#,notification_time)

    return data_ingestion_time#scheduler_time

if __name__=="__main__":
    #Read config time and time zone
    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)

    scheduler_time = config['scheduler']['time']
    scheduler_time_zone = config['scheduler']['time_zone']
    scheduler_time = os.environ.get('SCHEDULER_TIME', scheduler_time)
    scheduler_time_zone = os.environ.get('SCHEDULER_TIME_ZONE', scheduler_time_zone)
    try:
        print("Calling main function in scheduler module...")
        
        #Function to convert UTC time to time mentioned in common_config according to time zone
        data_ingestion_time = time_conversion(scheduler_time)
        print("Data ingestion time: ",data_ingestion_time)#.strftime("%H:%M"))
        notification_time = data_ingestion_time+timedelta(minutes=30) #make customisable
        print("Notification time: ",notification_time)
        
        s1 = schedule.every().day.at(data_ingestion_time.strftime("%H:%M:%S"), scheduler_time_zone).do(DataIngestion)

        print("="*50)

        s2 = schedule.every().day.at(notification_time.strftime("%H:%M:%S"), scheduler_time_zone).do(send_notification)
        # , user_notifications=user_notifications, subscription=subscription)

        print("Data ingestion scheduler will run again at -",s1.next_run)
        print("Notification scheduler will run again at -",s2.next_run)
        
        # Start an infinite loop to run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(2)

    except Exception as error:
        print("An exception occurred:", type(error).__name__)