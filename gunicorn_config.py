import os
from database import init_db

init_db()

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
