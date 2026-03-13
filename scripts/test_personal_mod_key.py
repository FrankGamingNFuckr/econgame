import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app_auth import app

c = app.test_client()

# Simulate owner session to call owner-only API
with c.session_transaction() as session:
    session['is_owner'] = True
    session['username'] = 'FrixxTV'
    session['player_id'] = 'FrixxTV'

resp_gen = c.post('/api/admin_keys/generate', json={
    'assigned_username': 'gringo77',
    'description': 'Personal key for gringo77'
})
json_gen = resp_gen.get_json()
key = json_gen['key']

resp_ok = c.post('/moderator-login', json={
    'username': 'Gringo77',
    'admin_key': key
})

resp_bad = c.post('/moderator-login', json={
    'username': 'OtherUser',
    'admin_key': key
})

print('GEN', resp_gen.status_code, json_gen.get('assigned_username'))
print('MOD_OK', resp_ok.status_code, resp_ok.get_json())
print('MOD_BAD', resp_bad.status_code, resp_bad.get_json())
