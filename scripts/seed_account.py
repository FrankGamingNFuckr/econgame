import json
import secrets
import hashlib
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('game_data')
ACCOUNTS = DATA_DIR / 'accounts.json'
USERS = DATA_DIR / 'users.json'

username = 'devuser'
email = 'dev@example.com'
password = 'devpass'

# Load or init
if ACCOUNTS.exists():
    accounts = json.loads(ACCOUNTS.read_text())
else:
    accounts = {}

if USERS.exists():
    users = json.loads(USERS.read_text())
else:
    users = {}

# Create salt and hash
salt = secrets.token_hex(16)
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

accounts[username] = {
    'username': username,
    'email': email,
    'salt': salt,
    'password_hash': password_hash,
    'created_at': datetime.now().isoformat()
}

# Create user entry with starter balances
users[username] = {
    'username': username,
    'createdAccount': True,
    'accountType': 'checking',
    'checking': 10000,
    'savings': 5000,
    'pockets': 2000,
    'emergency': 1000,
    'businesses': [],
    'stocks': {},
    'crypto': {},
    'inventory': {},
    'loans': {
        'regular': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'missedDays': 0, 'inCollections': False, 'startDate': None},
        'stock': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'inCollections': False, 'startDate': None}
    },
    'cooldowns': {},
    'jailedUntil': 0,
    'arrests': 0,
    'hasInsurance': False,
    'totalRobbedFrom': 0,
    'totalRobbedOthers': 0,
    'lastWorkDay': None,
    'createdAt': datetime.now().isoformat()
}

# Save
ACCOUNTS.write_text(json.dumps(accounts, indent=2))
USERS.write_text(json.dumps(users, indent=2))

print('Seeded account:', username)
print('Password:', password)
