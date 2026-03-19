"""
Simple BMS monitor — checks PVR Inorbit Cyberabad for
Dhurandhar PXL show on 22 March and notifies via email.
Uses Selenium to load the page like a real browser (BMS blocks plain requests).
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ============ CONFIGURE THESE ============
EVENT_URL = "https://in.bookmyshow.com/cinemas/hyderabad/pvr-inorbit-cyberabad/buytickets/PIIC/20260322"
MOVIE_NAME = "dhurandhar"
SCREEN_TYPE = "pxl"
SEATS_NEEDED = 2
CHECK_INTERVAL = 45  # seconds between checks (for loop mode)

# Email — reads from env vars (for GitHub Actions) or falls back to defaults
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hemanthchintada@gmail.com")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "ovse jibs phoe estl")
RECEIVER_EMAILS = os.environ.get("RECEIVER_EMAILS", "hemanthchintada@gmail.com,anumulakarthikreddy12345@gmail.com").split(",")
# =========================================


def create_driver():
    """Create a headless Chrome browser."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=opts)


def check_shows(driver):
    """Check BMS page for Dhurandhar PXL show."""
    try:
        driver.get(EVENT_URL)
        time.sleep(5)  # wait for JS to render
        text = driver.page_source.lower()
    except Exception as e:
        return False, f"Page fetch failed: {e}"

    if MOVIE_NAME not in text:
        return False, "Dhurandhar not listed yet."

    has_pxl = SCREEN_TYPE in text

    if not has_pxl:
        return False, "Dhurandhar found but PXL screen not listed."

    if "sold out" in text or "housefull" in text:
        return False, "Show found but sold out."

    return True, "Dhurandhar PXL show available!"


def send_email(details):
    """Send notification email."""
    msg = MIMEText(
        f"Dhurandhar PXL tickets at PVR Inorbit Cyberabad!\n\n"
        f"Screen: PXL, 22 March 2026\n"
        f"Seats needed: {SEATS_NEEDED}\n\n"
        f"Book now: {EVENT_URL}\n\n"
        f"{details}"
    )
    msg["Subject"] = "BMS: Dhurandhar PXL Tickets Available!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            s.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        print(">>> EMAIL SENT!")
    except Exception as e:
        print(f">>> Email failed: {e}")


def main():
    mode = os.environ.get("RUN_MODE", "loop")  # "once" for GitHub Actions, "loop" for local

    print("Monitoring: Dhurandhar | PXL | PVR Inorbit Cyberabad | 22 Mar 2026")

    driver = create_driver()
    try:
        if mode == "once":
            # Single check (GitHub Actions)
            available, details = check_shows(driver)
            print(f"[Check] {details}")
            if available:
                print("*** TICKETS AVAILABLE! ***")
                send_email(details)
        else:
            # Loop mode (local laptop)
            print(f"Checking every {CHECK_INTERVAL}s. Press Ctrl+C to stop.\n")
            while True:
                available, details = check_shows(driver)
                print(f"[Check] {details}")
                if available:
                    print("\n*** TICKETS AVAILABLE! ***")
                    send_email(details)
                    print("Waiting 5 min before re-checking...")
                    time.sleep(300)
                else:
                    time.sleep(CHECK_INTERVAL)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
