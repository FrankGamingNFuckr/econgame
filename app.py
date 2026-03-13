from flask import Flask, render_template, request, jsonify, session
import random
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Game state storage (in-memory for now)
game_state = {}

# Work messages (random selection)
WORK_MESSAGES = [
    "You fixed some fences and made ${amount}",
    "You mowed lawns all day and earned ${amount}",
    "You helped move furniture and made ${amount}",
    "You washed cars and brought home ${amount}",
    "You did some freelance work and earned ${amount}",
    "You sold handmade crafts and made ${amount}",
]

GOV_MESSAGES = [
    "You worked for the TSA screening luggage",
    "You filed paperwork at the DMV",
    "You inspected buildings for the city",
    "You worked as a postal worker",
    "You processed permits at City Hall",
    "You worked road maintenance for the state",
]

TAX_RATES = [15, 18, 22, 25, 28]  # Different tax rates

@app.route('/')
def index():
    # Initialize player session
    if 'player_id' not in session:
        session['player_id'] = secrets.token_hex(8)
        game_state[session['player_id']] = {
            'money': 0,
            'turns_left': 10,
            'total_turns': 10,
            'name': f"Player_{session['player_id'][:6]}"
        }
    return render_template('index.html')

@app.route('/get_state')
def get_state():
    player_id = session.get('player_id')
    if player_id in game_state:
        return jsonify(game_state[player_id])
    return jsonify({'error': 'No player found'}), 404

@app.route('/work', methods=['POST'])
def work():
    player_id = session.get('player_id')
    if player_id not in game_state:
        return jsonify({'error': 'No player found'}), 404
    
    player = game_state[player_id]
    
    if player['turns_left'] <= 0:
        return jsonify({'error': 'No turns left!'}), 400
    
    # Random amount earned (between $50-$200)
    amount = random.randint(50, 200)
    
    # Select random message
    message = random.choice(WORK_MESSAGES).replace('{amount}', str(amount))
    
    # Update player state
    player['money'] += amount
    player['turns_left'] -= 1
    
    return jsonify({
        'message': message,
        'amount': amount,
        'money': player['money'],
        'turns_left': player['turns_left']
    })

@app.route('/workgov', methods=['POST'])
def workgov():
    player_id = session.get('player_id')
    if player_id not in game_state:
        return jsonify({'error': 'No player found'}), 404
    
    player = game_state[player_id]
    
    if player['turns_left'] <= 0:
        return jsonify({'error': 'No turns left!'}), 400
    
    # Random amount earned (government pays more: $150-$350)
    gross_amount = random.randint(150, 350)
    tax_rate = random.choice(TAX_RATES)
    net_amount = int(gross_amount * (1 - tax_rate / 100))
    
    # Select random message
    job_desc = random.choice(GOV_MESSAGES)
    message = f"{job_desc} and made ${gross_amount} but taxes apply at {tax_rate}% so you only brought home ${net_amount}"
    
    # Update player state
    player['money'] += net_amount
    player['turns_left'] -= 1
    
    return jsonify({
        'message': message,
        'gross_amount': gross_amount,
        'tax_rate': tax_rate,
        'net_amount': net_amount,
        'money': player['money'],
        'turns_left': player['turns_left']
    })

@app.route('/reset', methods=['POST'])
def reset():
    player_id = session.get('player_id')
    if player_id in game_state:
        game_state[player_id] = {
            'money': 0,
            'turns_left': 10,
            'total_turns': 10,
            'name': game_state[player_id]['name']
        }
        return jsonify(game_state[player_id])
    return jsonify({'error': 'No player found'}), 404

if __name__ == '__main__':
    # For playing with friends, use host='0.0.0.0' to allow network access
    # WARNING: Only use this on a trusted local network!
    app.run(debug=True, host='127.0.0.1', port=5000)
    # To allow friends on same network: app.run(debug=False, host='0.0.0.0', port=5000)
