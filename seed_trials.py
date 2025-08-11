import os
from db import init_db, count_trials, save_trial_to_db
from datetime import datetime, timedelta

DEFAULT_EMAIL = os.getenv("SEED_TRIAL_EMAIL", "demo@carbon.com")
DEFAULT_NAME = os.getenv("SEED_TRIAL_NAME", "Demo User")
DEFAULT_KEY = os.getenv("SEED_TRIAL_KEY", "CARBON-DEMO123456")

init_db()

if count_trials() == 0:
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    trial_data = {
        "trial_key": DEFAULT_KEY,
        "full_name": DEFAULT_NAME,
        "email": DEFAULT_EMAIL,
        "company": "DemoCorp",
        "role": "Demo",
        "country": "DemoLand",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "queries_used": 0,
        "queries_limit": 100,
        "registration_date": start_date.isoformat(),
        "status": "active"
    }
    save_trial_to_db(trial_data)
    print(f"[SEED] Inserted default trial: {DEFAULT_KEY} ({DEFAULT_EMAIL})")
else:
    print("[SEED] Trials already exist, skipping seeding.")
