import json
import re
from pathlib import Path

DATA_DIR = Path('game_data')
ACCOUNTS_FILE = DATA_DIR / 'accounts.json'
USERS_FILE = DATA_DIR / 'users.json'

patterns = [
    r'^tester\d*$',
    r'^devuser$',
    r'^advisor_test$',
    r'^verify_',
    r'^resend_',
    r'^risk_',
    r'^riskdetail_',
    r'^illegal_',
    r'^noloan_',
    r'^raidhist_',
]
explicit = {'Gringo77', 'OtherUser', 'null'}


def is_test(name: str) -> bool:
    if name in explicit:
        return True
    return any(re.search(pattern, name) for pattern in patterns)


accounts = json.loads(ACCOUNTS_FILE.read_text())
users = json.loads(USERS_FILE.read_text())

removed_accounts = [key for key in list(accounts.keys()) if is_test(key)]
for key in removed_accounts:
    accounts.pop(key, None)

removed_users = [key for key in list(users.keys()) if is_test(key)]
for key in removed_users:
    users.pop(key, None)

ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))
USERS_FILE.write_text(json.dumps(users, indent=2))

print('REMOVED_ACCOUNTS', sorted(removed_accounts))
print('REMOVED_USERS', sorted(removed_users))
print('REMAINING_ACCOUNTS', sorted(accounts.keys()))
print('REMAINING_USERS_COUNT', len(users))
