import schedule
import time
from pytz import timezone
from datetime import datetime
import os

scheduler_notif_time = os.environ.get('SCHEDULER_NOTIFICATION_TIME')
print(f"[l1]SCHEDULER_NOTIFICATION_TIME {scheduler_notif_time}")
scheduler_notif_time = datetime.strptime(scheduler_notif_time, "%H:%M").strftime("%H:%M:%S")
print(f"[l2]SCHEDULER_NOTIFICATION_TIME {scheduler_notif_time}")
     
def my_task():
    # Replace this function with the task you want to execute at the specified time
    print("Task is executed at:", time.strftime('%H:%M:%S'))

def schedule_task():
    # Replace '12:34' with the HH:MM time you want the task to run
    schedule.every().day.at(scheduler_notif_time, timezone("Asia/Kolkata")).do(my_task)

# Call the scheduling function
schedule_task()

# Keep the script running to execute scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)



# import os
# import schedule
# import time
# import yaml
# # import pytz
# from datetime import datetime,timedelta
# from pytz import timezone

# from data import DataIngestion
# from common import mongodb_connect, send_notification
# python_path = os.environ.get('PYTHONPATH')


# def time_conversion(scheduler_time):
#     '''Function to convert UTC time to time mentioned in common_config according to time zone '''
#     ist_tz = pytz.timezone(scheduler_time_zone)
#     # Get the current UTC time
#     utc_now = datetime.utcnow()
#     # Convert UTC time to IST time
#     ist_now = utc_now.astimezone(ist_tz)
#     hms_modified = [0,0,0,0]
#     hms = scheduler_time.split(":")
    
#     for i in range(len(hms)):
#         hms_modified[i] = int(hms[i])

#     data_ingestion_time = ist_now.replace(hour=hms_modified[0], minute=hms_modified[1], second=hms_modified[2], microsecond=hms_modified[3])
    
#     print(data_ingestion_time)

#     return data_ingestion_time

# if __name__=="__main__":
#     #Read config time and time zone
#     config_stream = open(python_path+os.sep+"common_config.yml",'r')
#     config = yaml.load(config_stream, Loader=yaml.BaseLoader)
#     #Set default time values from config
#     scheduler_notif_time = config['scheduler']['notification']['time']
#     scheduler_time_zone = config['scheduler']['notification']['time_zone']
#     scheduler_time_interval = int(config['scheduler']['data_ingestion']['time_interval'])
#     #Set time values according to input while running docker
#     scheduler_notif_time = os.environ.get('SCHEDULER_NOTIFICATION_TIME', scheduler_notif_time)
#     scheduler_time_zone = os.environ.get('SCHEDULER_TIME_ZONE', scheduler_time_zone)
#     scheduler_time_interval = int(os.environ.get('SCHEDULER_TIME_INTERVAL', scheduler_time_interval))

#     print(f"SCHEDULER_NOTIFICATION_TIME {scheduler_notif_time}")
#     print(f"SCHEDULER_TIME_ZONE {scheduler_time_zone}")
#     print(f"SCHEDULER_TIME_INTERVAL {scheduler_time_interval}")

#     try:
#         print("Calling main function in scheduler module...")
        
#         s1 = schedule.every(scheduler_time_interval).minutes.do(DataIngestion)

#         # notification_time = time_conversion(scheduler_notif_time)
#         # print("Notification time: ",notification_time)

#         print("="*50)
#         # Parse the input string to a datetime object using the given format
#         scheduler_notif_time = datetime.strptime(scheduler_notif_time, "%H:%M").strftime("%H:%M:%S")
#         s2 = schedule.every().day.at(scheduler_notif_time, timezone(scheduler_time_zone)).do(send_notification)

#         print(f"Data ingestion scheduler will run again at {s1.next_run} (UTC)")
#         print(f"Notification scheduler will run again at {s2.next_run} (UTC)")
        
#         # Start an infinite loop to run the scheduler
#         while True:
#             schedule.run_pending()
#             time.sleep(2)

#     except Exception as error:
#         print("An exception occurred:", type(error).__name__)

src/common/scheduler_module.py