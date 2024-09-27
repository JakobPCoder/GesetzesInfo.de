from celery import shared_task
import time

@shared_task
def long_running_task():
    print("Task Started")
    time.sleep(5)  # Simulate a long-running task
    print("Task Finished")
    return "Task Completed"