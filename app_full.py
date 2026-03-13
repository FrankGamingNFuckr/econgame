from flask import Flask, render_template, request, jsonify, session
import random
import secrets
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint

# Expose routes as a Blueprint so this module can be registered into the
# main application in `app_auth.py`.
bp = Blueprint('full', __name__)

ADVISOR_PROFILES = {
    'none': {
        'name': 'No Advisor',
        'description': 'No modifiers applied.'
    },
    'helper': {
        'name': 'Helper Advisor',
        'description': 'Provides guidance notifications only (no gameplay modifiers).'
    },
    'miranda': {
        'name': 'Miranda (Lawyer)',
        'description': 'Better legal protection, but slower growth/income.'
    },
    'gina': {
        'name': 'Gina (Hotel Owner)',
        'description': 'Business gains are stronger, stock trading is less effective.'
    },
    'katie': {
        'name': 'Katie (Hollywood Star)',
        'description': 'Lifestyle is more expensive.'
    },
    'rivera': {
        'name': 'Rivera (Criminal)',
        'description': 'Lower chance of getting caught in crime actions, but penalties are harsher when caught.'
    }
}

ILLEGAL_BUSINESS_TYPES = {
    'black_market': {
        'name': 'Black Market Stall',
        'startup_cost': 120000,
        'min_payout': 12000,
        'max_payout': 28000,
        'base_raid_chance': 0.20,
    },
    'counterfeit_lab': {
        'name': 'Counterfeit Lab',
        'startup_cost': 180000,
        'min_payout': 18000,
        'max_payout': 42000,
        'base_raid_chance': 0.24,
    },
}

# Data directories
DATA_DIR = Path('game_data')
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / 'users.json'
BUSINESSES_FILE = DATA_DIR / 'businesses.json'
CONFIG_FILE = DATA_DIR / 'config.json'
STOCKS_FILE = DATA_DIR / 'stocks.json'
CRYPTO_FILE = DATA_DIR / 'crypto.json'
SHOP_FILE = DATA_DIR / 'shop.json'

# ==================== DATA LOADING/SAVING ====================

def load_json(file, default):
    if file.exists():
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file, data):
    # Ensure parent directory exists
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    return load_json(USERS_FILE, {})

def save_users(data):
    save_json(USERS_FILE, data)

def load_businesses():
    return load_json(BUSINESSES_FILE, {})

def save_businesses(data):
    save_json(BUSINESSES_FILE, data)

def load_config():
    defaults = {
        'emergencyCap': 250000,
        'taxRate': 0.1,
        'highIncomeRate': 0.25,
        'inflation': 0.02,
        'govTaxPercent': 21,
        'govShutdown': False,
        'recession': False,
        'depression': False,
        'interestRate': 3,
        'baseInterestRate': 3,
        'centralBankVault': 1000000,
        'lastHourlyUpdate': None,
        'strikeMode': False
    }
    data = load_json(CONFIG_FILE, defaults)
    for k, v in defaults.items():
        if k not in data:
            data[k] = v
    return data

def save_config(data):
    save_json(CONFIG_FILE, data)

def load_stocks():
    defaults = {
        'TECH': {'name': 'TechCorp', 'price': 100, 'history': []},
        'BANK': {'name': 'MegaBank', 'price': 150, 'history': []},
        'ENERGY': {'name': 'PowerCo', 'price': 80, 'history': []},
        'RETAIL': {'name': 'ShopMax', 'price': 50, 'history': []},
        'PHARMA': {'name': 'HealthPlus', 'price': 200, 'history': []},
    }
    return load_json(STOCKS_FILE, defaults)

def save_stocks(data):
    save_json(STOCKS_FILE, data)

def load_crypto():
    defaults = {
        'BTC': {'name': 'Bitcoin', 'price': 50000, 'history': []},
        'ETH': {'name': 'Ethereum', 'price': 3000, 'history': []},
        'DOGE': {'name': 'Dogecoin', 'price': 0.25, 'history': []},
    }
    return load_json(CRYPTO_FILE, defaults)

def save_crypto(data):
    save_json(CRYPTO_FILE, data)

def load_shop():
    defaults = {
        'apartment': {'name': 'Apartment', 'price': 50000, 'maxOwn': 1, 'rentHourly': 550, 'type': 'housing'},
        'house': {'name': 'House', 'price': 150000, 'maxOwn': 8, 'rentDaily': 2500, 'type': 'housing'},
        'mansion': {'name': 'Mansion', 'price': 500000, 'maxOwn': 3, 'rentDaily': 25000, 'type': 'housing'},
        'cookie': {'name': 'Cookie', 'price': 2, 'maxOwn': float('inf'), 'type': 'collectible'},
        'pinkfeet': {'name': 'Pink Feet', 'price': 8, 'maxOwn': float('inf'), 'type': 'collectible'},
        'feetpic': {'name': 'Feet Pic', 'price': 5, 'maxOwn': float('inf'), 'type': 'collectible'},
        'jar': {'name': 'Jar', 'price': 3, 'maxOwn': float('inf'), 'type': 'collectible'},
        'animefigurine': {'name': 'Anime Figurine', 'price': 30, 'maxOwn': float('inf'), 'type': 'collectible'}
    }
    return load_json(SHOP_FILE, defaults)

# ==================== WORK MESSAGES ====================

WORK_MESSAGES = [
    "You fixed some fences and made ${amount}",
    "You mowed lawns all day and earned ${amount}",
    "You helped move furniture and made ${amount}",
    "You washed cars and brought home ${amount}",
    "You did some freelance work and earned ${amount}",
    "You sold handmade crafts and made ${amount}",
    "You delivered packages and earned ${amount}",
    "You walked dogs around the neighborhood and made ${amount}",
    "You cleaned houses and earned ${amount}",
    "You did yard work and brought home ${amount}",
]

GOV_MESSAGES = [
    "You worked for the TSA screening luggage",
    "You filed paperwork at the DMV",
    "You inspected buildings for the city",
    "You worked as a postal worker",
    "You processed permits at City Hall",
    "You worked road maintenance for the state",
    "You worked at the Department of Education",
    "You assisted at the Department of Defense",
    "You helped at the Department of Health",
]

SHUTDOWN_MESSAGES = [
    "You showed up to work at the TSA, but the government is shut down. You got nothing!",
    "You tried to work at the DMV but it's closed due to government shutdown. $0 earned.",
    "Government shutdown! Your shift was cancelled. No pay today!",
]

ROB_SUCCESS_MESSAGES = [
    "You snuck into their house and stole ${amount}!",
    "You picked their pocket and got away with ${amount}!",
    "You hacked their account and transferred ${amount}!",
    "You found their wallet and took ${amount}!",
]

ROB_FAIL_MESSAGES = [
    "You got caught! The police arrested you.",
    "Security cameras spotted you! You're going to jail.",
    "They caught you red-handed! Off to jail you go.",
    "The alarm went off! Police got you.",
]

# ==================== UTILITY FUNCTIONS ====================

def ensure_user(user_id):
    users = load_users()
    changed = False
    if user_id not in users:
        users[user_id] = {
            'createdAccount': False,
            'accountType': None,
            'checking': 0,
            'savings': 0,
            'pockets': 0,
            'emergency': 0,
            'businesses': [],
            'stocks': {},
            'crypto': {},
            'inventory': {},
            'loans': {
                'regular': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'missedDays': 0, 'inCollections': False, 'startDate': None},
                'stock': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'inCollections': False, 'startDate': None}
            },
            'cooldowns': {},
            'arrests': 0,
            'hasInsurance': False,
            'totalRobbedFrom': 0,
            'totalRobbedOthers': 0,
            'lastWorkDay': None,
            'illegalBusinesses': [],
            'advisor': 'none',
            'notifications': [],
            'nextNotificationId': 1,
        }
        changed = True

    user = users[user_id]
    if 'advisor' not in user:
        user['advisor'] = 'none'
        changed = True
    if 'notifications' not in user:
        user['notifications'] = []
        changed = True
    if 'nextNotificationId' not in user:
        user['nextNotificationId'] = 1
        changed = True
    if 'illegalBusinesses' not in user:
        user['illegalBusinesses'] = []
        changed = True

    if changed and len(user.get('notifications', [])) == 0:
        add_notification(
            user,
            '👋 Welcome to EconGame beta! Thanks for playing — your data is saved locally for testing.',
            'info'
        )

    if changed:
        save_users(users)
    return users[user_id]

def ensure_runtime_fields(user):
    if 'advisor' not in user:
        user['advisor'] = 'none'
    if 'notifications' not in user:
        user['notifications'] = []
    if 'nextNotificationId' not in user:
        user['nextNotificationId'] = 1
    if 'illegalBusinesses' not in user:
        user['illegalBusinesses'] = []

def add_notification(user, message, level='info'):
    ensure_runtime_fields(user)
    notification = {
        'id': user['nextNotificationId'],
        'message': message,
        'level': level,
        'read': False,
        'createdAt': datetime.now().isoformat()
    }
    user['nextNotificationId'] += 1
    user['notifications'].append(notification)
    user['notifications'] = user['notifications'][-100:]

def maybe_add_helper_notifications(user):
    ensure_runtime_fields(user)
    advisor = user.get('advisor', 'none')
    if advisor not in ['helper', 'none']:
        return

    pockets = user.get('pockets', 0)
    if pockets < 200:
        add_notification(user, '💡 Helper: Your pockets are low. Try regular work or transfer funds.', 'warning')

    loans = user.get('loans', {})
    total_debt = loans.get('regular', {}).get('currentDebt', 0) + loans.get('stock', {}).get('currentDebt', 0)
    if total_debt > 20000:
        add_notification(user, '💡 Helper: Your debt is high. Consider paying loans before new investments.', 'warning')

def get_advisor(user):
    ensure_runtime_fields(user)
    advisor = user.get('advisor', 'none')
    if advisor not in ADVISOR_PROFILES:
        advisor = 'none'
        user['advisor'] = advisor
    return advisor


def run_illegal_business_job(user, illegal_business):
    advisor = get_advisor(user)
    business_type = illegal_business.get('type', 'black_market')
    template = ILLEGAL_BUSINESS_TYPES.get(business_type, ILLEGAL_BUSINESS_TYPES['black_market'])

    payout = random.randint(template['min_payout'], template['max_payout'])
    raid_chance = template['base_raid_chance']

    if advisor == 'rivera':
        payout = int(payout * 1.2)
        raid_chance *= 0.65  # 35% lower chance of getting caught

    # Katie lifestyle effect makes all operations more expensive (reduced net gain)
    if advisor == 'katie':
        payout = int(payout * 0.85)

    caught = random.random() < raid_chance
    if caught:
        fine = int(payout * 0.8)
        jail_ms = 120000

        if advisor == 'rivera':
            # Rivera downside: when caught, punishment hits harder
            fine *= 3
            jail_ms *= 3
        elif advisor == 'miranda':
            fine = int(fine * 0.65)
            jail_ms = int(jail_ms * 0.75)

        user['pockets'] = max(0, user.get('pockets', 0) - fine)
        jail_user(user.get('id_for_runtime', session.get('player_id')), jail_ms)

        return {
            'success': False,
            'caught': True,
            'fine': fine,
            'jail_ms': jail_ms,
            'raid_chance': raid_chance,
            'message': f"🚨 Police raid! Operation failed. Fine: ${fine:,}. Jail: {int(jail_ms/60000)} minute(s)."
        }

    user['pockets'] = user.get('pockets', 0) + payout
    illegal_business['runs'] = illegal_business.get('runs', 0) + 1
    illegal_business['totalEarnings'] = illegal_business.get('totalEarnings', 0) + payout

    return {
        'success': True,
        'caught': False,
        'payout': payout,
        'raid_chance': raid_chance,
        'message': f"💰 Illegal operation successful! You earned ${payout:,}."
    }


def get_illegal_risk_and_payout_preview(user, illegal_business):
    advisor = get_advisor(user)
    business_type = illegal_business.get('type', 'black_market')
    template = ILLEGAL_BUSINESS_TYPES.get(business_type, ILLEGAL_BUSINESS_TYPES['black_market'])

    base_raid_chance = template['base_raid_chance']
    raid_chance = base_raid_chance
    base_min_payout = template['min_payout']
    base_max_payout = template['max_payout']
    min_payout = base_min_payout
    max_payout = base_max_payout

    advisor_note = 'No advisor modifier'

    if advisor == 'rivera':
        raid_chance *= 0.65
        min_payout = int(min_payout * 1.2)
        max_payout = int(max_payout * 1.2)
        advisor_note = 'Rivera: raid chance -35%, payout +20%'
    elif advisor == 'katie':
        min_payout = int(min_payout * 0.85)
        max_payout = int(max_payout * 0.85)
        advisor_note = 'Katie: payout -15% (higher lifestyle costs)'

    return {
        'advisor': advisor,
        'advisorNote': advisor_note,
        'baseRaidChance': round(base_raid_chance, 4),
        'baseRaidPercent': round(base_raid_chance * 100, 1),
        'raidChance': round(raid_chance, 4),
        'raidPercent': round(raid_chance * 100, 1),
        'baseMinPayout': base_min_payout,
        'baseMaxPayout': base_max_payout,
        'minPayout': min_payout,
        'maxPayout': max_payout,
    }

def get_cooldown_remaining(user_id, key, cooldown_ms):
    users = load_users()
    if user_id not in users:
        return 0
    cooldowns = users[user_id].get('cooldowns', {})
    last = cooldowns.get(key, 0)
    remaining = (last + cooldown_ms) - (datetime.now().timestamp() * 1000)
    return max(0, remaining)

def set_cooldown(user_id, key):
    users = load_users()
    if user_id not in users:
        ensure_user(user_id)
    if 'cooldowns' not in users[user_id]:
        users[user_id]['cooldowns'] = {}
    users[user_id]['cooldowns'][key] = datetime.now().timestamp() * 1000
    save_users(users)

def format_cooldown(ms):
    if ms <= 0:
        return '0s'
    seconds = int(ms / 1000)
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f'{minutes}m {secs}s'
    return f'{secs}s'

def is_jailed(user_id):
    users = load_users()
    if user_id not in users:
        return False
    jailed_until = users[user_id].get('jailedUntil', 0)
    return datetime.now().timestamp() * 1000 < jailed_until

def jail_user(user_id, duration_ms):
    users = load_users()
    ensure_user(user_id)
    users[user_id]['jailedUntil'] = datetime.now().timestamp() * 1000 + duration_ms
    users[user_id]['arrests'] = users[user_id].get('arrests', 0) + 1
    save_users(users)

# ==================== ROUTES ====================

@bp.route('/_game_internal')
def index():
    if 'player_id' not in session:
        session['player_id'] = secrets.token_hex(8)
        ensure_user(session['player_id'])
    return render_template('game.html')

# ==================== BANKING ====================

@bp.route('/api/create_account', methods=['POST'])
def create_account():
    data = request.json
    account_type = data.get('type')
    user_id = session.get('player_id')
    
    users = load_users()
    user = users[user_id]
    
    if user['createdAccount']:
        return jsonify({'error': 'You already have an account!'}), 400
    
    if account_type not in ['checking', 'savings']:
        return jsonify({'error': 'Invalid account type'}), 400
    
    user['createdAccount'] = True
    user['accountType'] = account_type
    save_users(users)
    
    return jsonify({'success': True, 'message': f'Created {account_type} account!'})

@bp.route('/api/balance')
def get_balance():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    return jsonify({
        'checking': user.get('checking', 0),
        'savings': user.get('savings', 0),
        'pockets': user.get('pockets', 0),
        'emergency': user.get('emergency', 0),
        'accountType': user.get('accountType'),
        'hasAccount': user.get('createdAccount', False)
    })

@bp.route('/api/deposit', methods=['POST'])
def deposit():
    data = request.json
    amount = int(data.get('amount', 0))
    target = data.get('target')
    user_id = session.get('player_id')
    
    users = load_users()
    user = users[user_id]
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if user['pockets'] < amount:
        return jsonify({'error': 'Not enough in pockets'}), 400
    
    if target == 'checking':
        user['checking'] += amount
        user['pockets'] -= amount
    elif target == 'savings':
        user['savings'] += amount
        user['pockets'] -= amount
    elif target == 'emergency':
        config = load_config()
        cap = config['emergencyCap']
        current = user.get('emergency', 0)
        space = max(0, cap - current)
        if space <= 0:
            return jsonify({'error': 'Emergency fund is full!'}), 400
        to_add = min(space, amount)
        user['emergency'] += to_add
        user['pockets'] -= to_add
        amount = to_add
    else:
        return jsonify({'error': 'Invalid target'}), 400
    
    save_users(users)
    return jsonify({'success': True, 'amount': amount})

@bp.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    amount = int(data.get('amount', 0))
    source = data.get('source')
    user_id = session.get('player_id')
    
    users = load_users()
    user = users[user_id]
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if source == 'checking':
        if user['checking'] < amount:
            return jsonify({'error': 'Not enough in checking'}), 400
        user['checking'] -= amount
        user['pockets'] += amount
    elif source == 'savings':
        if user['savings'] < amount:
            return jsonify({'error': 'Not enough in savings'}), 400
        user['savings'] -= amount
        user['pockets'] += amount
    elif source == 'emergency':
        if user['emergency'] < amount:
            return jsonify({'error': 'Not enough in emergency fund'}), 400
        user['emergency'] -= amount
        user['pockets'] += amount
    else:
        return jsonify({'error': 'Invalid source'}), 400
    
    save_users(users)
    return jsonify({'success': True})

# ==================== WORK ====================

@bp.route('/api/work', methods=['POST'])
def work():
    user_id = session.get('player_id')
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'work', 10000)  # 10 second cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    set_cooldown(user_id, 'work')
    
    amount = random.randint(50, 200)
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'miranda':
        amount = int(amount * 0.85)

    message = random.choice(WORK_MESSAGES).replace('${amount}', str(amount))

    user['pockets'] = user.get('pockets', 0) + amount
    maybe_add_helper_notifications(user)
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': message,
        'amount': amount,
        'pockets': user['pockets']
    })

@bp.route('/api/workgov', methods=['POST'])
def workgov():
    user_id = session.get('player_id')
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'workgov', 120000)  # 2 minute cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    config = load_config()
    
    # Check for government shutdown
    if config.get('govShutdown', False):
        message = random.choice(SHUTDOWN_MESSAGES)
        return jsonify({
            'success': True,
            'message': message,
            'amount': 0,
            'shutdown': True
        })
    
    set_cooldown(user_id, 'workgov')
    
    gross_amount = random.randint(7500, 30000)
    tax_rate = config.get('govTaxPercent', 21)
    net_amount = int(gross_amount * (1 - tax_rate / 100))
    
    job_desc = random.choice(GOV_MESSAGES)
    message = f"{job_desc} and made ${gross_amount:,} but taxes apply at {tax_rate}% so you only brought home ${net_amount:,}"
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    # Check for loan collections
    collection_amount = 0
    deducted_amount = 0
    loans = user.get('loans', {})
    regular_loan = loans.get('regular', {})
    stock_loan = loans.get('stock', {})
    
    regular_debt = max(0, int(regular_loan.get('currentDebt', 0) or 0))
    stock_debt = max(0, int(stock_loan.get('currentDebt', 0) or 0))
    total_debt = regular_debt + stock_debt
    
    if total_debt > 0:
        # Collect 25% of net pay
        collection_amount = int(net_amount * 0.25)
        deducted_amount = collection_amount
        net_amount -= collection_amount
        
        # Apply to regular loan first, then stock loan
        if regular_loan.get('currentDebt', 0) > 0:
            payment = min(collection_amount, regular_loan['currentDebt'])
            regular_loan['currentDebt'] -= payment
            collection_amount -= payment
        
        if collection_amount > 0 and stock_loan.get('currentDebt', 0) > 0:
            payment = min(collection_amount, stock_loan['currentDebt'])
            stock_loan['currentDebt'] -= payment
        
        if deducted_amount > 0:
            message += f"\n⚠️ LOAN COLLECTIONS: ${deducted_amount:,} deducted for outstanding loans"

    if advisor == 'miranda':
        net_amount = int(net_amount * 0.9)
        message += "\n⚖️ MIRANDA EFFECT: cautious strategy reduces short-term gains."
    
    user['pockets'] = user.get('pockets', 0) + net_amount
    maybe_add_helper_notifications(user)
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': message,
        'gross': gross_amount,
        'net': net_amount,
        'tax_rate': tax_rate,
        'pockets': user['pockets']
    })

# ==================== BUSINESSES ====================

@bp.route('/api/create_business', methods=['POST'])
def create_business():
    data = request.json
    business_name = data.get('name', '').strip()
    business_type = data.get('type', 'general')
    user_id = session.get('player_id')
    
    if not business_name or len(business_name) < 3:
        return jsonify({'error': 'Business name must be at least 3 characters'}), 400
    
    cost = 50000  # Cost to create a business
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        cost = int(cost * 1.2)
    
    if user.get('pockets', 0) < cost:
        return jsonify({'error': f'Need ${cost:,} in pockets to create a business'}), 400
    
    businesses = load_businesses()
    business_id = secrets.token_hex(8)
    
    businesses[business_id] = {
        'id': business_id,
        'name': business_name,
        'type': business_type,
        'owner': user_id,
        'workers': 0,
        'revenue': 0,
        'totalEarnings': 0,
        'createdAt': datetime.now().isoformat()
    }
    
    user['businesses'].append(business_id)
    user['pockets'] -= cost
    
    save_businesses(businesses)
    save_users(users)
    
    return jsonify({'success': True, 'business': businesses[business_id]})

@bp.route('/api/businesses')
def get_businesses():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    businesses = load_businesses()
    user_businesses = [businesses[bid] for bid in user.get('businesses', []) if bid in businesses]
    
    return jsonify({'businesses': user_businesses})


@bp.route('/api/create_illegal_business', methods=['POST'])
def create_illegal_business():
    data = request.json or {}
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    business_type = data.get('type', 'black_market')
    name = (data.get('name') or '').strip()

    if business_type not in ILLEGAL_BUSINESS_TYPES:
        return jsonify({'error': 'Invalid illegal business type'}), 400

    template = ILLEGAL_BUSINESS_TYPES[business_type]
    cost = template['startup_cost']
    advisor = get_advisor(user)

    if advisor == 'katie':
        cost = int(cost * 1.2)

    if user.get('pockets', 0) < cost:
        return jsonify({'error': f'Need ${cost:,} in pockets to start this operation'}), 400

    business_id = secrets.token_hex(8)
    illegal_business = {
        'id': business_id,
        'type': business_type,
        'name': name or template['name'],
        'createdAt': datetime.now().isoformat(),
        'runs': 0,
        'totalEarnings': 0,
        'lastRunAt': None,
        'history': [],
        'lastOutcome': None,
    }

    user['pockets'] -= cost
    user['illegalBusinesses'].append(illegal_business)
    add_notification(user, f"🕶️ New illegal business started: {illegal_business['name']}", 'warning')
    save_users(users)

    return jsonify({'success': True, 'business': illegal_business, 'startup_cost': cost})


@bp.route('/api/illegal_businesses')
def list_illegal_businesses():
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    cooldown_ms = 180000
    payload_businesses = []
    for entry in user.get('illegalBusinesses', []):
        business_copy = dict(entry)
        preview = get_illegal_risk_and_payout_preview(user, entry)
        remaining = 0
        last_run_iso = business_copy.get('lastRunAt')
        if last_run_iso:
            try:
                last_run = datetime.fromisoformat(last_run_iso)
                remaining = max(0, cooldown_ms - int((datetime.now() - last_run).total_seconds() * 1000))
            except Exception:
                remaining = 0

        business_copy['cooldownRemainingMs'] = remaining
        business_copy['cooldownLabel'] = format_cooldown(remaining)
        business_copy['risk'] = preview
        payload_businesses.append(business_copy)

    return jsonify({'businesses': payload_businesses, 'types': ILLEGAL_BUSINESS_TYPES, 'cooldownMs': cooldown_ms})


@bp.route('/api/run_illegal_business', methods=['POST'])
def run_illegal_business():
    data = request.json or {}
    business_id = data.get('business_id')
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    user['id_for_runtime'] = user_id

    if is_jailed(user_id):
        del user['id_for_runtime']
        return jsonify({'error': 'You are in jail!'}), 400

    illegal_business = None
    for entry in user.get('illegalBusinesses', []):
        if entry.get('id') == business_id:
            illegal_business = entry
            break

    if not illegal_business:
        del user['id_for_runtime']
        return jsonify({'error': 'Illegal business not found'}), 404

    # Shared cooldown per illegal business
    cooldown_ms = 180000
    last_run_iso = illegal_business.get('lastRunAt')
    if last_run_iso:
        try:
            last_run = datetime.fromisoformat(last_run_iso)
            remaining = cooldown_ms - int((datetime.now() - last_run).total_seconds() * 1000)
            if remaining > 0:
                del user['id_for_runtime']
                return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
        except Exception:
            pass

    result = run_illegal_business_job(user, illegal_business)
    illegal_business['lastRunAt'] = datetime.now().isoformat()

    outcome = {
        'at': datetime.now().isoformat(),
        'success': result.get('success', False),
        'caught': result.get('caught', False),
        'message': result.get('message'),
        'payout': result.get('payout', 0),
        'fine': result.get('fine', 0),
        'jail_ms': result.get('jail_ms', 0),
        'raid_chance': result.get('raid_chance', 0)
    }
    illegal_business['lastOutcome'] = outcome
    history = illegal_business.get('history', [])
    history.append(outcome)
    illegal_business['history'] = history[-15:]

    if result.get('caught'):
        add_notification(user, result['message'], 'danger')
    else:
        add_notification(user, result['message'], 'success')

    del user['id_for_runtime']
    save_users(users)

    payload = {
        'success': result['success'],
        'message': result['message'],
        'pockets': user.get('pockets', 0),
        'lastOutcome': illegal_business.get('lastOutcome')
    }
    if result.get('caught'):
        payload['fine'] = result['fine']
        payload['jail_ms'] = result['jail_ms']
    else:
        payload['payout'] = result['payout']

    return jsonify(payload)

@bp.route('/api/hire_worker', methods=['POST'])
def hire_worker():
    data = request.json
    business_id = data.get('business_id')
    user_id = session.get('player_id')
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = businesses[business_id]
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    cost_per_worker = 5000
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        cost_per_worker = int(cost_per_worker * 1.2)
    
    if user.get('pockets', 0) < cost_per_worker:
        return jsonify({'error': f'Need ${cost_per_worker:,} to hire a worker'}), 400
    
    user['pockets'] -= cost_per_worker
    business['workers'] += 1
    
    save_users(users)
    save_businesses(businesses)
    
    return jsonify({'success': True, 'workers': business['workers']})

# ==================== STOCKS ====================

@bp.route('/api/stocks')
def get_stocks():
    stocks = load_stocks()
    return jsonify({'stocks': stocks})

@bp.route('/api/buy_stock', methods=['POST'])
def buy_stock():
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    user_id = session.get('player_id')
    
    if quantity <= 0:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    stocks = load_stocks()
    if symbol not in stocks:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock_price = stocks[symbol]['price']
    total_cost = stock_price * quantity
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'gina':
        total_cost = int(total_cost * 1.1)
    elif advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    if user.get('pockets', 0) < total_cost:
        return jsonify({'error': f'Need ${total_cost:,} in pockets'}), 400
    
    user['pockets'] -= total_cost
    
    if 'stocks' not in user:
        user['stocks'] = {}
    
    user['stocks'][symbol] = user['stocks'].get(symbol, 0) + quantity
    save_users(users)
    
    return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/sell_stock', methods=['POST'])
def sell_stock():
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    user_id = session.get('player_id')
    
    if quantity <= 0:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    
    owned = user.get('stocks', {}).get(symbol, 0)
    if owned < quantity:
        return jsonify({'error': f'You only own {owned} shares'}), 400
    
    stocks = load_stocks()
    if symbol not in stocks:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock_price = stocks[symbol]['price']
    total_revenue = stock_price * quantity

    advisor = get_advisor(user)
    if advisor == 'gina':
        total_revenue = int(total_revenue * 0.9)
    
    user['stocks'][symbol] -= quantity
    if user['stocks'][symbol] == 0:
        del user['stocks'][symbol]
    
    user['pockets'] = user.get('pockets', 0) + total_revenue
    save_users(users)
    
    return jsonify({'success': True, 'total_revenue': total_revenue})

@bp.route('/api/portfolio')
def get_portfolio():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    stocks = load_stocks()
    portfolio = []
    
    for symbol, quantity in user.get('stocks', {}).items():
        if symbol in stocks:
            stock = stocks[symbol]
            portfolio.append({
                'symbol': symbol,
                'name': stock['name'],
                'quantity': quantity,
                'currentPrice': stock['price'],
                'totalValue': stock['price'] * quantity
            })
    
    return jsonify({'portfolio': portfolio})

# ==================== CRYPTO ====================

@bp.route('/api/crypto')
def get_crypto():
    crypto = load_crypto()
    return jsonify({'crypto': crypto})

@bp.route('/api/buy_crypto', methods=['POST'])
def buy_crypto():
    data = request.json
    symbol = data.get('symbol')
    amount = float(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    crypto = load_crypto()
    if symbol not in crypto:
        return jsonify({'error': 'Crypto not found'}), 404
    
    crypto_price = crypto[symbol]['price']
    total_cost = int(amount * crypto_price)
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    if user.get('pockets', 0) < total_cost:
        return jsonify({'error': f'Need ${total_cost:,} in pockets'}), 400
    
    user['pockets'] -= total_cost
    
    if 'crypto' not in user:
        user['crypto'] = {}
    
    user['crypto'][symbol] = user['crypto'].get(symbol, 0) + amount
    save_users(users)
    
    return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/sell_crypto', methods=['POST'])
def sell_crypto():
    data = request.json
    symbol = data.get('symbol')
    amount = float(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    owned = user.get('crypto', {}).get(symbol, 0)
    if owned < amount:
        return jsonify({'error': f'You only own {owned:.4f} {symbol}'}), 400
    
    crypto = load_crypto()
    if symbol not in crypto:
        return jsonify({'error': 'Crypto not found'}), 404
    
    crypto_price = crypto[symbol]['price']
    total_revenue = int(amount * crypto_price)
    
    user['crypto'][symbol] -= amount
    if user['crypto'][symbol] <= 0:
        del user['crypto'][symbol]
    
    user['pockets'] = user.get('pockets', 0) + total_revenue
    save_users(users)
    
    return jsonify({'success': True, 'total_revenue': total_revenue})

@bp.route('/api/crypto_wallet')
def get_crypto_wallet():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    crypto = load_crypto()
    wallet = []
    
    for symbol, amount in user.get('crypto', {}).items():
        if symbol in crypto:
            coin = crypto[symbol]
            wallet.append({
                'symbol': symbol,
                'name': coin['name'],
                'amount': amount,
                'currentPrice': coin['price'],
                'totalValue': int(coin['price'] * amount)
            })
    
    return jsonify({'wallet': wallet})

# ==================== LOANS ====================

@bp.route('/api/take_loan', methods=['POST'])
def take_loan():
    data = request.json
    loan_type = data.get('type', 'regular')
    amount = int(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0 or amount > 100000:
        return jsonify({'error': 'Loan amount must be between $1 and $100,000'}), 400
    
    users = load_users()
    user = users[user_id]
    
    if 'loans' not in user:
        user['loans'] = {
            'regular': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'missedDays': 0, 'inCollections': False, 'startDate': None},
            'stock': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'inCollections': False, 'startDate': None}
        }
    
    loan = user['loans'].get(loan_type, {})
    
    if loan.get('currentDebt', 0) > 0:
        return jsonify({'error': f'You already have an active {loan_type} loan'}), 400
    
    loan['principal'] = amount
    loan['currentDebt'] = amount
    loan['spent'] = 0
    loan['startDate'] = datetime.now().isoformat()
    loan['inCollections'] = False
    
    user['pockets'] = user.get('pockets', 0) + amount
    
    save_users(users)
    
    return jsonify({'success': True, 'amount': amount})

@bp.route('/api/pay_loan', methods=['POST'])
def pay_loan():
    data = request.json
    loan_type = data.get('type', 'regular')
    amount = int(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    loan = user.get('loans', {}).get(loan_type, {})
    current_debt = loan.get('currentDebt', 0)
    
    if current_debt == 0:
        return jsonify({'error': 'No active loan'}), 400
    
    if user.get('pockets', 0) < amount:
        return jsonify({'error': 'Not enough in pockets'}), 400
    
    payment = min(amount, current_debt)
    loan['currentDebt'] -= payment
    user['pockets'] -= payment
    
    save_users(users)
    
    return jsonify({'success': True, 'paid': payment, 'remaining': loan['currentDebt']})

@bp.route('/api/loans')
def get_loans():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    loans = user.get('loans', {
        'regular': {'principal': 0, 'currentDebt': 0, 'inCollections': False},
        'stock': {'principal': 0, 'currentDebt': 0, 'inCollections': False}
    })
    
    config = load_config()
    
    return jsonify({
        'loans': loans,
        'interestRate': config.get('interestRate', 3)
    })

# ==================== SHOP ====================

@bp.route('/api/shop')
def get_shop():
    shop = load_shop()
    return jsonify({'items': shop})

@bp.route('/api/buy_item', methods=['POST'])
def buy_item():
    data = request.json
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    user_id = session.get('player_id')
    
    shop = load_shop()
    if item_id not in shop:
        return jsonify({'error': 'Item not found'}), 404
    
    item = shop[item_id]
    total_cost = item['price'] * quantity
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    # Check max ownership
    current_owned = user.get('inventory', {}).get(item_id, 0)
    max_own = item.get('maxOwn', float('inf'))
    
    if current_owned + quantity > max_own:
        return jsonify({'error': f'Can only own {max_own} of this item'}), 400
    
    if user.get('pockets', 0) < total_cost:
        return jsonify({'error': f'Need ${total_cost:,} in pockets'}), 400
    
    user['pockets'] -= total_cost
    user['inventory'][item_id] = current_owned + quantity
    
    save_users(users)
    
    return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/inventory')
def get_inventory():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    shop = load_shop()
    inventory = []
    
    for item_id, quantity in user.get('inventory', {}).items():
        if item_id in shop:
            item = shop[item_id]
            inventory.append({
                'id': item_id,
                'name': item['name'],
                'quantity': quantity,
                'type': item.get('type', 'other')
            })
    
    return jsonify({'inventory': inventory})

# ==================== ROBBERY ====================

@bp.route('/api/rob/<target_id>', methods=['POST'])
def rob_user(target_id):
    user_id = session.get('player_id')
    
    if user_id == target_id:
        return jsonify({'error': 'Cannot rob yourself!'}), 400
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'rob', 300000)  # 5 minute cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    users = load_users()
    
    if target_id not in users:
        return jsonify({'error': 'Target not found'}), 404
    
    target = users[target_id]
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    set_cooldown(user_id, 'rob')
    
    # 50% success rate (Rivera reduces caught chance by 35%)
    success_threshold = 0.5
    if advisor == 'rivera':
        success_threshold = 0.325

    success = random.random() > success_threshold
    
    if success:
        # Steal 10-30% of their pockets
        target_pockets = target.get('pockets', 0)
        steal_percent = random.uniform(0.1, 0.3)
        stolen_amount = int(target_pockets * steal_percent)
        
        if stolen_amount == 0:
            return jsonify({
                'success': False,
                'message': "They had nothing to steal!",
                'amount': 0
            })
        
        # Check if target has insurance
        if target.get('hasInsurance', False):
            # Insurance pays them back 50%
            insurance_payout = int(stolen_amount * 0.5)
            target['pockets'] += insurance_payout
            stolen_amount = int(stolen_amount * 0.5)  # You only get 50%
            message = random.choice(ROB_SUCCESS_MESSAGES).replace('${amount}', f'{stolen_amount:,}') + f"\n(They had insurance, so you only got half!)"
        else:
            target['pockets'] -= stolen_amount
            message = random.choice(ROB_SUCCESS_MESSAGES).replace('${amount}', f'{stolen_amount:,}')
        
        user['pockets'] = user.get('pockets', 0) + stolen_amount
        user['totalRobbedOthers'] = user.get('totalRobbedOthers', 0) + stolen_amount
        target['totalRobbedFrom'] = target.get('totalRobbedFrom', 0) + stolen_amount
        target['lastRobbedAmount'] = stolen_amount
        
        save_users(users)
        
        return jsonify({
            'success': True,
            'message': message,
            'amount': stolen_amount
        })
    else:
        # Failed - go to jail for 2 minutes
        jail_duration = 120000
        if advisor == 'rivera':
            jail_duration = int(jail_duration * 3)
        elif advisor == 'miranda':
            jail_duration = int(jail_duration * 0.75)

        jail_user(user_id, jail_duration)
        message = random.choice(ROB_FAIL_MESSAGES)
        
        return jsonify({
            'success': False,
            'message': message + f" You're jailed for {int(jail_duration/60000)} minute(s)!",
            'jailed': True
        })

@bp.route('/api/buy_insurance', methods=['POST'])
def buy_insurance():
    user_id = session.get('player_id')
    
    cost = 10000
    
    users = load_users()
    user = users[user_id]
    
    if user.get('hasInsurance', False):
        return jsonify({'error': 'You already have insurance!'}), 400
    
    if user.get('pockets', 0) < cost:
        return jsonify({'error': f'Insurance costs ${cost:,}'}), 400
    
    user['pockets'] -= cost
    user['hasInsurance'] = True
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Insurance purchased!'})

# ==================== CONFIG/ADMIN ====================

@bp.route('/api/config')
def get_config():
    config = load_config()
    return jsonify(config)

@bp.route('/api/toggle_shutdown', methods=['POST'])
def toggle_shutdown():
    config = load_config()
    config['govShutdown'] = not config.get('govShutdown', False)
    save_config(config)
    return jsonify({'shutdown': config['govShutdown']})

@bp.route('/api/toggle_recession', methods=['POST'])
def toggle_recession():
    config = load_config()
    config['recession'] = not config.get('recession', False)
    save_config(config)
    return jsonify({'recession': config['recession']})

@bp.route('/api/advisors')
def get_advisors():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    advisor = get_advisor(user)
    return jsonify({'current': advisor, 'advisors': ADVISOR_PROFILES})

@bp.route('/api/advisor/select', methods=['POST'])
def select_advisor():
    user_id = session.get('player_id')
    data = request.json or {}
    advisor = (data.get('advisor') or 'none').strip().lower()

    if advisor not in ADVISOR_PROFILES:
        return jsonify({'error': 'Invalid advisor'}), 400

    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    user['advisor'] = advisor
    add_notification(user, f"🎭 Advisor updated: {ADVISOR_PROFILES[advisor]['name']}", 'info')
    maybe_add_helper_notifications(user)
    save_users(users)

    return jsonify({'success': True, 'advisor': advisor, 'profile': ADVISOR_PROFILES[advisor]})

@bp.route('/api/notifications')
def get_notifications():
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    maybe_add_helper_notifications(user)
    unread = sum(1 for n in user['notifications'] if not n.get('read'))
    save_users(users)
    return jsonify({'notifications': list(reversed(user['notifications'])), 'unread': unread})

@bp.route('/api/notifications/read', methods=['POST'])
def mark_notification_read():
    user_id = session.get('player_id')
    data = request.json or {}
    notification_id = data.get('id')
    read_all = bool(data.get('all', False))

    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    if read_all:
        for notification in user['notifications']:
            notification['read'] = True
    else:
        if notification_id is None:
            return jsonify({'error': 'id required (or all=true)'}), 400
        for notification in user['notifications']:
            if notification.get('id') == notification_id:
                notification['read'] = True
                break

    save_users(users)
    return jsonify({'success': True})

# ==================== LEADERBOARD ====================

@bp.route('/api/leaderboard')
def get_leaderboard():
    users = load_users()
    
    leaderboard = []
    for user_id, user in users.items():
        total_worth = (
            user.get('checking', 0) +
            user.get('savings', 0) +
            user.get('pockets', 0) +
            user.get('emergency', 0)
        )
        
        leaderboard.append({
            'id': user_id[:8],
            'total_worth': total_worth
        })
    
    leaderboard.sort(key=lambda x: x['total_worth'], reverse=True)
    
    return jsonify({'leaderboard': leaderboard[:10]})

# ==================== HOURLY PROCESSING ====================

def process_hourly_updates():
    """Process all hourly game updates"""
    config = load_config()
    
    # Update stock prices
    stocks = load_stocks()
    for symbol, stock in stocks.items():
        change_percent = random.uniform(-0.05, 0.05)  # -5% to +5%
        if config.get('recession', False):
            change_percent -= 0.02  # Extra -2% during recession
        
        stock['price'] = max(1, int(stock['price'] * (1 + change_percent)))
        
        if 'history' not in stock:
            stock['history'] = []
        stock['history'].append({
            'time': datetime.now().isoformat(),
            'price': stock['price']
        })
        # Keep only last 100 history points
        stock['history'] = stock['history'][-100:]
    
    save_stocks(stocks)
    
    # Update crypto prices
    crypto = load_crypto()
    for symbol, coin in crypto.items():
        change_percent = random.uniform(-0.1, 0.1)  # -10% to +10% (more volatile)
        coin['price'] = max(0.01, coin['price'] * (1 + change_percent))
        
        if 'history' not in coin:
            coin['history'] = []
        coin['history'].append({
            'time': datetime.now().isoformat(),
            'price': coin['price']
        })
        coin['history'] = coin['history'][-100:]
    
    save_crypto(crypto)
    
    # Process business revenue
    businesses = load_businesses()
    users = load_users()
    for business_id, business in businesses.items():
        workers = business.get('workers', 0)
        if workers > 0:
            revenue = workers * random.randint(100, 500)

            owner_id = business.get('owner')
            if owner_id in users:
                owner = users[owner_id]
                ensure_runtime_fields(owner)
                if get_advisor(owner) == 'gina':
                    revenue = int(revenue * 1.25)

            business['revenue'] = revenue
            business['totalEarnings'] = business.get('totalEarnings', 0) + revenue
    
    save_businesses(businesses)
    
    # Process interest on loans
    for user_id, user in users.items():
        loans = user.get('loans', {})
        
        for loan_type, loan in loans.items():
            if loan.get('currentDebt', 0) > 0:
                interest_rate = config.get('interestRate', 3) / 100
                daily_interest = loan['currentDebt'] * (interest_rate / 24)  # Hourly
                loan['currentDebt'] = int(loan['currentDebt'] + daily_interest)
        
        # Process savings interest
        savings = user.get('savings', 0)
        if savings > 0:
            interest_rate = config.get('interestRate', 3) / 100
            hourly_interest = savings * (interest_rate / 24 / 365)
            user['savings'] = int(savings + hourly_interest)
    
    save_users(users)
    
    config['lastHourlyUpdate'] = datetime.now().isoformat()
    save_config(config)
    
    print(f"[HOURLY] Processed updates at {datetime.now()}")

# You can set up a background task or cron job to call process_hourly_updates()
# For now, we'll add a manual endpoint
@bp.route('/api/process_hourly', methods=['POST'])
def trigger_hourly():
    process_hourly_updates()
    return jsonify({'success': True, 'message': 'Hourly updates processed'})

