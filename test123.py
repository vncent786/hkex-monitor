import os

SMTP_PASSWORD = os.getenv("HKEX_EMAIL_PASS")     # App password from env

print(SMTP_PASSWORD)