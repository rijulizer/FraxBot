import sys


import os
import schedule
import time
import yaml
# import pytz
from datetime import datetime,timedelta
from pytz import timezone

from data import DataIngestion
from common import mongodb_connect, send_notification
python_path = os.environ.get('PYTHONPATH')


if __name__=="__main__":
    #Read config time and time zone
    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)
    #Set default time values from config
    scheduler_notif_time = config['scheduler']['notification']['time']
    scheduler_time_zone = config['scheduler']['notification']['time_zone']
    scheduler_time_interval = int(config['scheduler']['data_ingestion']['time_interval'])
    #Set time values according to input while running docker
    scheduler_notif_time = os.environ.get('SCHEDULER_NOTIFICATION_TIME', scheduler_notif_time)
    scheduler_time_zone = os.environ.get('SCHEDULER_TIME_ZONE', scheduler_time_zone)
    scheduler_time_interval = int(os.environ.get('SCHEDULER_TIME_INTERVAL', scheduler_time_interval))

    print(f"SCHEDULER_NOTIFICATION_TIME {scheduler_notif_time}")
    print(f"SCHEDULER_TIME_ZONE {scheduler_time_zone}")
    print(f"SCHEDULER_TIME_INTERVAL {scheduler_time_interval}")

    try:
        print("Calling main function in scheduler module...")
        
        s1 = schedule.every(scheduler_time_interval).minutes.do(DataIngestion)

        # notification_time = time_conversion(scheduler_notif_time)
        # print("Notification time: ",notification_time)

        print("="*50)
        # Parse the input string to a datetime object using the given format
        scheduler_notif_time = datetime.strptime(scheduler_notif_time, "%H:%M").strftime("%H:%M:%S")
        s2 = schedule.every().day.at(scheduler_notif_time, timezone(scheduler_time_zone)).do(send_notification)

        print(f"Data ingestion scheduler will run again at {s1.next_run} (UTC)")
        print(f"Notification scheduler will run again at {s2.next_run} (UTC)")
        
        # Start an infinite loop to run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(2)

    except Exception as error:
        print("An exception occurred in SCHEDULER MODULE:", type(error).__name__)