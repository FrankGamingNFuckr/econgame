// Tab Management
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'businesses') { loadBusinesses(); loadIllegalBusinesses(); }
    if (tabName === 'stocks') { loadStocks(); loadPortfolio(); }
    if (tabName === 'crypto') { loadCrypto(); loadWallet(); }
    if (tabName === 'loans') loadLoans();
    if (tabName === 'shop') { loadShop(); loadInventory(); }
    if (tabName === 'leaderboard') loadLeaderboard();
    if (tabName === 'dashboard') loadDashboard();
}

// Initialize tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchTab(btn.dataset.tab);
    });
});

// Modal Management
function showModal(message) {
    document.getElementById('modal-message').innerHTML = message;
    document.getElementById('message-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('message-modal').classList.remove('active');
}

// Update header stats
async function updateStats() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();
        
        document.getElementById('stat-checking').textContent = '$' + data.checking.toLocaleString();
        document.getElementById('stat-savings').textContent = '$' + data.savings.toLocaleString();
        document.getElementById('stat-pockets').textContent = '$' + data.pockets.toLocaleString();
        document.getElementById('stat-emergency').textContent = '$' + data.emergency.toLocaleString();
        
        // Show/hide banking controls
        if (data.hasAccount) {
            document.getElementById('create-account-section').style.display = 'none';
            document.getElementById('banking-controls').style.display = 'block';
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// ==================== BANKING ====================

async function createAccount(type) {
    try {
        const response = await fetch('/api/create_account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error creating account');
    }
}

async function deposit() {
    const amount = parseInt(document.getElementById('deposit-amount').value);
    const target = document.getElementById('deposit-target').value;
    
    if (!amount || amount <= 0) {
        showModal('❌ Please enter a valid amount');
        return;
    }
    
    try {
        const response = await fetch('/api/deposit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, target })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Deposited $${data.amount.toLocaleString()} to ${target}`);
            document.getElementById('deposit-amount').value = '';
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error depositing');
    }
}

async function withdraw() {
    const amount = parseInt(document.getElementById('withdraw-amount').value);
    const source = document.getElementById('withdraw-source').value;
    
    if (!amount || amount <= 0) {
        showModal('❌ Please enter a valid amount');
        return;
    }
    
    try {
        const response = await fetch('/api/withdraw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, source })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Withdrew $${amount.toLocaleString()} from ${source}`);
            document.getElementById('withdraw-amount').value = '';
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error withdrawing');
    }
}

// ==================== WORK ====================

async function doWork() {
    try {
        const response = await fetch('/api/work', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showModal(`💼 ${data.message}`);
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error working');
    }
}

async function doWorkGov() {
    try {
        const response = await fetch('/api/workgov', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showModal(`🏛️ ${data.message}`);
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error working');
    }
}

// ==================== BUSINESSES ====================

async function createBusiness() {
    const name = document.getElementById('business-name').value.trim();
    const type = document.getElementById('business-type').value;
    
    if (!name || name.length < 3) {
        showModal('❌ Business name must be at least 3 characters');
        return;
    }
    
    try {
        const response = await fetch('/api/create_business', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Created business: ${data.business.name}`);
            document.getElementById('business-name').value = '';
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error creating business');
    }
}

async function loadBusinesses() {
    try {
        const response = await fetch('/api/businesses');
        const data = await response.json();
        
        const container = document.getElementById('businesses-list');
        
        if (data.businesses.length === 0) {
            container.innerHTML = '<p class="text-muted">No businesses yet. Create one to start earning passive income!</p>';
            return;
        }
        
        container.innerHTML = data.businesses.map(b => `
            <div class="card business-item">
                <div>
                    <h4>${b.name}</h4>
                    <p>Type: ${b.type} | Workers: ${b.workers}</p>
                    <p>Hourly Revenue: $${b.revenue.toLocaleString()} | Total Earnings: $${b.totalEarnings.toLocaleString()}</p>
                </div>
                <button onclick="hireWorker('${b.id}')" class="btn btn-primary">Hire Worker ($5,000)</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading businesses:', error);
    }
}

async function hireWorker(businessId) {
    try {
        const response = await fetch('/api/hire_worker', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Hired a worker! Now have ${data.workers} workers.`);
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error hiring worker');
    }
}

async function createIllegalBusiness() {
    const name = document.getElementById('illegal-business-name').value.trim();
    const type = document.getElementById('illegal-business-type').value;

    try {
        const response = await fetch('/api/create_illegal_business', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type })
        });

        const data = await response.json();
        if (response.ok) {
            showModal(`✅ Illegal operation created: ${data.business.name} (Cost: $${data.startup_cost.toLocaleString()})`);
            document.getElementById('illegal-business-name').value = '';
            updateStats();
            loadIllegalBusinesses();
            loadNotifications();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error creating illegal business');
    }
}

async function loadIllegalBusinesses() {
    try {
        const response = await fetch('/api/illegal_businesses');
        const data = await response.json();

        const container = document.getElementById('illegal-businesses-list');
        if (!container) return;

        if (!data.businesses || data.businesses.length === 0) {
            container.innerHTML = '<p class="text-muted">No illegal operations yet.</p>';
            return;
        }

        container.innerHTML = data.businesses.map(b => {
            const cooldownText = b.cooldownRemainingMs > 0
                ? `⏳ Cooldown: ${b.cooldownLabel}`
                : '✅ Ready to run';

            const raidPercent = (b.risk && b.risk.raidPercent !== undefined) ? b.risk.raidPercent : 0;
            const riskColor = raidPercent >= 30 ? '#d9534f' : (raidPercent >= 20 ? '#f0ad4e' : '#5cb85c');
            const payoutMin = (b.risk && b.risk.minPayout) ? b.risk.minPayout : 0;
            const payoutMax = (b.risk && b.risk.maxPayout) ? b.risk.maxPayout : 0;
            const detailId = `illegal-risk-detail-${b.id}`;

            const history = (b.history || []).slice(-5).reverse();
            const historyHtml = history.length > 0
                ? history.map(h => `
                    <li>
                        <small>${new Date(h.at).toLocaleTimeString()} — ${h.success ? 'Success' : 'Raid'}
                        ${h.success ? `(+ $${(h.payout || 0).toLocaleString()})` : `(- $${(h.fine || 0).toLocaleString()})`}</small>
                    </li>
                `).join('')
                : '<li><small>No history yet.</small></li>';

            return `
            <div class="card" style="border-left: 4px solid #b33;">
                <div style="display:flex; justify-content:space-between; gap:12px; align-items:center;">
                    <div>
                        <h4>${b.name}</h4>
                        <p>Type: ${b.type} | Runs: ${b.runs || 0}</p>
                        <p>Total Earnings: $${(b.totalEarnings || 0).toLocaleString()}</p>
                        <p>Expected Payout: $${payoutMin.toLocaleString()} - $${payoutMax.toLocaleString()}</p>
                        <p style="margin-bottom: 4px;">Risk Meter: ${raidPercent}% raid chance</p>
                        <div style="width: 220px; max-width: 100%; height: 10px; background: #eee; border-radius: 8px; overflow: hidden;">
                            <div style="height: 100%; width: ${Math.min(100, raidPercent)}%; background: ${riskColor};"></div>
                        </div>
                        <div class="risk-legend">Legend: <span class="risk-low">Low &lt;20%</span> | <span class="risk-medium">Medium 20-29%</span> | <span class="risk-high">High 30%+</span></div>
                        <p style="margin-top: 8px;">
                            <a href="#" onclick="toggleIllegalRiskDetails('${detailId}'); return false;">Show Details</a>
                        </p>
                        <div id="${detailId}" style="display:none; margin-top: 8px; padding: 8px; background: #f7f7f7; border-radius: 6px;">
                            <small>
                                Base Raid: ${(b.risk?.baseRaidPercent ?? 0)}%<br>
                                Modified Raid: ${(b.risk?.raidPercent ?? 0)}%<br>
                                Base Payout: $${((b.risk?.baseMinPayout ?? 0)).toLocaleString()} - $${((b.risk?.baseMaxPayout ?? 0)).toLocaleString()}<br>
                                Modified Payout: $${((b.risk?.minPayout ?? 0)).toLocaleString()} - $${((b.risk?.maxPayout ?? 0)).toLocaleString()}<br>
                                Advisor Note: ${b.risk?.advisorNote || 'N/A'}
                            </small>
                        </div>
                        <p>${cooldownText}</p>
                        <p><small>Recent outcomes:</small></p>
                        <ul style="margin: 0 0 0 18px;">${historyHtml}</ul>
                    </div>
                    <button onclick="runIllegalBusiness('${b.id}')" class="btn btn-danger" ${b.cooldownRemainingMs > 0 ? 'disabled' : ''}>Run Operation</button>
                </div>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading illegal businesses:', error);
    }
}

function toggleIllegalRiskDetails(detailId) {
    const node = document.getElementById(detailId);
    if (!node) return;
    node.style.display = node.style.display === 'none' ? 'block' : 'none';
}

async function runIllegalBusiness(businessId) {
    try {
        const response = await fetch('/api/run_illegal_business', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId })
        });

        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
            updateStats();
            loadIllegalBusinesses();
            loadNotifications();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error running illegal operation');
    }
}

// ==================== STOCKS ====================

async function loadStocks() {
    try {
        const response = await fetch('/api/stocks');
        const data = await response.json();
        
        const container = document.getElementById('stocks-list');
        container.innerHTML = Object.entries(data.stocks).map(([symbol, stock]) => `
            <div class="card stock-item">
                <div>
                    <h4>${stock.name} (${symbol})</h4>
                    <p class="stock-price">$${stock.price.toLocaleString()}</p>
                </div>
                <div class="trade-controls">
                    <input type="number" id="buy-${symbol}-qty" placeholder="Quantity" min="1" value="1">
                    <button onclick="buyStock('${symbol}')" class="btn btn-success">Buy</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading stocks:', error);
    }
}

async function buyStock(symbol) {
    const quantity = parseInt(document.getElementById(`buy-${symbol}-qty`).value) || 1;
    
    try {
        const response = await fetch('/api/buy_stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Bought ${quantity} shares of ${symbol} for $${data.total_cost.toLocaleString()}`);
            updateStats();
            loadPortfolio();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error buying stock');
    }
}

async function sellStock(symbol, owned) {
    const quantity = parseInt(prompt(`How many shares of ${symbol} to sell? (You own ${owned})`, '1'));
    
    if (!quantity || quantity <= 0) return;
    
    try {
        const response = await fetch('/api/sell_stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Sold ${quantity} shares of ${symbol} for $${data.total_revenue.toLocaleString()}`);
            updateStats();
            loadPortfolio();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error selling stock');
    }
}

async function loadPortfolio() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        const container = document.getElementById('portfolio-list');
        
        if (data.portfolio.length === 0) {
            container.innerHTML = '<p class="text-muted">No stocks owned yet.</p>';
            return;
        }
        
        container.innerHTML = data.portfolio.map(p => `
            <div class="card">
                <div class="stock-item">
                    <div>
                        <h4>${p.name} (${p.symbol})</h4>
                        <p>Owned: ${p.quantity} shares @ $${p.currentPrice.toLocaleString()} each</p>
                        <p class="stock-price">Total Value: $${p.totalValue.toLocaleString()}</p>
                    </div>
                    <button onclick="sellStock('${p.symbol}', ${p.quantity})" class="btn btn-danger">Sell</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

// ==================== CRYPTO ====================

async function loadCrypto() {
    try {
        const response = await fetch('/api/crypto');
        const data = await response.json();
        
        const container = document.getElementById('crypto-list');
        container.innerHTML = Object.entries(data.crypto).map(([symbol, coin]) => `
            <div class="card crypto-item">
                <div>
                    <h4>${coin.name} (${symbol})</h4>
                    <p class="crypto-price">$${coin.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                </div>
                <div class="trade-controls">
                    <input type="number" id="buy-${symbol}-amt" placeholder="Amount" min="0.01" step="0.01" value="1">
                    <button onclick="buyCrypto('${symbol}')" class="btn btn-success">Buy</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading crypto:', error);
    }
}

async function buyCrypto(symbol) {
    const amount = parseFloat(document.getElementById(`buy-${symbol}-amt`).value) || 1;
    
    try {
        const response = await fetch('/api/buy_crypto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, amount })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Bought ${amount} ${symbol} for $${data.total_cost.toLocaleString()}`);
            updateStats();
            loadWallet();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error buying crypto');
    }
}

async function sellCrypto(symbol, owned) {
    const amount = parseFloat(prompt(`How much ${symbol} to sell? (You own ${owned.toFixed(4)})`, '1'));
    
    if (!amount || amount <= 0) return;
    
    try {
        const response = await fetch('/api/sell_crypto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, amount })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Sold ${amount} ${symbol} for $${data.total_revenue.toLocaleString()}`);
            updateStats();
            loadWallet();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error selling crypto');
    }
}

async function loadWallet() {
    try {
        const response = await fetch('/api/crypto_wallet');
        const data = await response.json();
        
        const container = document.getElementById('wallet-list');
        
        if (data.wallet.length === 0) {
            container.innerHTML = '<p class="text-muted">No crypto owned yet.</p>';
            return;
        }
        
        container.innerHTML = data.wallet.map(w => `
            <div class="card">
                <div class="crypto-item">
                    <div>
                        <h4>${w.name} (${w.symbol})</h4>
                        <p>Owned: ${w.amount.toFixed(4)} @ $${w.currentPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} each</p>
                        <p class="crypto-price">Total Value: $${w.totalValue.toLocaleString()}</p>
                    </div>
                    <button onclick="sellCrypto('${w.symbol}', ${w.amount})" class="btn btn-danger">Sell</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading wallet:', error);
    }
}

// ==================== LOANS ====================

async function takeLoan() {
    const amount = parseInt(document.getElementById('loan-amount').value);
    const type = document.getElementById('loan-type').value;
    
    if (!amount || amount <= 0 || amount > 100000) {
        showModal('❌ Loan amount must be between $1 and $100,000');
        return;
    }
    
    try {
        const response = await fetch('/api/take_loan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, type })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Loan approved! $${data.amount.toLocaleString()} added to your pockets.`);
            document.getElementById('loan-amount').value = '';
            updateStats();
            loadLoans();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error taking loan');
    }
}

async function payLoan(type) {
    const amount = parseInt(prompt('How much do you want to pay?', '1000'));
    
    if (!amount || amount <= 0) return;
    
    try {
        const response = await fetch('/api/pay_loan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, type })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Paid $${data.paid.toLocaleString()}. Remaining debt: $${data.remaining.toLocaleString()}`);
            updateStats();
            loadLoans();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error paying loan');
    }
}

async function loadLoans() {
    try {
        const response = await fetch('/api/loans');
        const data = await response.json();
        
        document.getElementById('interest-rate').textContent = data.interestRate;
        
        const container = document.getElementById('loans-list');
        let html = '';
        
        if (data.loans.regular.currentDebt > 0) {
            html += `
                <div class="card">
                    <h3>💳 Regular Loan</h3>
                    <p>Current Debt: <span class="text-danger">$${data.loans.regular.currentDebt.toLocaleString()}</span></p>
                    <p>Original: $${data.loans.regular.principal.toLocaleString()}</p>
                    ${data.loans.regular.inCollections ? '<p class="text-warning">⚠️ IN COLLECTIONS</p>' : ''}
                    <button onclick="payLoan('regular')" class="btn btn-success">Make Payment</button>
                </div>
            `;
        }
        
        if (data.loans.stock.currentDebt > 0) {
            html += `
                <div class="card">
                    <h3>📈 Stock Loan</h3>
                    <p>Current Debt: <span class="text-danger">$${data.loans.stock.currentDebt.toLocaleString()}</span></p>
                    <p>Original: $${data.loans.stock.principal.toLocaleString()}</p>
                    ${data.loans.stock.inCollections ? '<p class="text-warning">⚠️ IN COLLECTIONS</p>' : ''}
                    <button onclick="payLoan('stock')" class="btn btn-success">Make Payment</button>
                </div>
            `;
        }
        
        if (html === '') {
            html = '<p class="text-muted">No active loans.</p>';
        }
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading loans:', error);
    }
}

// ==================== SHOP ====================

async function loadShop() {
    try {
        const response = await fetch('/api/shop');
        const data = await response.json();
        
        const container = document.getElementById('shop-items');
        container.innerHTML = Object.entries(data.items).map(([id, item]) => `
            <div class="card shop-item">
                <div>
                    <h4>${item.name}</h4>
                    <p>Type: ${item.type} | Price: $${item.price.toLocaleString()}</p>
                    ${item.maxOwn !== Infinity ? `<p>Max Own: ${item.maxOwn}</p>` : ''}
                    ${item.rentHourly ? `<p>Rent: $${item.rentHourly}/hour</p>` : ''}
                    ${item.rentDaily ? `<p>Rent: $${item.rentDaily}/day</p>` : ''}
                </div>
                <button onclick="buyItem('${id}')" class="btn btn-success">Buy</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading shop:', error);
    }
}

async function buyItem(itemId) {
    const quantity = parseInt(prompt('How many?', '1'));
    
    if (!quantity || quantity <= 0) return;
    
    try {
        const response = await fetch('/api/buy_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, quantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ Purchased ${quantity} item(s) for $${data.total_cost.toLocaleString()}`);
            updateStats();
            loadInventory();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error buying item');
    }
}

async function loadInventory() {
    try {
        const response = await fetch('/api/inventory');
        const data = await response.json();
        
        const container = document.getElementById('inventory-list');
        
        if (data.inventory.length === 0) {
            container.innerHTML = '<p class="text-muted">No items in inventory.</p>';
            return;
        }
        
        container.innerHTML = data.inventory.map(item => `
            <div class="card">
                <h4>${item.name}</h4>
                <p>Quantity: ${item.quantity} | Type: ${item.type}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

// ==================== ROBBERY ====================

async function buyInsurance() {
    try {
        const response = await fetch('/api/buy_insurance', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error buying insurance');
    }
}

async function robPlayer() {
    const targetId = document.getElementById('rob-target-id').value.trim();
    
    if (!targetId) {
        showModal('❌ Please enter a target player ID');
        return;
    }
    
    if (!confirm(`Are you sure you want to rob player ${targetId}? You could get caught and jailed!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/rob/${targetId}`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            if (data.success) {
                showModal(`✅ ${data.message}`);
                updateStats();
            } else {
                showModal(`❌ ${data.message}`);
            }
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error robbing player');
    }
}

// ==================== LEADERBOARD ====================

async function loadLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard');
        const data = await response.json();
        
        const container = document.getElementById('leaderboard-list');
        
        if (data.leaderboard.length === 0) {
            container.innerHTML = '<p class="text-muted">No players yet.</p>';
            return;
        }
        
        container.innerHTML = data.leaderboard.map((player, index) => `
            <div class="leaderboard-item">
                <div>
                    <span class="leaderboard-rank">#${index + 1}</span>
                    <span>Player ${player.id}</span>
                </div>
                <span class="leaderboard-worth">$${player.total_worth.toLocaleString()}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// ==================== DASHBOARD ====================

async function loadAdvisors() {
    try {
        const response = await fetch('/api/advisors');
        const data = await response.json();

        const select = document.getElementById('advisor-select');
        if (!select) return;

        const options = Object.entries(data.advisors).map(([key, profile]) => {
            const selected = key === data.current ? 'selected' : '';
            return `<option value="${key}" ${selected}>${profile.name}</option>`;
        }).join('');

        select.innerHTML = options;
        const current = data.advisors[data.current];
        if (current) {
            document.getElementById('advisor-description').textContent = current.description;
        }
    } catch (error) {
        console.error('Error loading advisors:', error);
    }
}

async function setAdvisor() {
    const select = document.getElementById('advisor-select');
    if (!select) return;

    const advisor = select.value;
    try {
        const response = await fetch('/api/advisor/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ advisor })
        });

        const data = await response.json();
        if (response.ok) {
            showModal(`✅ Advisor set: ${data.profile.name}`);
            document.getElementById('advisor-description').textContent = data.profile.description;
            loadNotifications();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error setting advisor');
    }
}

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();

        const unreadNode = document.getElementById('notif-unread');
        const container = document.getElementById('notifications-list');
        if (!unreadNode || !container) return;

        unreadNode.textContent = data.unread > 0 ? `(${data.unread} unread)` : '';

        if (!data.notifications || data.notifications.length === 0) {
            container.innerHTML = '<p class="text-muted">No notifications yet.</p>';
            return;
        }

        container.innerHTML = data.notifications.slice(0, 12).map(n => {
            const level = (n.level || 'info').toLowerCase();
            const levelClass = ['success', 'warning', 'danger', 'info'].includes(level) ? level : 'info';
            const levelLabel = levelClass.toUpperCase();

            return `
            <div class="card notification-item ${n.read ? 'read' : 'unread'}">
                <div style="display: flex; justify-content: space-between; gap: 10px;">
                    <div>
                        <p style="margin: 0;">${n.message}</p>
                        <div class="notification-meta">
                            <span class="status-badge ${levelClass}">${levelLabel}</span>
                            <small class="text-muted">${new Date(n.createdAt).toLocaleString()}</small>
                        </div>
                    </div>
                    ${n.read ? '' : `<button class="btn btn-primary" onclick="markNotificationRead(${n.id})">Read</button>`}
                </div>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function markNotificationRead(id) {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking notification:', error);
    }
}

async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ all: true })
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking all notifications:', error);
    }
}

async function loadDashboard() {
    try {
        // Load config for economic status
        const configRes = await fetch('/api/config');
        const config = await configRes.json();
        
        // Load balance
        const balanceRes = await fetch('/api/balance');
        const balance = await balanceRes.json();
        
        // Load businesses
        const businessRes = await fetch('/api/businesses');
        const businesses = await businessRes.json();
        
        // Load portfolio
        const portfolioRes = await fetch('/api/portfolio');
        const portfolio = await portfolioRes.json();
        
        // Load crypto wallet
        const walletRes = await fetch('/api/crypto_wallet');
        const wallet = await walletRes.json();
        
        // Calculate totals
        const totalWorth = balance.checking + balance.savings + balance.pockets + balance.emergency;
        const portfolioValue = portfolio.portfolio.reduce((sum, p) => sum + p.totalValue, 0);
        const cryptoValue = wallet.wallet.reduce((sum, w) => sum + w.totalValue, 0);
        
        document.getElementById('total-worth').textContent = '$' + totalWorth.toLocaleString();
        document.getElementById('business-count').textContent = businesses.businesses.length;
        document.getElementById('portfolio-value').textContent = '$' + portfolioValue.toLocaleString();
        document.getElementById('crypto-value').textContent = '$' + cryptoValue.toLocaleString();
        
        // Economic status
        document.getElementById('gov-shutdown-status').innerHTML = config.govShutdown 
            ? '<span class="status-badge danger">⚠️ Government Shutdown Active</span>'
            : '<span class="status-badge success">✅ Government Operating Normally</span>';
        
        document.getElementById('recession-status').innerHTML = config.recession
            ? '<span class="status-badge warning">📉 Recession Active</span>'
            : '<span class="status-badge success">📈 Economy Healthy</span>';
        
        document.getElementById('interest-rate-status').innerHTML = 
            `Interest Rate: <strong>${config.interestRate}%</strong> daily`;

        loadAdvisors();
        loadNotifications();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// ==================== ADMIN ====================

async function toggleShutdown() {
    try {
        const response = await fetch('/api/toggle_shutdown', { method: 'POST' });
        const data = await response.json();
        
        showModal(`Government Shutdown: ${data.shutdown ? 'ON' : 'OFF'}`);
        loadDashboard();
    } catch (error) {
        showModal('❌ Error toggling shutdown');
    }
}

async function toggleRecession() {
    try {
        const response = await fetch('/api/toggle_recession', { method: 'POST' });
        const data = await response.json();
        
        showModal(`Recession: ${data.recession ? 'ON' : 'OFF'}`);
        loadDashboard();
    } catch (error) {
        showModal('❌ Error toggling recession');
    }
}

async function processHourly() {
    try {
        const response = await fetch('/api/process_hourly', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Hourly updates processed! Stock/crypto prices updated, interest applied, business revenue generated.');
            loadDashboard();
        } else {
            showModal('❌ Error processing hourly updates');
        }
    } catch (error) {
        showModal('❌ Error processing hourly updates');
    }
}

// Display player ID in admin
async function showPlayerId() {
    // Display a friendly note — player ID is managed server-side in session
    document.getElementById('player-id-display').textContent =
        'Your player ID is visible in the leaderboard. Others can use the first 8 characters to rob you!';
}

// ==================== INITIALIZATION ====================

// Update stats every 5 seconds
setInterval(updateStats, 5000);

// Initial load
updateStats();
loadDashboard();
showPlayerId();
loadNotifications();

// Close modal on background click
document.getElementById('message-modal').addEventListener('click', (e) => {
    if (e.target.id === 'message-modal') {
        closeModal();
    }
});
