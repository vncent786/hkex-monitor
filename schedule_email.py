import schedule
import time
from send_test_email import main

def job():
    print("Sending email...")
    main()

# Schedule the job at 1:26 AM daily
schedule.every().day.at("01:26").do(job)

print("Scheduler started. Waiting for the scheduled time...")

while True:
    schedule.run_pending()
    time.sleep(1)