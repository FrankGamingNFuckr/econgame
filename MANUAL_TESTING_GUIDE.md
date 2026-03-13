# Manual Testing Guide for EconGame

## Getting Started

1. **Open your browser** to: http://127.0.0.1:5000
2. You'll see the home page with options to Login or Register

## Test 1: User Registration & Login

### Register a New Account
1. Click "Register" or go to http://127.0.0.1:5000/register
2. Fill in:
   - Username: `test_player` (or any unique name)
   - Email: `test@example.com` (or any email)
   - Password: `password123` (minimum 6 characters)
3. Click "Register"
4. You'll see a verification link - **copy and paste it** into your browser
5. After verification, return to login page

### Login
1. Go to http://127.0.0.1:5000/login
2. Enter your username and password
3. Click "Login"
4. You should be redirected to the game page

## Test 2: Banking System

### Create Your First Account
1. Navigate to the **"Banking"** tab
2. Select account type (Checking or Savings)
3. Click "Create Account"
4. ✓ You should see confirmation message

### Check Your Balance
- Look at your balance display
- You should see:
  - **Pockets**: Starting balance (used for purchases)
  - **Checking/Savings**: $0 (newly created)
  - **Emergency Fund**: $0

## Test 3: Earning Money

### Regular Work
1. Go to **"Work"** tab
2. Click the **"Work"** button
3. ✓ You should earn $50-$200 randomly
4. Money goes to your **Pockets**
5. Try clicking again - you should see a **10-second cooldown** message
6. Wait 10 seconds and work again

### Government Work
1. In the same **"Work"** tab
2. Click **"Government Job"** button
3. ✓ You should earn $7,500-$30,000 (minus 21% tax)
4. This has a **2-minute cooldown**
5. Check if "Government Shutdown" is active (if so, you'll earn $0)

### Tips to Make Money Fast
- Spam the regular work button (every 10 seconds)
- Use government jobs when available (every 2 minutes)
- Watch your Pockets balance grow!

## Test 4: Banking Operations

### Deposit Money
1. Go back to **"Banking"** tab
2. Make sure you have money in Pockets (work a few times if needed)
3. Enter an amount to deposit (e.g., 500)
4. Select account (checking or savings)
5. Click "Deposit"
6. ✓ Money should move from Pockets to your account

### Withdraw Money
1. In **"Banking"** tab
2. Enter amount to withdraw
3. Select account
4. Click "Withdraw"
5. ✓ Money should move from account to Pockets

## Test 5: Stock Market

### View Stocks
1. Go to **"Stocks"** tab
2. You should see 5 stocks:
   - TECH
   - BANK
   - ENERGY
   - RETAIL
   - PHARMA
3. Each shows current price

### Buy Stocks
1. Work several times to get money in Pockets (need at least $100-$500)
2. Enter ticker symbol (e.g., "TECH")
3. Enter number of shares
4. Click "Buy Stock"
5. ✓ Stock appears in your portfolio

### Sell Stocks
1. If you own stocks, enter ticker and shares
2. Click "Sell Stock"
3. ✓ Money returns to Pockets

## Test 6: Cryptocurrency

### View Crypto
1. Go to **"Crypto"** tab
2. You should see 3 cryptocurrencies:
   - Bitcoin (BTC)
   - Ethereum (ETH)
   - Dogecoin (DOGE)
3. Prices are volatile (±10% per hour)

### Buy Crypto
1. Work to get money in Pockets
2. Enter coin symbol (e.g., "BTC")
3. Enter amount (can be fractional like 0.001)
4. Click "Buy Crypto"
5. ✓ Crypto added to your wallet

## Test 7: Business Empire

### Create a Business
1. Go to **"Businesses"** tab
2. Work until you have **$50,000 in Pockets**
3. Enter a business name
4. Select business type (General, Tech, Retail, Restaurant)
5. Click "Create Business"
6. ✓ Business is created

### Hire Workers
1. Click "Hire Worker" (costs $5,000)
2. Workers generate **$100-$500 per hour** automatically
3. Check back later to see passive income!

## Test 8: Shop & Inventory

### Browse Shop
1. Go to **"Shop"** tab
2. You should see items like:
   - Housing (Apartment $50K, House $150K, Mansion $500K)
   - Collectibles (Cookies, Pink Feet, Jars, etc.)

### Buy Items
1. Work to get money
2. Click "Buy" next to an item
3. ✓ Item added to inventory
4. Some items have ownership limits

## Test 9: Loan System (Advanced)

### Take a Loan
1. Go to **"Loans"** tab
2. Enter loan amount (up to $100,000)
3. Select loan type (Regular or Stock)
4. Click "Take Loan"
5. ✓ Money goes to Pockets
6. 3% daily interest applies
7. 25% of work income auto-pays loans

## Test 10: Dashboard & Stats

### Check Your Progress
1. Go to **"Dashboard"** tab
2. View your:
   - Net worth
   - Total assets
   - Cash on hand
   - Investments
   - Business income

## Common Issues & Solutions

### Issue: "Email verification required"
**Solution**: Check your registration response for the verification link, or check `game_data/accounts.json`

### Issue: "Cooldown" messages
**Solution**: This is normal! Wait for the cooldown timer to expire

### Issue: "Not enough money"
**Solution**: Work more times to earn money in Pockets

### Issue: "Already have account"
**Solution**: You can only create one bank account per user

## Testing Checklist

Complete this checklist to fully test your game:

- [ ] Register new user
- [ ] Verify email
- [ ] Login successfully
- [ ] Create checking account
- [ ] Earn money with regular work
- [ ] Earn money with government work
- [ ] Deposit money to account
- [ ] Withdraw money from account
- [ ] View stock prices
- [ ] Buy at least 1 stock
- [ ] View crypto prices
- [ ] Buy crypto (if you have funds)
- [ ] Create a business (requires $50K)
- [ ] View shop items
- [ ] Buy a shop item
- [ ] Check portfolio
- [ ] Check dashboard
- [ ] Take a loan (optional)
- [ ] Logout and login again

## Advanced Features to Explore

1. **Advisors**: Select an advisor for gameplay modifiers
2. **Illegal Businesses**: Higher risk, higher reward
3. **Robbing**: Rob other players (risky!)
4. **Insurance**: Protect your assets
5. **Leaderboard**: See top players

## Performance Testing

Try these scenarios:
1. Click work button rapidly (should enforce cooldown)
2. Try to withdraw more than you have (should show error)
3. Try to buy stocks with insufficient funds (should show error)
4. Create multiple accounts and test interactions

## What to Look For

### Good Signs ✓
- Smooth page navigation
- Clear error messages
- Balance updates immediately
- Cooldown timers work
- No crashes or 500 errors

### Potential Issues ✗
- Page doesn't load
- Buttons don't respond
- Balance doesn't update
- Error messages unclear
- Session expires unexpectedly

---

## Need Help?

- Check browser console (F12) for JavaScript errors
- Check server terminal for Python errors
- Review `TEST_REPORT.md` for automated test results
- Check `game_data/` JSON files for data integrity

**Have fun testing your economy game!** 💰🎮
