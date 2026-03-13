import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app_auth import app

client = app.test_client()

username = 'advisor_test'
email = 'advisor_test@example.com'
password = 'password123'

# Register (idempotent-ish)
client.post('/register', json={'username': username, 'email': email, 'password': password})

# Force verify for test login
with open('game_data/accounts.json', 'r') as file:
    accounts = json.load(file)
if username in accounts:
    accounts[username]['email_verified'] = True
with open('game_data/accounts.json', 'w') as file:
    json.dump(accounts, file, indent=2)

login = client.post('/login', json={'username': username, 'password': password})
print('LOGIN', login.status_code, login.get_json())

advisors = client.get('/api/advisors')
print('ADVISORS', advisors.status_code)

set_advisor = client.post('/api/advisor/select', json={'advisor': 'miranda'})
print('SET_ADVISOR', set_advisor.status_code, set_advisor.get_json())

work = client.post('/api/work')
print('WORK', work.status_code, work.get_json())

notifications = client.get('/api/notifications')
notif_json = notifications.get_json()
print('NOTIFICATIONS', notifications.status_code, 'unread=', notif_json.get('unread'))
