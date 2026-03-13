# 🧪 Testing Guide - EconGame Authentication & Moderation

## Quick Start

Your server is now running at: **http://127.0.0.1:5000**

## What's New?

✅ **Home Screen** - Welcome page with options to login or register  
✅ **User Login** - Regular players can create accounts and play  
✅ **Moderator Login** - Admin access with special keys  
✅ **Admin Tab** - Only visible to moderators  
✅ **Moderator Badge** - Shows who has admin access  

---

## Test Scenarios

### 1. Regular User Flow

1. **Visit Home Page**
   - Go to: http://127.0.0.1:5000
   - You'll see the home screen with "Login" and "Create Account" buttons

2. **Create Account**
   - Click "Create Account"
   - Fill in:
     - Username: `testplayer`
     - Email: `test@example.com`
     - Password: `password123`
   - Submit
   - You'll be auto-logged in and redirected to the game

3. **Play the Game**
   - Notice: **NO Admin tab** is visible (only for moderators)
   - Your username appears in the header
   - You can see all 10 tabs except Admin
   - Test the /api/balance endpoint to verify auth is working

4. **Logout**
   - Click "Logout" link in header
   - You're redirected to home page

5. **Login Again**
   - Click "Login" on home page
   - Enter credentials
   - Access granted!

---

### 2. Moderator Flow

1. **Visit Home Page**
   - Go to: http://127.0.0.1:5000
   - Scroll down to see "Moderator Login" button

2. **Moderator Login**
   - Click "🛡️ Moderator Login"
   - Enter:
     - Username: `Admin` (or any name you want)
     - Admin Key: Use one of the keys below

   **Available Admin Keys:**
   ```
   0dQjx0zm-TEHaLYNyY0hs-Fsf7YglFgT_7AJdFTNJhM
   UV3d3kFQG_7ygDhFnAxTAbWbxFIkNmgzMuZVa-zKp10
   VpUJ8cyrT1W7YyYf6cq6MCdj4-GX7HqBt_GHfUe4TT4
   HcJanwHuGbegh1bnTPfoFxeJ9kgeH08VQ7vXVAq2_oo
   7wU-iuW6ICfM5IfWBjnjgKwgHBuwpUsC8sdUR9ejIPk
   ```

3. **Verify Moderator Access**
   - After login, you'll see:
     - ✅ Your username + **🛡️ MODERATOR** badge in header
     - ✅ **11 tabs** including the Admin tab
     - ✅ Admin controls: Toggle Shutdown, Toggle Recession, Process Hourly

4. **Test Admin Features**
   - Click on "Admin" tab
   - Try toggling government shutdown
   - Try toggling recession
   - These affect the economy for all players!

---

## Testing Checklist

### Home Screen
- [ ] Visit http://127.0.0.1:5000
- [ ] See welcome screen with logo
- [ ] See "Login" and "Create Account" buttons
- [ ] See "Moderator Login" button
- [ ] See 6 feature cards

### Regular User Registration
- [ ] Click "Create Account"
- [ ] Fill in username (min 3 chars)
- [ ] Fill in email (must have @)
- [ ] Fill in password (min 6 chars)
- [ ] Submit and auto-login works
- [ ] Redirected to game
- [ ] Username shows in header
- [ ] NO moderator badge
- [ ] NO admin tab visible

### Regular User Login
- [ ] Logout first
- [ ] Click "Login" on home
- [ ] Enter username/password
- [ ] Login successful
- [ ] Game loads

### Password Reset (Optional)
- [ ] Click "Forgot Password" on login page
- [ ] Enter email
- [ ] Reset code appears on screen
- [ ] Copy the code
- [ ] Go to reset password page
- [ ] Enter code + new password
- [ ] Login with new password

### Moderator Login
- [ ] Visit http://127.0.0.1:5000/moderator-login
- [ ] Enter username (anything)
- [ ] Paste admin key from list above
- [ ] Submit
- [ ] See "Moderator access granted" message
- [ ] Redirected to game
- [ ] **MODERATOR** badge visible in header
- [ ] Admin tab IS visible (11 tabs total)

### Admin Features (Moderator Only)
- [ ] Click "Admin" tab
- [ ] See "Admin Controls" heading
- [ ] See 3 buttons:
  - [ ] Toggle Government Shutdown
  - [ ] Toggle Recession
  - [ ] Process Hourly Updates
- [ ] Click shutdown button - success message
- [ ] Click recession button - success message

### Session Management
- [ ] After login, refresh page - still logged in
- [ ] Click logout - redirected to home
- [ ] Try accessing /game without login - redirected to home

---

## Admin Keys Explained

**Where are they stored?**
- File: `game_data/admin_keys.json`
- Contains 5 pre-generated keys
- Each key tracks when it was last used and by whom

**Key Features:**
- Keys never expire (unless manually deactivated)
- Multiple moderators can use different keys
- You can see which key was used by which username
- Keys are generated using cryptographically secure random tokens

**Generate More Keys:**
You can manually add more keys to `admin_keys.json`:
```json
{
  "YOUR-NEW-KEY-HERE": {
    "created_at": "2026-03-12T00:00:00",
    "active": true,
    "description": "Custom Admin Key",
    "last_used": null,
    "last_username": null
  }
}
```

---

## Differences: Regular Users vs Moderators

| Feature | Regular User | Moderator |
|---------|-------------|-----------|
| Login Method | Username + Password | Admin Key |
| Create Account | Yes (email required) | No (just use key) |
| Password Reset | Yes | N/A |
| Tabs Visible | 10 (no admin) | 11 (with admin) |
| Header Badge | None | 🛡️ MODERATOR |
| Can Toggle Shutdown | ❌ No | ✅ Yes |
| Can Toggle Recession | ❌ No | ✅ Yes |
| Can Process Hourly | ❌ No | ✅ Yes |
| Data Persists | Yes (in accounts.json) | Yes (in users.json) |

---

## File Structure

```
game_data/
├── accounts.json          # Regular user login credentials
├── users.json             # All player game data (including moderators)
├── admin_keys.json        # Moderator access keys
├── password_resets.json   # Password reset tokens
├── businesses.json        # Business data
├── stocks.json            # Stock market data
├── crypto.json            # Cryptocurrency data
├── config.json            # Game configuration
└── (created as needed)
```

---

## Common Issues

### "Admin tab not showing up"
- You must login via `/moderator-login` with a valid admin key
- Regular user accounts cannot see admin tab, even if they're moderators

### "Invalid admin key"
- Copy the exact key from the list above (no spaces)
- Keys are case-sensitive
- Check `game_data/admin_keys.json` for active keys
- Make sure the key has `"active": true`

### "Server not starting"
- Make sure port 5000 is not in use: `netstat -ano | findstr :5000`
- Check the terminal for errors
- Try: `python app_auth.py`

---

## Next Steps (Development)

Currently, `app_auth.py` has:
- ✅ Full authentication system
- ✅ Moderator access control
- ✅ Password reset
- ⚠️ Only `/api/balance` endpoint (limited game functionality)

To get full game features:
1. Copy routes from `app_full.py` to `app_auth.py`
2. Or run `app_full.py` for testing game mechanics (no auth)

**For now, you can:**
- Test authentication flow ✅
- Test moderator access ✅
- Create multiple user accounts ✅
- Login/logout ✅
- See admin tab as moderator ✅

**To play the full game:**
- Use `app_full.py` for now (no authentication)
- Or wait until all game routes are added to `app_auth.py`

---

## 🎮 Ready to Test!

1. Server running at: http://127.0.0.1:5000
2. Try creating a regular account
3. Then logout and login as moderator with a key
4. Notice the difference (admin tab appears!)

Enjoy testing! 🚀
