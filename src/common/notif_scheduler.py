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

    new_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])
    # notification_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])
    print(new_time)

    return new_time

def convert_to_utc(time_str, from_timezone):
    # Define the time zone for the given time

    print("\n","-"*50)
    print(f"Time in utc noe - {datetime.utcnow()}")
    print("\n","-"*50)

    from_tz = pytz.timezone(from_timezone)

    # Parse the time string to a datetime object
    datetime_obj = datetime.strptime(time_str, '%H:%M')

    # Attach the time zone information to the datetime object
    from_time = from_tz.localize(datetime_obj)

    # Convert the time to UTC
    utc_time = from_time.astimezone(pytz.utc)

    return utc_time

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
    print("*"*50)
    print(os.environ['SCHEDULER_NOTIFICATION_TIME'])
    print(os.environ['SCHEDULER_TIME_ZONE'])
    print(os.environ['PYTHONPATH'])
    print(os.environ['MONGO_CERTIFICATE_PATH'])
    print("*"*50)
    config_stream = open(python_path+os.sep+"common_config.yml",'r')
    config = yaml.load(config_stream, Loader=yaml.BaseLoader)

    scheduler_time = config['scheduler']['notification']['time']
    scheduler_time_zone = config['scheduler']['notification']['time_zone']
    
    scheduler_time = os.environ.get('SCHEDULER_NOTIFICATION_TIME', scheduler_time)
    scheduler_time_zone = os.environ.get('SCHEDULER_TIME_ZONE', scheduler_time_zone)

    print("Calling main function in scheduler module...")

    # notification_time = time_conversion(scheduler_time)
    # print("Notification time: ",notification_time.strftime("%H:%M:%S"))
    notif_time = convert_to_utc(scheduler_time,scheduler_time_zone)
    print(f"You will get notifications at - {notif_time.strftime("%H:%M:%S")}")
    
    # try:
    # s = schedule.every().day.at(notification_time.strftime("%H:%M:%S"), scheduler_time_zone).do(dummy_notif)
    s = schedule.every().day.at(notif_time.strftime("%H:%M:%S")).do(dummy_notif)
    print("="*50)

    # s2 = schedule.every().day.at(notification_time.strftime("%H:%M:%S:%f"), scheduler_time_zone).do(dummy_notif)
    print("Notification scheduler will run again at -",s.next_run)

    while True:
        schedule.run_pending()
        time.sleep(1)

    # except Exception as error:
    #     print("An exception occurred:", type(error).__name__)