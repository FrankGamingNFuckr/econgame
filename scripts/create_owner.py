import json
import secrets
import hashlib
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('game_data')
OWNER_FILE = DATA_DIR / 'owner.json'

username = 'FrixxTVOwner'
# Generate a secure random password (urlsafe)
password = secrets.token_urlsafe(24)

salt = secrets.token_hex(16)
# Use the same PBKDF2 iterations as the app's `hash_password` (100000)
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

owner = {
    'username': username,
    'salt': salt,
    'password_hash': password_hash,
    'created_at': datetime.now().isoformat()
}

OWNER_FILE.write_text(json.dumps(owner, indent=2))

print('Owner created:')
print('  username:', username)
print('  password:', password)
print('Owner credentials saved to', OWNER_FILE)
print('Please copy the password somewhere secure. This is the only time it will be displayed.')
