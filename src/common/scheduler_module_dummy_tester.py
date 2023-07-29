import sys
import os
print("*"*50)
print('-------------------------------------------ENVIRONMENT VARIABLES---------------------------------------')
print("Running Dummy Tester ....\n")
print(os.environ['SCHEDULER_NOTIFICATION_TIME'])
print(os.environ['SCHEDULER_TIME_ZONE'])
print(os.environ['SCHEDULER_TIME_INTERVAL'])
print(os.environ['PYTHONPATH'])
print(os.environ['MONGO_CERTIFICATE_PATH'])
print("*"*50)
# sys.path.append('d:\\FRAX_project\\FraxBot\\src\\')
# sys.path.append(r'D:\Telegram_Bot(dummy)\Rasa_enhancements_final\FraxBot\src')
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
    ist_tz = pytz.timezone(scheduler_time_zone)

    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Convert UTC time to IST time
    ist_now = utc_now.astimezone(ist_tz)

    hms_modified = [0,0,0,0]
    hms = scheduler_time.split(":")
    
    for i in range(len(hms)):
        hms_modified[i] = int(hms[i])

    data_ingestion_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])

    print(data_ingestion_time)

    return data_ingestion_time

def dummy_notif():
    print("="*50)
    print(datetime.now())
    print("Hello Mic testing...")
    print("="*50)
    print(datetime.now())
    time.sleep(5)
    print("="*50)
    return

if __name__=="__main__":
    #Read config time and time zone

    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)

    scheduler_time = config['scheduler']['notification']['time']
    scheduler_time_zone = config['scheduler']['notification']['time_zone']
    scheduler_time_interval = int(config['scheduler']['data_ingestion']['time_interval'])
    
    scheduler_time = os.environ.get('SCHEDULER_NOTIFICATION_TIME', scheduler_time)
    scheduler_time_zone = os.environ.get('SCHEDULER_TIME_ZONE', scheduler_time_zone)
    time_interval = int(os.environ.get('SCHEDULER_TIME_INTERVAL', scheduler_time_interval))

    print("Calling main function in scheduler module...")
    
    s1 = schedule.every(scheduler_time_interval).minutes.do(DataIngestion)

    notification_time = time_conversion(scheduler_time)
    print("Notification time: ",notification_time.strftime("%H:%M:%S"))

    print("="*50)

    s2 = schedule.every().day.at(notification_time.strftime("%H:%M:%S"), scheduler_time_zone).do(dummy_notif)

    print("Data ingestion scheduler will run again at -",s1.next_run)
    print("Notification scheduler will run again at -",s2.next_run)
    
    while True:
        schedule.run_pending()
        time.sleep(2)