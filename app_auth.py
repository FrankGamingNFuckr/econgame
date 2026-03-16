from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import random
import secrets
import json
import os
import hashlib
import hmac
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path
from itsdangerous import URLSafeTimedSerializer

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, that's okay

app = Flask(__name__)
FAVICON_VERSION = '20260315b'
STATIC_ASSET_VERSION = '20260315c'

# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
email_serializer = URLSafeTimedSerializer(app.secret_key)

# Session configuration for Remember Me
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30 days for remember me
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Register full game API/logic as a blueprint so login and APIs run together
try:
    from app_full import bp as full_bp
    app.register_blueprint(full_bp)
    print('✅ app_full.py blueprint loaded successfully')
except Exception as e:
    print(f'❌ ERROR: Failed to load app_full.py blueprint: {e}')
    import traceback
    traceback.print_exc()
    # Re-raise so the error is visible
    raise

# Optional: Enable rate limiting if flask-limiter is installed
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    print("WARNING: flask-limiter not installed. Rate limiting disabled.")
    print("   Install with: pip install flask-limiter")

# Data directories
DATA_DIR = Path('game_data')
DATA_DIR.mkdir(exist_ok=True)

# Serve game images
@app.route('/game_images/<path:filename>')
def serve_game_image(filename):
    """Serve images from the game_images directory"""
    images_dir = os.path.join(app.root_path, 'game_images')
    return send_from_directory(images_dir, filename)

@app.route('/favicon.ico')
def favicon():
    # Some browsers auto-request /favicon.ico even when a PNG is specified in HTML.
    images_dir = os.path.join(app.root_path, 'game_images')
    return send_from_directory(images_dir, 'favicon.png')

@app.context_processor
def inject_global_template_vars():
    return {
        'favicon_url': f'/game_images/favicon.png?v={FAVICON_VERSION}',
        'static_asset_version': STATIC_ASSET_VERSION
    }

USERS_FILE = DATA_DIR / 'users.json'
ACCOUNTS_FILE = DATA_DIR / 'accounts.json'  # Separate file for login credentials
BUSINESSES_FILE = DATA_DIR / 'businesses.json'
CONFIG_FILE = DATA_DIR / 'config.json'
STOCKS_FILE = DATA_DIR / 'stocks.json'
CRYPTO_FILE = DATA_DIR / 'crypto.json'
SHOP_FILE = DATA_DIR / 'shop.json'
PASSWORD_RESETS_FILE = DATA_DIR / 'password_resets.json'
ADMIN_KEYS_FILE = DATA_DIR / 'admin_keys.json'  # Moderator access keys

# ==================== SECURITY FUNCTIONS ====================

def hash_password(password, salt=None):
    """Hash a password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 for secure password hashing
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    return salt, password_hash.hex()

def verify_password(stored_salt, stored_hash, provided_password):
    """Verify a password against a hash"""
    _, new_hash = hash_password(provided_password, stored_salt)
    return hmac.compare_digest(stored_hash, new_hash)

def generate_email_verification_token(email):
    return email_serializer.dumps(email, salt='email-verify')

def verify_email_verification_token(token, max_age_seconds=86400):
    try:
        return email_serializer.loads(token, salt='email-verify', max_age=max_age_seconds)
    except Exception:
        return None

def send_verification_email(to_email, username, token):
    """
    Send verification email.
    Returns tuple: (email_sent: bool, verification_link: str)
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USERNAME')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    # Auto-detect URL from Render environment or use localhost for local dev
    app_url = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('APP_URL', 'http://localhost:5000')

    verification_link = f"{app_url}/verify-email?token={token}"

    # Dev fallback: no SMTP configured
    if not smtp_user or not smtp_pass:
        print("WARNING: Verification email not sent: SMTP not configured")
        print(f"DEV VERIFICATION LINK for {to_email}: {verification_link}")
        return False, verification_link

    subject = "EconGame - Verify Your Email"
    body = f"""Hi {username},

Welcome to EconGame!

Please verify your email by clicking this link:
{verification_link}

This link expires in 24 hours.

If you did not create this account, you can ignore this email.

- EconGame Team
"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email

    try:
        # Add timeout to prevent hanging
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"SUCCESS: Verification email sent to {to_email}")
        return True, verification_link
    except Exception as e:
        print(f"ERROR: Failed to send verification email: {e}")
        print(f"DEV VERIFICATION LINK for {to_email}: {verification_link}")
        return False, verification_link
        print(f"DEV VERIFICATION LINK for {to_email}: {verification_link}")
        return False, verification_link

def send_reset_email(to_email, reset_code, username):
    """
    Send password reset email.
    Returns True if email sent successfully, False otherwise.
    
    Configure these environment variables:
        SMTP_SERVER (default: smtp.gmail.com)
        SMTP_PORT (default: 587)
        SMTP_USERNAME (your email)
        SMTP_PASSWORD (your app password)
        APP_URL (default: http://localhost:5000)
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USERNAME')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    # Auto-detect URL from Render environment or use localhost for local dev
    app_url = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('APP_URL', 'http://localhost:5000')
    
    # If SMTP not configured, return False
    if not smtp_user or not smtp_pass:
        print("WARNING: Email not sent: SMTP credentials not configured")
        print("   Set SMTP_USERNAME and SMTP_PASSWORD environment variables")
        return False
    
    subject = "EconGame - Password Reset Request"
    reset_link = f"{app_url}/reset-password?code={reset_code}"
    
    body = f"""Hi {username},

You requested a password reset for your EconGame account.

Click here to reset your password:
{reset_link}

Or use this reset code manually: {reset_code}

This code expires in 1 hour.

If you didn't request this, you can safely ignore this email.

- EconGame Team
"""
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    
    try:
        # Add timeout to prevent hanging
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"SUCCESS: Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email: {e}")
        return False

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

def load_accounts():
    """Load user login credentials (username/email -> password hash)"""
    return load_json(ACCOUNTS_FILE, {})

def save_accounts(data):
    save_json(ACCOUNTS_FILE, data)

def load_users():
    """Load user game data"""
    return load_json(USERS_FILE, {})

def save_users(data):
    save_json(USERS_FILE, data)

def load_password_resets():
    return load_json(PASSWORD_RESETS_FILE, {})

def save_password_resets(data):
    save_json(PASSWORD_RESETS_FILE, data)

def load_admin_keys():
    """Load admin keys for moderator access"""
    return load_json(ADMIN_KEYS_FILE, {})

def save_admin_keys(data):
    save_json(ADMIN_KEYS_FILE, data)

def generate_admin_key():
    """Generate a new admin key"""
    return secrets.token_urlsafe(32)

def verify_admin_key(key, username=None):
    """Verify if an admin key is valid and (optionally) allowed for username."""
    keys = load_admin_keys()
    if key not in keys:
        return False

    key_data = keys[key]
    if not key_data.get('active', True):
        return False

    assigned_username = (key_data.get('assigned_username') or '').strip().lower()
    if assigned_username:
        provided_username = (username or '').strip().lower()
        return provided_username == assigned_username

    return True


def load_owner_credentials():
    """Load owner credentials from game_data/owner.json, or None if unavailable."""
    owner_file = Path('game_data') / 'owner.json'
    if not owner_file.exists():
        return None
    try:
        return json.loads(owner_file.read_text())
    except Exception:
        return None


def username_exists_for_assignment(username):
    """Check whether a username exists in accounts/users/owner records."""
    normalized = (username or '').strip().lower()
    if not normalized:
        return False

    owner = load_owner_credentials() or {}
    owner_username = (owner.get('username') or '').strip().lower()
    if owner_username == normalized:
        return True

    accounts = load_accounts()
    if normalized in accounts:
        return True

    users = load_users()
    # users.json may have mixed-case keys, so compare case-insensitively
    return any((key or '').strip().lower() == normalized for key in users.keys())


def require_owner():
    """Return tuple (None) if owner in session, else a redirect/JSON error."""
    if not session.get('is_owner'):
        return jsonify({'error': 'Owner access required'}), 403
    return None

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

def ensure_user(username):
    """Ensure user game data exists"""
    try:
        from app_full import ensure_user as full_ensure_user
        return full_ensure_user(username)
    except Exception:
        pass

    users = load_users()
    if username not in users:
        users[username] = {
            'username': username,
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
            'jailedUntil': 0,
            'arrests': 0,
            'hasInsurance': False,
            'totalRobbedFrom': 0,
            'totalRobbedOthers': 0,
            'lastWorkDay': None,
            'createdAt': datetime.now().isoformat()
        }
        save_users(users)
    return users[username]

def get_owner_user_key(users, owner_username):
    if owner_username in users:
        return owner_username

    owner_lower = owner_username.lower()
    for existing_key in users.keys():
        if existing_key.lower() == owner_lower:
            return existing_key

    return owner_username

def get_current_user():
    """Get currently logged in username"""
    return session.get('username')

def require_login():
    """Redirect to login if not authenticated"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return None

def get_cooldown_remaining(username, key, cooldown_ms):
    users = load_users()
    if username not in users:
        return 0
    cooldowns = users[username].get('cooldowns', {})
    last = cooldowns.get(key, 0)
    remaining = (last + cooldown_ms) - (datetime.now().timestamp() * 1000)
    return max(0, remaining)

def set_cooldown(username, key):
    users = load_users()
    if username not in users:
        ensure_user(username)
    if 'cooldowns' not in users[username]:
        users[username]['cooldowns'] = {}
    users[username]['cooldowns'][key] = datetime.now().timestamp() * 1000
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

def is_jailed(username):
    users = load_users()
    if username not in users:
        return False
    jailed_until = users[username].get('jailedUntil', 0)
    return datetime.now().timestamp() * 1000 < jailed_until

def jail_user(username, duration_ms):
    users = load_users()
    ensure_user(username)
    users[username]['jailedUntil'] = datetime.now().timestamp() * 1000 + duration_ms
    users[username]['arrests'] = users[username].get('arrests', 0) + 1
    save_users(users)

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    # If already logged in, redirect to game
    if session.get('player_id'):
        return redirect('/game')
    # Show home screen with options to login or register
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to game
    if request.method == 'GET' and session.get('player_id'):
        return redirect('/game')
    
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        accounts = load_accounts()

        account = accounts.get(username)

        # Owner fallback: allow owner account to use regular login even if not in accounts.json
        owner = load_owner_credentials()
        owner_username = (owner.get('username', '') if owner else '').strip().lower()
        owner_login = owner and username == owner_username

        if account is None and not owner_login:
            return jsonify({'error': 'Invalid username or password'}), 401

        if owner_login:
            owner_salt = owner.get('salt')
            owner_hash = owner.get('password_hash', '')
            if not owner_salt or not verify_password(owner_salt, owner_hash, password):
                return jsonify({'error': 'Invalid username or password'}), 401

            # Owner regular login should still grant owner + moderator capabilities
            session['username'] = owner.get('username')
            session['player_id'] = owner.get('username')
            session['is_owner'] = True
            session['is_moderator'] = True
            session.permanent = remember_me
            ensure_user(owner.get('username'))

            return jsonify({'success': True, 'message': 'Login successful!'})

        # Normal account login path
        account = accounts[username]

        # Email verification disabled - allow all users to login
        # (Password reset still requires email)
        
        if not verify_password(account['salt'], account['password_hash'], password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Successful login
        session['username'] = username
        # Keep compatibility with game APIs expecting `player_id`
        session['player_id'] = username
        session.permanent = remember_me
        ensure_user(username)
        
        return jsonify({'success': True, 'message': 'Login successful!'})
    
    turnstile_site_key = os.environ.get('TURNSTILE_SITE_KEY', '1x00000000000000000000AA')
    return render_template('login.html', turnstile_site_key=turnstile_site_key)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Resend verification email (or print dev link when SMTP is not configured).
    Accepts username or email to locate account.
    """
    data = request.json or {}
    identifier = (data.get('identifier') or '').strip().lower()

    if not identifier:
        return jsonify({'error': 'Username or email required'}), 400

    accounts = load_accounts()

    # Find account by username or email
    matched_username = None
    matched_account = None

    if identifier in accounts:
        matched_username = identifier
        matched_account = accounts[identifier]
    else:
        for username, account in accounts.items():
            if account.get('email', '').lower() == identifier:
                matched_username = username
                matched_account = account
                break

    # Generic success response for unknown accounts (avoid account enumeration)
    if not matched_account:
        return jsonify({
            'success': True,
            'message': 'If that account exists, a verification email has been sent.'
        })

    if matched_account.get('email_verified') is True:
        return jsonify({'success': True, 'message': 'This account is already verified.'})

    email = matched_account.get('email')
    if not email:
        return jsonify({'error': 'Account email not found'}), 400

    token = generate_email_verification_token(email)
    email_sent, verification_link = send_verification_email(email, matched_username, token)

    if email_sent:
        return jsonify({'success': True, 'message': 'Verification email sent. Please check your inbox.'})

    # Dev fallback
    return jsonify({
        'success': True,
        'message': 'Email service not configured. Use the dev verification link below.',
        'verification_link': verification_link
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If already logged in, redirect to game
    if request.method == 'GET' and session.get('player_id'):
        return redirect('/game')
    
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = data.get('username', '').strip().lower()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if not email or '@' not in email:
            return jsonify({'error': 'Valid email required'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if username/email already exists
        accounts = load_accounts()

        if username_exists_for_assignment(username):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Check if email already used
        for acc_username, acc_data in accounts.items():
            if acc_data.get('email') == email:
                return jsonify({'error': 'Email already registered'}), 400
        
        # Create account
        salt, password_hash = hash_password(password)
        
        accounts[username] = {
            'username': username,
            'email': email,
            'salt': salt,
            'password_hash': password_hash,
            'email_verified': True,  # Email verification disabled for easier access
            'email_verified_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        save_accounts(accounts)
        
        # Create game data
        ensure_user(username)

        # Email verification disabled - skip sending verification emails
        return jsonify({
            'success': True,
            'message': 'Account created successfully! You can now log in.'
        })
    
    return render_template('register.html')

@app.route('/verify-email')
def verify_email():
    token = request.args.get('token', '').strip()
    if not token:
        return "Missing verification token.", 400

    email = verify_email_verification_token(token, max_age_seconds=86400)
    if not email:
        return "Invalid or expired verification link.", 400

    accounts = load_accounts()
    matched_username = None
    for username, account in accounts.items():
        if account.get('email') == email:
            matched_username = username
            break

    if not matched_username:
        return "Account not found for this verification link.", 404

    accounts[matched_username]['email_verified'] = True
    accounts[matched_username]['email_verified_at'] = datetime.now().isoformat()
    save_accounts(accounts)

    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/moderator-login', methods=['GET', 'POST'])
def moderator_login():
    # If already logged in as moderator, redirect to game
    if request.method == 'GET' and session.get('player_id') and session.get('is_moderator'):
        return redirect('/game')
    
    if request.method == 'POST':
        data = request.json
        username = data.get('username', 'Moderator').strip()
        admin_key = data.get('admin_key', '').strip()
        remember_me = data.get('remember_me', False)
        
        if not admin_key:
            return jsonify({'error': 'Admin key required'}), 400
        
        # Owner special-case: allow owner to authenticate here using owner password
        owner = load_owner_credentials()
        owner_username = (owner.get('username', '') if owner else '').strip().lower()
        if owner and username.strip().lower() == owner_username:
            owner_salt = owner.get('salt')
            owner_hash = owner.get('password_hash', '')
            if owner_salt and verify_password(owner_salt, owner_hash, admin_key):
                owner_name = owner.get('username')
                session['username'] = owner_name
                session['player_id'] = owner_name
                session['is_moderator'] = True
                session['is_owner'] = True
                session.permanent = remember_me
                ensure_user(owner_name)
                return jsonify({
                    'success': True,
                    'message': f'Welcome, {owner_name}! Owner/moderator access granted.'
                })

        # Verify admin key
        if verify_admin_key(admin_key, username):
            # Grant moderator access
            session['username'] = username
            # Ensure APIs using `player_id` work for moderators as well
            session['player_id'] = username
            session['is_moderator'] = True
            session.permanent = remember_me
            
            # Ensure user data exists (moderators can also play)
            ensure_user(username)
            
            # Track which key was used
            keys = load_admin_keys()
            keys[admin_key]['last_used'] = datetime.now().isoformat()
            keys[admin_key]['last_username'] = username
            save_admin_keys(keys)
            
            return jsonify({
                'success': True,
                'message': f'Welcome, {username}! Moderator access granted.'
            })
        else:
            return jsonify({'error': 'Invalid admin key or key not assigned to this username'}), 401
    
    turnstile_site_key = os.environ.get('TURNSTILE_SITE_KEY', '1x00000000000000000000AA')
    return render_template('moderator_login.html', turnstile_site_key=turnstile_site_key)


@app.route('/owner-login', methods=['GET', 'POST'])
def owner_login():
    """Owner-only login. Owner credentials are stored in game_data/owner.json
    The script `scripts/create_owner.py` generates a secure password and writes
    a salted hash to that file."""
    # If already logged in as owner, redirect to owner dashboard
    if request.method == 'GET' and session.get('player_id') and session.get('is_owner'):
        return redirect('/owner-dashboard')
    
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        # Only allow the configured owner username
        owner_file = Path('game_data') / 'owner.json'
        if not owner_file.exists():
            return jsonify({'error': 'Owner not configured'}), 500

        try:
            owner = json.loads(owner_file.read_text())
        except Exception:
            return jsonify({'error': 'Failed to read owner credentials'}), 500

        if username != owner.get('username'):
            return jsonify({'error': 'Invalid owner credentials'}), 401

        salt = owner.get('salt')
        if not salt:
            return jsonify({'error': 'Owner credentials invalid'}), 500

        # Verify password
        _, hashed = hash_password(password, salt)
        if not hmac.compare_digest(hashed, owner.get('password_hash', '')):
            return jsonify({'error': 'Invalid owner credentials'}), 401

        # Successful owner login
        session['username'] = username
        session['is_owner'] = True
        session['is_moderator'] = True
        session['player_id'] = username
        session.permanent = remember_me

        # Ensure game user data exists
        ensure_user(username)

        return jsonify({'success': True, 'message': 'Owner login successful!'})

    turnstile_site_key = os.environ.get('TURNSTILE_SITE_KEY', '1x00000000000000000000AA')
    return render_template('owner_login.html', turnstile_site_key=turnstile_site_key)


@app.route('/owner-dashboard')
def owner_dashboard():
    # Owner-only UI
    auth = require_owner()
    if auth:
        return auth
    return render_template('owner_dashboard.html')


@app.route('/api/admin_keys')
def api_admin_keys():
    auth = require_owner()
    if auth:
        return auth
    keys = load_admin_keys()
    return jsonify({'keys': keys})


@app.route('/api/admin_keys/toggle', methods=['POST'])
def api_admin_keys_toggle():
    auth = require_owner()
    if auth:
        return auth
    data = request.json or {}
    key = data.get('key')
    if not key:
        return jsonify({'error': 'Key required'}), 400
    keys = load_admin_keys()
    if key not in keys:
        return jsonify({'error': 'Key not found'}), 404
    keys[key]['active'] = not keys[key].get('active', True)
    keys[key]['last_used'] = datetime.now().isoformat()
    save_admin_keys(keys)
    return jsonify({'success': True, 'key': key, 'active': keys[key]['active']})


@app.route('/api/admin_keys/generate', methods=['POST'])
def api_admin_keys_generate():
    auth = require_owner()
    if auth:
        return auth
    data = request.json or {}
    assigned_username = (data.get('assigned_username') or '').strip().lower()
    description = (data.get('description') or '').strip() or 'Generated by owner'

    if assigned_username and not username_exists_for_assignment(assigned_username):
        return jsonify({'error': 'Enter a valid username for assignment'}), 400

    keys = load_admin_keys()
    new = generate_admin_key()
    keys[new] = {
        'created_at': datetime.now().isoformat(),
        'active': True,
        'description': description,
        'assigned_username': assigned_username or None,
        'last_used': None,
        'last_username': None
    }
    save_admin_keys(keys)
    return jsonify({'success': True, 'key': new, 'assigned_username': assigned_username or None})


@app.route('/api/admin_keys/reassign', methods=['POST'])
def api_admin_keys_reassign():
    auth = require_owner()
    if auth:
        return auth

    data = request.json or {}
    key = (data.get('key') or '').strip()
    assigned_username = (data.get('assigned_username') or '').strip().lower()

    if not key:
        return jsonify({'error': 'Key required'}), 400

    keys = load_admin_keys()
    if key not in keys:
        return jsonify({'error': 'Key not found'}), 404

    if assigned_username and not username_exists_for_assignment(assigned_username):
        return jsonify({'error': 'Enter a valid username for assignment'}), 400

    # Empty string means unassign (shared moderator key)
    keys[key]['assigned_username'] = assigned_username or None
    keys[key]['last_used'] = datetime.now().isoformat()
    save_admin_keys(keys)

    return jsonify({'success': True, 'key': key, 'assigned_username': keys[key]['assigned_username']})


@app.route('/api/usernames')
def api_usernames():
    """Owner-only endpoint to provide username suggestions for key assignment UI."""
    auth = require_owner()
    if auth:
        return auth

    query = (request.args.get('query') or '').strip().lower()

    usernames = set()

    owner = load_owner_credentials() or {}
    if owner.get('username'):
        usernames.add(owner['username'])

    accounts = load_accounts()
    usernames.update(accounts.keys())

    users = load_users()
    usernames.update(users.keys())

    filtered = []
    for username in usernames:
        if query and query not in (username or '').lower():
            continue
        filtered.append(username)

    filtered.sort(key=lambda value: value.lower())

    # Keep payload lightweight
    return jsonify({'usernames': filtered[:200]})

# ============================================================================
# ECONOMIC RATE MANAGEMENT APIS
# ============================================================================

@app.route('/api/owner/economic-rates')
def get_economic_rates():
    """Owner-only: Get current economic rates from config"""
    auth = require_owner()
    if auth:
        return auth
    
    config = load_config()
    rates = {
        'taxRate': config.get('taxRate', 0.1),
        'highIncomeRate': config.get('highIncomeRate', 0.25),
        'govTaxPercent': config.get('govTaxPercent', 21),
        'inflation': config.get('inflation', 0.02)
    }
    return jsonify({'success': True, 'rates': rates})

@app.route('/api/owner/update-economic-rates', methods=['POST'])
def update_economic_rates():
    """Owner-only: Update economic rates immediately"""
    auth = require_owner()
    if auth:
        return auth
    
    data = request.json
    
    taxRate = data.get('taxRate')
    highIncomeRate = data.get('highIncomeRate')
    govTaxPercent = data.get('govTaxPercent')
    inflation = data.get('inflation')
    
    if any(v is None for v in [taxRate, highIncomeRate, govTaxPercent, inflation]):
        return jsonify({'error': 'All rate fields required'}), 400
    
    config = load_config()
    config['taxRate'] = float(taxRate)
    config['highIncomeRate'] = float(highIncomeRate)
    config['govTaxPercent'] = int(govTaxPercent)
    config['inflation'] = float(inflation)
    save_config(config)
    
    return jsonify({'success': True, 'message': 'Economic rates updated successfully'})

@app.route('/api/owner/rate-change-requests')
def get_rate_change_requests():
    """Owner-only: Get pending rate change requests from moderators"""
    auth = require_owner()
    if auth:
        return auth
    
    # Load owner's notifications that are rate change requests
    owner = load_owner_credentials()
    if not owner:
        return jsonify({'requests': []})
    
    owner_username = owner.get('username', '').strip()
    users = load_users()
    owner_user_key = get_owner_user_key(users, owner_username)
    
    if owner_user_key not in users:
        return jsonify({'requests': []})
    
    owner_user_data = users[owner_user_key]
    notifications = owner_user_data.get('notifications', [])
    
    # Filter for rate change request notifications
    requests = []
    for notif in notifications:
        if notif.get('type') == 'rate_change_request' and not notif.get('read'):
            requests.append({
                'id': notif['id'],
                'from_moderator': notif.get('from_moderator', 'Unknown'),
                'changes': notif.get('changes', {}),
                'reason': notif.get('reason', ''),
                'timestamp': notif.get('createdAt', '')
            })
    
    return jsonify({'requests': requests})

@app.route('/api/owner/approve-rate-request', methods=['POST'])
def approve_rate_request():
    """Owner-only: Approve and apply a moderator's rate change request"""
    auth = require_owner()
    if auth:
        return auth
    
    data = request.json
    request_id = data.get('requestId')
    
    if not request_id:
        return jsonify({'error': 'Request ID required'}), 400
    
    # Load owner's notifications
    owner = load_owner_credentials()
    owner_username = owner.get('username', '').strip()
    users = load_users()
    owner_user_key = get_owner_user_key(users, owner_username)
    
    if owner_user_key not in users:
        return jsonify({'error': 'Owner user data not found'}), 404
    
    owner_user_data = users[owner_user_key]
    notifications = owner_user_data.get('notifications', [])
    
    # Find the request
    request_notif = None
    for notif in notifications:
        if notif.get('id') == int(request_id) and notif.get('type') == 'rate_change_request':
            request_notif = notif
            break
    
    if not request_notif:
        return jsonify({'error': 'Request not found'}), 404
    
    # Apply the changes
    config = load_config()
    changes = request_notif.get('changes', {})
    
    if 'taxRate' in changes:
        config['taxRate'] = float(changes['taxRate'])
    if 'highIncomeRate' in changes:
        config['highIncomeRate'] = float(changes['highIncomeRate'])
    if 'govTaxPercent' in changes:
        config['govTaxPercent'] = int(changes['govTaxPercent'])
    if 'inflation' in changes:
        config['inflation'] = float(changes['inflation'])
    
    save_config(config)
    
    # Mark notification as read
    request_notif['read'] = True
    save_users(users)
    
    # Send confirmation notification to the moderator
    moderator_name = request_notif.get('from_moderator', '').lower()
    if moderator_name in users:
        from app_full import add_notification
        add_notification(
            users[moderator_name],
            f"✅ Your economic rate change request has been approved by the owner!",
            'success'
        )
        save_users(users)
    
    return jsonify({'success': True, 'message': 'Rate changes applied successfully'})

@app.route('/api/owner/dismiss-rate-request', methods=['POST'])
def dismiss_rate_request():
    """Owner-only: Dismiss a moderator's rate change request without applying"""
    auth = require_owner()
    if auth:
        return auth
    
    data = request.json
    request_id = data.get('requestId')
    
    if not request_id:
        return jsonify({'error': 'Request ID required'}), 400
    
    # Load owner's notifications
    owner = load_owner_credentials()
    owner_username = owner.get('username', '').strip()
    users = load_users()
    owner_user_key = get_owner_user_key(users, owner_username)
    
    if owner_user_key not in users:
        return jsonify({'error': 'Owner user data not found'}), 404
    
    owner_user_data = users[owner_user_key]
    notifications = owner_user_data.get('notifications', [])
    
    # Find and mark as read
    for notif in notifications:
        if notif.get('id') == int(request_id) and notif.get('type') == 'rate_change_request':
            notif['read'] = True
            save_users(users)
            return jsonify({'success': True, 'message': 'Request dismissed'})
    
    return jsonify({'error': 'Request not found'}), 404

@app.route('/api/moderator/request-rate-change', methods=['POST'])
def moderator_request_rate_change():
    """Moderator-only: Request economic rate changes from owner"""
    if not session.get('is_moderator'):
        return jsonify({'error': 'Moderator access required'}), 403
    
    data = request.json
    changes = data.get('changes', {})
    reason = data.get('reason', '').strip()
    
    if not changes:
        return jsonify({'error': 'No changes specified'}), 400
    
    moderator_name = session.get('username', 'Unknown')
    
    # Load owner's user data to add notification
    owner = load_owner_credentials()
    if not owner:
        return jsonify({'error': 'Owner not found'}), 500
    
    owner_username = owner.get('username', '').strip()
    users = load_users()
    owner_user_key = get_owner_user_key(users, owner_username)
    
    if owner_user_key not in users:
        ensure_user(owner_username)
        users = load_users()
        owner_user_key = get_owner_user_key(users, owner_username)
    
    owner_user_data = users[owner_user_key]
    
    # Ensure notification fields exist
    if 'notifications' not in owner_user_data:
        owner_user_data['notifications'] = []
    if 'nextNotificationId' not in owner_user_data:
        owner_user_data['nextNotificationId'] = 1
    
    # Create rate change request notification
    notification = {
        'id': owner_user_data['nextNotificationId'],
        'type': 'rate_change_request',
        'message': f"📊 Moderator {moderator_name} requests economic rate changes",
        'level': 'warning',
        'read': False,
        'createdAt': datetime.now().isoformat(),
        'from_moderator': moderator_name,
        'changes': changes,
        'reason': reason
    }
    
    owner_user_data['nextNotificationId'] += 1
    owner_user_data['notifications'].append(notification)
    owner_user_data['notifications'] = owner_user_data['notifications'][-100:]
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Rate change request sent to owner'})

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        accounts = load_accounts()
        
        # Find username by email
        username = None
        for uname, acc in accounts.items():
            if acc.get('email') == email:
                username = uname
                break
        
        if not username:
            # Don't reveal if email exists or not (security)
            return jsonify({'success': True, 'message': 'If that email exists, a reset code has been generated.'})
        
        # Generate reset code
        reset_code = secrets.token_urlsafe(16)
        
        resets = load_password_resets()
        resets[reset_code] = {
            'username': username,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        save_password_resets(resets)
        
        # Try to send email
        email_sent = send_reset_email(email, reset_code, username)
        
        if email_sent:
            # Production: Email was sent
            return jsonify({
                'success': True,
                'message': 'Password reset email sent! Check your inbox.'
            })
        else:
            # Development: Show code on screen (SMTP not configured)
            return jsonify({
                'success': True,
                'message': 'Password reset code generated! (Email not configured)',
                'reset_code': reset_code,  # Only shown when SMTP not configured
                'dev_note': 'Configure SMTP environment variables to send emails.'
            })
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        data = request.json
        reset_code = data.get('reset_code', '').strip()
        new_password = data.get('new_password', '')
        
        if not reset_code or not new_password:
            return jsonify({'error': 'Reset code and new password required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        resets = load_password_resets()
        
        if reset_code not in resets:
            return jsonify({'error': 'Invalid reset code'}), 400
        
        reset_data = resets[reset_code]
        
        # Check if expired
        expires_at = datetime.fromisoformat(reset_data['expires_at'])
        if datetime.now() > expires_at:
            del resets[reset_code]
            save_password_resets(resets)
            return jsonify({'error': 'Reset code expired'}), 400
        
        # Update password
        username = reset_data['username']
        accounts = load_accounts()
        
        if username not in accounts:
            return jsonify({'error': 'User not found'}), 404
        
        salt, password_hash = hash_password(new_password)
        accounts[username]['salt'] = salt
        accounts[username]['password_hash'] = password_hash
        save_accounts(accounts)
        
        # Delete used reset code
        del resets[reset_code]
        save_password_resets(resets)
        
        return jsonify({'success': True, 'message': 'Password reset successful!'})
    
    return render_template('reset_password.html')

@app.route('/game')
def game():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    
    # Pass both username and moderator status to template
    is_moderator = session.get('is_moderator', False)
    is_owner = session.get('is_owner', False)
    username = session.get('username', 'Player')
    
    return render_template('game.html', username=username, is_moderator=is_moderator, is_owner=is_owner)

# The full game API routes are provided by the `app_full` blueprint.
# They are registered above when `app_full.bp` is imported.

def initialize_game_data():
    """Initialize default data files if they don't exist."""
    if not STOCKS_FILE.exists():
        save_stocks(load_stocks())
    if not CRYPTO_FILE.exists():
        save_crypto(load_crypto())
    if not SHOP_FILE.exists():
        save_json(SHOP_FILE, load_shop())
    if not CONFIG_FILE.exists():
        save_config(load_config())
    if not ACCOUNTS_FILE.exists():
        save_accounts({})
    if not PASSWORD_RESETS_FILE.exists():
        save_password_resets({})
    
    # Generate initial admin keys if they don't exist
    if not ADMIN_KEYS_FILE.exists():
        admin_keys = {}
        # Generate 5 admin keys for testing
        for i in range(5):
            key = generate_admin_key()
            admin_keys[key] = {
                'created_at': datetime.now().isoformat(),
                'active': True,
                'description': f'Admin Key #{i+1}',
                'last_used': None,
                'last_username': None
            }
        save_admin_keys(admin_keys)
        print(f"Generated {len(admin_keys)} admin keys (available in {ADMIN_KEYS_FILE})")
    
    # Print active admin keys count
    keys = load_admin_keys()
    active_keys = [k for k, v in keys.items() if v.get('active', True)]
    if active_keys:
        print(f"{len(active_keys)} active admin key(s) available")

# Initialize game data when module is imported (works for both development and production)
initialize_game_data()

if __name__ == '__main__':
    # Development server startup messages
    print("\nStarting EconGame server...")
    print("   Home: http://127.0.0.1:5000")
    print("   Player Login: http://127.0.0.1:5000/login")
    print("   Moderator Login: http://127.0.0.1:5000/moderator-login\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
