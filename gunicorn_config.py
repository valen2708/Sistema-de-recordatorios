import os
from database import init_db
from scheduler import iniciar_scheduler

init_db()
iniciar_scheduler()

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
