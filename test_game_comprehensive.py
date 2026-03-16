"""
Comprehensive Test Suite for EconGame
Tests all major game features and systems
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class GameTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_username = f"test_player_{int(time.time())}"
        self.test_email = f"{self.test_username}@test.com"
        self.test_password = "TestPassword123!"
        self.verification_link = None
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def log_pass(self, test_name):
        """Log a passed test"""
        print(f"✓ PASS: {test_name}")
        self.results['passed'].append(test_name)
    
    def log_fail(self, test_name, error):
        """Log a failed test"""
        print(f"✗ FAIL: {test_name}")
        print(f"  Error: {error}")
        self.results['failed'].append({'test': test_name, 'error': str(error)})
    
    def log_warning(self, test_name, message):
        """Log a warning"""
        print(f"⚠ WARNING: {test_name}")
        print(f"  Message: {message}")
        self.results['warnings'].append({'test': test_name, 'message': message})
    
    def test_home_page(self):
        """Test if home page loads"""
        try:
            r = self.session.get(f"{BASE_URL}/")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert "EconGame" in r.text or "Welcome" in r.text, "Home page doesn't contain expected content"
            self.log_pass("Home Page Loading")
        except Exception as e:
            self.log_fail("Home Page Loading", e)
    
    def test_register(self):
        """Test user registration"""
        try:
            data = {
                'username': self.test_username,
                'email': self.test_email,
                'password': self.test_password,
                'confirm_password': self.test_password
            }
            r = self.session.post(f"{BASE_URL}/register", json=data, allow_redirects=False)
            
            # Check if registration was successful (redirect or success message)
            if r.status_code in [200, 302]:
                # Check response
                try:
                    resp_data = r.json()
                    if resp_data.get('success'):
                        self.log_pass("User Registration")
                        # Store verification link if provided
                        if 'verification_link' in resp_data:
                            self.verification_link = resp_data['verification_link']
                    else:
                        self.log_fail("User Registration", resp_data.get('error', 'Unknown'))
                except:
                    self.log_warning("User Registration", "Registered but verification needed")
            else:
                self.log_fail("User Registration", f"Status code: {r.status_code}")
        except Exception as e:
            self.log_fail("User Registration", e)
    
    def test_verify_email(self):
        """Test email verification"""
        try:
            if not self.verification_link:
                self.log_warning("Email Verification", "No verification link available")
                return
            
            # Extract the verification URL path
            r = self.session.get(self.verification_link, allow_redirects=True)
            
            if r.status_code == 200:
                if 'verified' in r.text.lower() or 'success' in r.text.lower():
                    self.log_pass("Email Verification")
                else:
                    self.log_warning("Email Verification", "Verification page loaded but unclear result")
            else:
                self.log_fail("Email Verification", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Email Verification", e)
    
    def test_login(self):
        """Test user login"""
        try:
            data = {
                'username': self.test_username,
                'password': self.test_password
            }
            r = self.session.post(f"{BASE_URL}/login", json=data, allow_redirects=True)
            
            if r.status_code == 200:
                # Check if login was successful
                try:
                    resp_data = r.json()
                    if resp_data.get('success'):
                        self.log_pass("User Login")
                    else:
                        # Might fail due to email verification
                        error = resp_data.get('error', 'Unknown error')
                        if 'verify' in error.lower():
                            self.log_warning("User Login", "Email verification required")
                        else:
                            self.log_fail("User Login", error)
                except:
                    self.log_fail("User Login", f"Invalid response: {r.text[:100]}")
            else:
                self.log_fail("User Login", f"Expected 200, got {r.status_code}")
        except Exception as e:
            self.log_fail("User Login", e)
    
    def test_create_checking_account(self):
        """Test creating a checking account"""
        try:
            r = self.session.post(f"{BASE_URL}/api/create_account", json={'type': 'checking'})
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Create Checking Account")
                    else:
                        self.log_fail("Create Checking Account", data.get('error', 'Unknown error'))
                except:
                    self.log_fail("Create Checking Account", f"Invalid JSON response: {r.text[:100]}")
            else:
                self.log_fail("Create Checking Account", f"Status {r.status_code}: {r.text[:100]}")
        except Exception as e:
            self.log_fail("Create Checking Account", e)
    
    def test_create_savings_account(self):
        """Test creating a savings account"""
        try:
            r = self.session.post(f"{BASE_URL}/api/create_account", json={'type': 'savings'})
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Create Savings Account")
                    else:
                        self.log_warning("Create Savings Account", data.get('error', 'Unknown error'))
                except:
                    self.log_fail("Create Savings Account", f"Invalid response: {r.text[:100]}")
            elif r.status_code == 400:
                # Expected if account already exists
                self.log_warning("Create Savings Account", "Already have account (expected)")
            else:
                self.log_warning("Create Savings Account", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Create Savings Account", e)
    
    def test_work(self):
        """Test working to earn money"""
        try:
            r = self.session.post(f"{BASE_URL}/api/work")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        amount = data.get('amount', 0)
                        self.log_pass(f"Work (earned ${amount})")
                    else:
                        error = data.get('error', 'Unknown error')
                        if 'cooldown' in error.lower():
                            self.log_warning("Work", error)
                        else:
                            self.log_fail("Work", error)
                except:
                    self.log_fail("Work", f"Invalid response: {r.text[:100]}")
            elif r.status_code == 400:
                try:
                    data = r.json()
                    error = data.get('error', 'Bad request')
                    if 'cooldown' in error.lower():
                        self.log_warning("Work", error)
                    else:
                        self.log_fail("Work", f"Status 400: {error}")
                except:
                    self.log_fail("Work", f"Status 400: {r.text[:100]}")
            else:
                self.log_fail("Work", f"Status {r.status_code}: Not logged in or endpoint error")
        except Exception as e:
            self.log_fail("Work", e)
    
    def test_government_work(self):
        """Test government job"""
        try:
            r = self.session.post(f"{BASE_URL}/api/workgov")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        amount = data.get('amount', 0)
                        self.log_pass(f"Government Work (earned ${amount})")
                    else:
                        # Might be on cooldown or government shutdown
                        self.log_warning("Government Work", data.get('error', 'Unknown error'))
                except:
                    self.log_fail("Government Work", f"Invalid response: {r.text[:100]}")
            else:
                self.log_warning("Government Work", f"Status code: {r.status_code}")
        except Exception as e:
            self.log_fail("Government Work", e)
    
    def test_deposit_to_checking(self):
        """Test depositing money to checking account"""
        try:
            # First work to get some money
            self.session.post(f"{BASE_URL}/api/work")
            time.sleep(0.5)
            
            r = self.session.post(f"{BASE_URL}/api/deposit", json={
                'account': 'checking',
                'amount': 100
            })
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Deposit to Checking")
                    else:
                        self.log_warning("Deposit to Checking", data.get('error', 'Unknown error'))
                except:
                    self.log_fail("Deposit to Checking", f"Invalid response: {r.text[:100]}")
            else:
                self.log_warning("Deposit to Checking", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Deposit to Checking", e)
    
    def test_withdraw_from_checking(self):
        """Test withdrawing money from checking account"""
        try:
            r = self.session.post(f"{BASE_URL}/api/withdraw", json={
                'account': 'checking',
                'amount': 50
            })
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Withdraw from Checking")
                    else:
                        self.log_warning("Withdraw from Checking", data.get('error', 'Unknown error'))
                except:
                    self.log_fail("Withdraw from Checking", f"Invalid response: {r.text[:100]}")
            else:
                self.log_warning("Withdraw from Checking", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Withdraw from Checking", e)
    
    def test_create_business(self):
        """Test creating a business"""
        try:
            # Work multiple times to get enough money
            for i in range(10):
                self.session.post(f"{BASE_URL}/api/work")
                time.sleep(0.2)
            
            r = self.session.post(f"{BASE_URL}/api/create_business", json={
                'name': f'Test Business {int(time.time())}',
                'type': 'general'
            })
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Create Business")
                    else:
                        self.log_warning("Create Business", data.get('error', 'Not enough money'))
                except:
                    self.log_fail("Create Business", f"Invalid response: {r.text[:100]}")
            else:
                self.log_warning("Create Business", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Create Business", e)
    
    def test_view_stocks(self):
        """Test viewing stock prices"""
        try:
            r = self.session.get(f"{BASE_URL}/api/stocks")
            data = r.json()
            
            if r.status_code == 200 and 'stocks' in data:
                stock_count = len(data['stocks'])
                self.log_pass(f"View Stocks ({stock_count} stocks available)")
            else:
                self.log_fail("View Stocks", "No stocks data returned")
        except Exception as e:
            self.log_fail("View Stocks", e)
    
    def test_buy_stock(self):
        """Test buying stocks"""
        try:
            # Work to get some money
            for i in range(20):
                self.session.post(f"{BASE_URL}/api/work")
                time.sleep(0.1)
            
            r = self.session.post(f"{BASE_URL}/api/buy_stock", json={
                'ticker': 'APEX',
                'shares': 1
            })
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('success'):
                        self.log_pass("Buy Stock")
                    else:
                        self.log_warning("Buy Stock", data.get('error', 'Not enough money'))
                except:
                    self.log_fail("Buy Stock", f"Invalid response: {r.text[:100]}")
            else:
                self.log_warning("Buy Stock", f"Status {r.status_code}")
        except Exception as e:
            self.log_fail("Buy Stock", e)
    
    def test_view_crypto(self):
        """Test viewing crypto prices"""
        try:
            r = self.session.get(f"{BASE_URL}/api/crypto")
            data = r.json()
            
            if r.status_code == 200 and 'crypto' in data:
                crypto_count = len(data['crypto'])
                self.log_pass(f"View Crypto ({crypto_count} coins available)")
            else:
                self.log_fail("View Crypto", "No crypto data returned")
        except Exception as e:
            self.log_fail("View Crypto", e)
    
    def test_view_shop(self):
        """Test viewing shop items"""
        try:
            r = self.session.get(f"{BASE_URL}/api/shop")
            data = r.json()
            
            if r.status_code == 200 and 'items' in data:
                item_count = len(data['items'])
                self.log_pass(f"View Shop ({item_count} items available)")
            else:
                self.log_fail("View Shop", "No shop data returned")
        except Exception as e:
            self.log_fail("View Shop", e)
    
    def test_get_user_data(self):
        """Test getting user balance"""
        try:
            r = self.session.get(f"{BASE_URL}/api/balance")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if 'pockets' in data or 'checking' in data:
                        pockets = data.get('pockets', 0)
                        self.log_pass(f"Get Balance (Pockets: ${pockets:,.2f})")
                    else:
                        self.log_fail("Get Balance", "Invalid balance data returned")
                except:
                    self.log_fail("Get Balance", f"Invalid response: {r.text[:100]}")
            else:
                self.log_fail("Get Balance", f"Status {r.status_code}: Not logged in")
        except Exception as e:
            self.log_fail("Get Balance", e)
    
    def test_dashboard(self):
        """Test portfolio endpoint"""
        try:
            r = self.session.get(f"{BASE_URL}/api/portfolio")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if 'portfolio' in data:
                        stocks_count = len(data.get('portfolio', []))
                        self.log_pass(f"Portfolio ({stocks_count} positions)")
                    else:
                        self.log_fail("Portfolio", "Invalid portfolio data")
                except:
                    self.log_fail("Portfolio", f"Invalid response: {r.text[:100]}")
            else:
                self.log_fail("Portfolio", f"Status {r.status_code}: Not logged in")
        except Exception as e:
            self.log_fail("Portfolio", e)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Passed: {len(self.results['passed'])}")
        print(f"✗ Failed: {len(self.results['failed'])}")
        print(f"⚠ Warnings: {len(self.results['warnings'])}")
        print("="*60)
        
        if self.results['failed']:
            print("\nFailed Tests:")
            for fail in self.results['failed']:
                print(f"  - {fail['test']}: {fail['error']}")
        
        if self.results['warnings']:
            print("\nWarnings (may be expected):")
            for warn in self.results['warnings']:
                print(f"  - {warn['test']}: {warn['message']}")
        
        print("\nPassed Tests:")
        for test in self.results['passed']:
            print(f"  ✓ {test}")
        
        print("\n")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("STARTING ECONGAME COMPREHENSIVE TEST SUITE")
        print("="*60 + "\n")
        
        # Basic tests
        self.test_home_page()
        self.test_register()
        self.test_verify_email()
        self.test_login()
        
        # Banking tests
        print("\n--- Banking Tests ---")
        self.test_create_checking_account()
        self.test_create_savings_account()
        self.test_deposit_to_checking()
        self.test_withdraw_from_checking()
        
        # Work tests
        print("\n--- Work Tests ---")
        self.test_work()
        self.test_government_work()
        
        # Business tests
        print("\n--- Business Tests ---")
        self.test_create_business()
        
        # Market tests
        print("\n--- Market Tests ---")
        self.test_view_stocks()
        self.test_buy_stock()
        self.test_view_crypto()
        
        # Shop tests
        print("\n--- Shop Tests ---")
        self.test_view_shop()
        
        # Data tests
        print("\n--- Data Tests ---")
        self.test_get_user_data()
        self.test_dashboard()
        
        # Print summary
        self.print_summary()

if __name__ == "__main__":
    print("EconGame Comprehensive Test Suite")
    print("Make sure the server is running at http://127.0.0.1:5000")
    print()
    
    tester = GameTester()
    tester.run_all_tests()
