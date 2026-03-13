# 💰 EconGame - Full Economy Simulator

A comprehensive multiplayer economic simulation game based on your Discord bot, now playable in your web browser!

## 🎮 Complete Feature Set

### 🏦 Banking System
- **Multiple Accounts**: Checking, Savings, Pockets, Emergency Fund
- **Account Management**: Deposit, withdraw, and transfer between accounts
- **Interest**: Earn interest on savings accounts (processed hourly)
- **Emergency Fund**: Special account with $250,000 cap

### 💼 Work Systems
- **Regular Work**: Earn $50-$200 per job (10 second cooldown)
- **Government Jobs**: Higher pay ($7,500-$30,000) but taxed at ~21% (2 minute cooldown)
- **Government Shutdown**: When active, government jobs pay nothing!
- **Loan Collections**: 25% of wages automatically go to outstanding loans

### 🏢 Business Empire
- **Create Businesses**: Start your own company for $50,000
- **Hire Workers**: Each worker costs $5,000 and generates hourly revenue
- **Passive Income**: Businesses earn money every hour automatically
- **Multiple Types**: General, Tech, Retail, Restaurant

### 📈 Stock Market
- **5 Stocks**: TECH, BANK, ENERGY, RETAIL, PHARMA
- **Buy & Sell**: Trade stocks at market prices
- **Portfolio Tracking**: Monitor your investments
- **Price Fluctuations**: Prices update hourly
- **Recession Impact**: Stock prices drop extra -2% during recessions

### ₿ Cryptocurrency
- **3 Coins**: Bitcoin (BTC), Ethereum (ETH), Dogecoin (DOGE)
- **High Volatility**: Prices can swing ±10% per hour
- **Crypto Wallet**: Track all your holdings
- **Fractional Amounts**: Buy any amount (0.001 BTC, etc.)

### 💳 Loan System
- **Two Loan Types**: Regular loans and Stock loans
- **Borrow up to $100,000**: Get cash instantly
- **Daily Interest**: 3% compounding interest
- **Automatic Collections**: 25% of work income goes to loan payments
- **Collections Mode**: Miss payments and face stricter terms

### 🛒 Shop & Inventory
- **Housing**: Apartments ($50K), Houses ($150K), Mansions ($500K)
- **Collectibles**: Cookies, Pink Feet, Feet Pics, Jars, Anime Figurines
- **Ownership Limits**: Some items have max ownership caps
- **Rent Payments**: Housing generates rent expenses (hourly/daily)

### 🦹 Robbery & Crime
- **Rob Other Players**: Steal 10-30% of their pockets
- **50% Success Rate**: Get caught? Go to jail for 2 minutes!
- **Insurance System**: Buy insurance for $10,000 to protect against robberies
- **Insurance Payout**: Get 50% back if robbed while insured
- **Arrest Tracking**: Track how many times you've been caught

### 📊 Economic Events
- **Government Shutdown**: Disables all government job income
- **Recession**: Stocks drop an extra 2% per hour
- **Depression Mode**: Severe economic downturn (ready but not implemented)
- **Dynamic Interest Rates**: Affects loans and savings
- **Central Bank**: Tracks money supply

### 🏆 Leaderboard
- **Top 10 Richest Players**: See who's dominating the economy
- **Net Worth Tracking**: Total of all account balances
- **Player IDs**: First 8 characters shown for robbery targeting

### ⚙️ Admin Controls
- **Toggle Shutdown**: Turn government shutdown on/off
- **Toggle Recession**: Enable/disable recession mode
- **Process Hourly**: Manually trigger hourly updates
- **View Player ID**: Get your ID for sharing with friends

## 🚀 Setup & Installation

### 1. Install Python
Make sure you have Python 3.7+ installed.

### 2. Install Dependencies
```bash
pip install Flask
```

### 3. Run the Game

**For local play:**
```bash
python app_full.py
```

Then open your browser to: `http://127.0.0.1:5000`

**For multiplayer with friends on same network:**

1. Edit `app_full.py` and change the last line to:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. Find your local IP address:
   - **Windows**: Run `ipconfig` in Command Prompt, look for "IPv4 Address"
   - **Mac/Linux**: Run `ifconfig` or `ip addr` in Terminal

3. Share your IP with friends:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```
   Example: `http://192.168.1.100:5000`

## 🎯 How to Play

### Getting Started
1. **Create Account**: Choose Checking or Savings as your primary account
2. **Work Jobs**: Start with regular work to build initial capital
3. **Build Empire**: Invest in businesses, stocks, or crypto
4. **Manage Finances**: Keep money in different accounts for organization

### Strategies
- **Early Game**: Focus on government jobs for high income
- **Mid Game**: Create businesses for passive income
- **Late Game**: Diversify into stocks and crypto
- **Risk Management**: Buy insurance before accumulating too much wealth
- **Loan Strategy**: Only borrow if you can handle 3% daily interest

### Tips & Tricks
- Emergency fund is capped at $250K but provides security
- Savings accounts earn interest hourly
- Businesses with more workers = more revenue
- Stocks are safer than crypto but less profitable
- Rob players when they have high pocket balances (risky!)
- Insurance halves your losses from robberies

## 🔧 Customization

### Modify Work Messages
Edit the arrays in `app_full.py`:
```python
WORK_MESSAGES = [...]
GOV_MESSAGES = [...]
```

### Adjust Economic Parameters
In `app_full.py` `load_config()` function:
- `taxRate`: Base tax rate (10%)
- `govTaxPercent`: Government job tax (21%)
- `interestRate`: Loan/savings interest (3%)
- `emergencyCap`: Emergency fund max ($250,000)

### Change Colors
Edit `static/game.css`:
- Main gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Button colors: `.btn`, `.btn-primary`, `.btn-success`, etc.

### Modify Stock/Crypto Prices
Edit starting prices in `load_stocks()` and `load_crypto()` functions

## 📁 Game Data Storage

All game data is stored in JSON files in the `game_data/` directory:
- `users.json`: Player accounts, balances, inventory
- `businesses.json`: All created businesses
- `stocks.json`: Stock prices and history
- `crypto.json`: Cryptocurrency prices and history
- `config.json`: Game configuration and economic settings
- `shop.json`: Available items for purchase

**Note**: Data persists between server restarts!

## ⚠️ Security & Multiplayer

**Safe for Local Networks:**
- Use on home WiFi with trusted friends
- Each player gets unique session ID
- Data isolated per player

**NOT for Public Internet:**
- No authentication system
- No encryption
- No protection against exploits
- Use only on private trusted networks

**Cheating Prevention:**
- All calculations done server-side
- Cooldowns enforced on backend
- Transaction validation
- Balance checks before purchases

## 🔄 Hourly Processing

The game processes these updates every hour (manually triggered):
1. **Stock Prices**: Random fluctuation ±5% (±7% during recession)
2. **Crypto Prices**: Random fluctuation ±10%
3. **Business Revenue**: Each worker generates $100-$500
4. **Loan Interest**: 3% daily interest applied (hourly)
5. **Savings Interest**: Earn interest on savings accounts

**To trigger manually**: Go to Admin tab → "Process Hourly Updates"

## 🎨 UI Features

- **Tabbed Interface**: 11 different sections
- **Live Stats**: Header shows all account balances in real-time
- **Modal Popups**: Clean message system for all actions
- **Responsive Design**: Works on desktop and mobile
- **Color-Coded**: Different colors for different actions
- **Cooldown Timers**: Visual feedback on work cooldowns

## 🐛 Troubleshooting

**"Module not found" error:**
```bash
pip install Flask
```

**Port already in use:**
- Change port to 5001 in `app_full.py` last line
- Or kill the process using port 5000

**Game data lost:**
- Check that `game_data/` folder exists
- Don't delete JSON files while server is running

**Can't connect multiplayer:**
- Make sure friends are on same WiFi/network
- Check firewall isn't blocking port 5000
- Verify you're using `host='0.0.0.0'`

## 🚧 Future Enhancements

Potential additions:
- Real-time multiplayer chat
- Scheduled hourly updates (background cron)
- More economic events (inflation, deflation, boom)
- Achievement system
- Business upgrades and specializations
- Stock market crashes
- Cryptocurrency mining
- Player trading system
- Mortgage system for housing
- Tax refund system

## 📝 Credits

Based on the Discord bot economy system with full feature parity:
- All major features from Discord bot implemented
- Web-based interface for easier access
- Persistent data storage
- Multiplayer support via LAN/WiFi

---

**Enjoy building your economic empire! 💰🏢📈**
