// Tab Management
let stocksAutoRefreshTimer = null;
let businessIndustriesData = {}; // Store industries data globally
let illegalBusinessCategoriesData = {}; // Store illegal categories data globally
let allShopItems = {}; // Store all shop items for filtering
let currentShopFilter = 'all'; // Current category filter
let currentVehicleClassFilter = 'all'; // Current vehicle class filter
let currentBalance = { checking: 0, savings: 0, pockets: 0, emergency: 0 }; // Store current balance

// ==================== ERROR REPORTING ====================

async function reportError(message, stack = '', url = '', line = 0, column = 0) {
    try {
        if (shouldIgnoreErrorReport(message, stack, url)) {
            return;
        }

        // Get username if available
        const usernameElement = document.getElementById('username');
        const username = usernameElement ? usernameElement.textContent : 'anonymous';
        
        await fetch('/api/report_error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                stack: stack,
                url: url,
                line: line,
                column: column,
                userAgent: navigator.userAgent,
                username: username
            })
        });
        
        console.log('Error reported to owner');
    } catch (e) {
        // Don't let error reporting crash the app
        console.error('Failed to report error:', e);
    }
}

function shouldIgnoreErrorReport(message = '', stack = '', url = '') {
    const combined = `${message}\n${stack}\n${url}`.toLowerCase();
    return combined.includes('content.js')
        || combined.includes('chrome-extension://')
        || combined.includes('moz-extension://')
        || combined.includes('message channel closed before a response was received')
        || combined.includes("failed to execute 'removechild' on 'node'");
}

// Global error handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global error caught:', message, source, lineno, colno, error);
    const stack = error && error.stack ? error.stack : '';
    reportError(message, stack, source, lineno, colno);
    return false; // Let default error handling continue
};

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    const message = event.reason && event.reason.message ? event.reason.message : String(event.reason);
    const stack = event.reason && event.reason.stack ? event.reason.stack : '';
    reportError('Unhandled Promise Rejection: ' + message, stack, window.location.href, 0, 0);
});

// ==================== TAB MANAGEMENT ====================

function stopStocksAutoRefresh() {
    if (stocksAutoRefreshTimer) {
        clearInterval(stocksAutoRefreshTimer);
        stocksAutoRefreshTimer = null;
    }
}

function startStocksAutoRefresh() {
    stopStocksAutoRefresh();
    // Refresh occasionally while the Stocks tab is open.
    stocksAutoRefreshTimer = setInterval(() => {
        const active = document.querySelector('.tab-content.active');
        if (!active || active.id !== 'tab-stocks') {
            stopStocksAutoRefresh();
            return;
        }
        loadStocks();
        loadPortfolio();
    }, 30000);
}

function switchTab(tabName) {
    if (tabName !== 'stocks') stopStocksAutoRefresh();

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
    if (tabName === 'stocks') { loadStocks(); loadPortfolio(); loadSP12Index(); startStocksAutoRefresh(); }
    if (tabName === 'crypto') { loadCrypto(); loadWallet(); }
    if (tabName === 'loans') loadLoans();
    if (tabName === 'shop') { loadShop(); }
    if (tabName === 'inventory') { loadInventory(); }
    if (tabName === 'casino') loadCasinoStats();
    if (tabName === 'trading') { loadTrades(); setupTradingUI(); }
    if (tabName === 'leaderboard') loadLeaderboard();
    if (tabName === 'achievements') loadAchievements();
    if (tabName === 'economy') loadEconomy();
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'banking') loadTransactions();
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

// Input Modal Management
let inputModalResolve = null;

function showInputModal(title, defaultValue = '', placeholder = 'Enter amount...') {
    return new Promise((resolve) => {
        inputModalResolve = resolve;
        
        document.getElementById('input-modal-title').textContent = title;
        document.getElementById('input-modal-input').value = defaultValue;
        document.getElementById('input-modal-input').placeholder = placeholder;
        document.getElementById('input-modal').classList.add('active');
        
        // Focus on input
        setTimeout(() => {
            document.getElementById('input-modal-input').focus();
            document.getElementById('input-modal-input').select();
        }, 100);
        
        // Handle Enter key
        const input = document.getElementById('input-modal-input');
        const enterHandler = (e) => {
            if (e.key === 'Enter') {
                confirmInputModal();
                input.removeEventListener('keypress', enterHandler);
            }
        };
        input.addEventListener('keypress', enterHandler);
    });
}

function confirmInputModal() {
    const value = document.getElementById('input-modal-input').value;
    closeInputModal(value);
}

function closeInputModal(value = null) {
    document.getElementById('input-modal').classList.remove('active');
    if (inputModalResolve) {
        inputModalResolve(value);
        inputModalResolve = null;
    }
}

// Confirm Modal Management
let confirmModalResolve = null;

function showConfirmModal(message) {
    return new Promise((resolve) => {
        confirmModalResolve = resolve;
        
        document.getElementById('confirm-modal-message').textContent = message;
        document.getElementById('confirm-modal').classList.add('active');
    });
}

function closeConfirmModal(result) {
    document.getElementById('confirm-modal').classList.remove('active');
    if (confirmModalResolve) {
        confirmModalResolve(result);
        confirmModalResolve = null;
    }
}

// Update header stats
async function updateStats() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();

        // Store balance globally for quick transfer
        currentBalance = {
            checking: data.checking || 0,
            savings: data.savings || 0,
            pockets: data.pockets || 0,
            emergency: data.emergency || 0
        };

        // Animate header stats for a more lively UI
        animateCurrencyEl('stat-checking', data.checking);
        animateCurrencyEl('stat-savings', data.savings);
        animateCurrencyEl('stat-pockets', data.pockets);
        animateCurrencyEl('stat-emergency', data.emergency);

        // Show/hide banking controls and account creation buttons
        const hasAnyAccount = data.hasAccount || false;
        const hasChecking = data.hasCheckingAccount || false;
        const hasSavings = data.hasSavingsAccount || false;
        updateBankingAccountOptions(hasChecking, hasSavings);
        
        if (hasAnyAccount) {
            document.getElementById('banking-controls').style.display = 'block';
            
            // Show account creation section if user doesn't have both accounts
            if (!hasChecking || !hasSavings) {
                document.getElementById('create-account-section').style.display = 'block';
                
                // Update message and hide buttons for accounts they already have
                const checkingBtn = document.getElementById('btn-create-checking');
                const savingsBtn = document.getElementById('btn-create-savings');
                const message = document.getElementById('account-creation-message');
                
                if (hasChecking && !hasSavings) {
                    checkingBtn.style.display = 'none';
                    savingsBtn.style.display = 'inline-block';
                    message.textContent = 'You can also create a savings account:';
                } else if (hasSavings && !hasChecking) {
                    savingsBtn.style.display = 'none';
                    checkingBtn.style.display = 'inline-block';
                    message.textContent = 'You can also create a checking account:';
                } else {
                    // Both exist, hide the entire section
                    document.getElementById('create-account-section').style.display = 'none';
                }
            } else {
                document.getElementById('create-account-section').style.display = 'none';
            }
        } else {
            // No accounts yet - show creation options
            document.getElementById('create-account-section').style.display = 'block';
            document.getElementById('banking-controls').style.display = 'none';
            document.getElementById('btn-create-checking').style.display = 'inline-block';
            document.getElementById('btn-create-savings').style.display = 'inline-block';
            document.getElementById('account-creation-message').textContent = 'Choose your account type to get started:';
        }
        
        // Update quick transfer button labels with actual amounts
        updateQuickTransferButtons();
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

function updateQuickTransferButtons() {
    const checkingBtn = document.getElementById('quick-all-checking');
    const savingsBtn = document.getElementById('quick-all-savings');
    
    if (checkingBtn) {
        checkingBtn.textContent = `All Checking ($${currentBalance.checking.toLocaleString()})`;
    }
    if (savingsBtn) {
        savingsBtn.textContent = `All Savings ($${currentBalance.savings.toLocaleString()})`;
    }
}

function updateBankingAccountOptions(hasChecking, hasSavings) {
    const depositTarget = document.getElementById('deposit-target');
    const withdrawSource = document.getElementById('withdraw-source');
    const quickCheckingBtn = document.getElementById('quick-all-checking');
    const quickSavingsBtn = document.getElementById('quick-all-savings');

    if (depositTarget) {
        Array.from(depositTarget.options).forEach((option) => {
            if (option.value === 'checking') option.disabled = !hasChecking;
            if (option.value === 'savings') option.disabled = !hasSavings;
        });
        if (depositTarget.selectedOptions[0] && depositTarget.selectedOptions[0].disabled) {
            depositTarget.value = hasChecking ? 'checking' : hasSavings ? 'savings' : 'emergency';
        }
    }

    if (withdrawSource) {
        Array.from(withdrawSource.options).forEach((option) => {
            if (option.value === 'checking') option.disabled = !hasChecking;
            if (option.value === 'savings') option.disabled = !hasSavings;
        });
        if (withdrawSource.selectedOptions[0] && withdrawSource.selectedOptions[0].disabled) {
            withdrawSource.value = hasChecking ? 'checking' : hasSavings ? 'savings' : 'emergency';
        }
    }

    if (quickCheckingBtn) quickCheckingBtn.disabled = !hasChecking;
    if (quickSavingsBtn) quickSavingsBtn.disabled = !hasSavings;
}

// ==================== UI ANIMATION HELPERS ====================
function animateNumber(el, start, end, duration = 900, formatFn) {
    const range = end - start;
    const startTime = performance.now();
    function step(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const value = Math.round(start + range * progress);
        el.textContent = formatFn ? formatFn(value) : value;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function animateCurrencyEl(id, endValue, suffix = '') {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
    animateNumber(el, current, endValue, 900, (v) => '$' + v.toLocaleString() + suffix);
}

// Trading help modal
function showTradingGuide() {
    const guideHtml = `
        <h3>💱 Trading Guide</h3>
        <p>Trading allows direct player-to-player exchanges. Use precise terms and prefer smaller test trades for unfamiliar partners.</p>
        <ul style="text-align:left; margin-top:8px;">
            <li><strong>Assets:</strong> Money, shop items (use exact ID), stocks, crypto.</li>
            <li><strong>No escrow:</strong> Trades are direct — moderators can assist but there's no automatic escrow.</li>
            <li><strong>Best Practice:</strong> Verify the counterparty username and ask for screenshots or small test trades if you're unsure.</li>
            <li><strong>Advanced:</strong> For high-value exchanges, consider splitting payments or using moderator keys.</li>
        </ul>
        <p style="margin-top:10px; font-size:0.9em; color:#ccc;">Tip: Use the 'Trade History' and 'Received' lists to audit offers and avoid scams.</p>
    `;
    showModal(guideHtml);
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

async function setDepositAmount(amount) {
    const input = document.getElementById('deposit-amount');
    if (amount === 'all') {
        // Fetch fresh balance data for "All" button to prevent stale data issues
        try {
            const response = await fetch('/api/balance');
            const data = await response.json();
            const pockets = data.pockets || 0;
            input.value = pockets;
            if (pockets <= 0) {
                showModal('❌ No cash in pockets to deposit');
            }
        } catch (error) {
            // Fallback to cached balance if fetch fails
            const pockets = currentBalance?.pockets || 0;
            input.value = pockets;
            if (pockets <= 0) {
                showModal('❌ No cash in pockets to deposit');
            }
        }
    } else {
        input.value = amount;
    }
}

async function deposit() {
    const amountStr = document.getElementById('deposit-amount').value;
    const amount = parseInt(amountStr);
    const target = document.getElementById('deposit-target').value;
    
    if (!amount || isNaN(amount) || amount <= 0) {
        showModal('❌ Please enter a valid amount');
        return;
    }

    const pockets = currentBalance?.pockets || 0;
    if (pockets < amount) {
        showModal(`❌ You only have $${pockets.toLocaleString()} in pockets`);
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

async function setWithdrawAmount(amount) {
    const input = document.getElementById('withdraw-amount');
    const source = document.getElementById('withdraw-source').value;
    
    if (amount === 'all') {
        // Fetch fresh balance data for "All" button to prevent stale data issues
        try {
            const response = await fetch('/api/balance');  
            const data = await response.json();
            const maxAmount = data[source] || 0;
            input.value = maxAmount;
            if (maxAmount <= 0) {
                showModal(`❌ No funds available in ${source}`);
            }
        } catch (error) {
            // Fallback to cached balance if fetch fails
            const maxAmount = currentBalance?.[source] || 0;
            input.value = maxAmount;
            if (maxAmount <= 0) {
                showModal(`❌ No funds available in ${source}`);
            }
        }
    } else {
        input.value = amount;
    }
}

async function withdraw() {
    const amount = parseInt(document.getElementById('withdraw-amount').value);
    const source = document.getElementById('withdraw-source').value;
    
    if (!amount || isNaN(amount) || amount <= 0) {
        showModal('❌ Please enter a valid amount');
        return;
    }

    const sourceBalance = currentBalance?.[source] || 0;
    if (sourceBalance < amount) {
        showModal(`❌ You only have $${sourceBalance.toLocaleString()} in ${source}`);
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

function setQuickTransferAmount(amount) {
    const input = document.getElementById('quick-transfer-amount');
    if (amount === 'max-checking') {
        input.value = currentBalance.checking;
        input.setAttribute('data-source', 'checking');
    } else if (amount === 'max-savings') {
        input.value = currentBalance.savings;
        input.setAttribute('data-source', 'savings');
    } else {
        input.value = amount;
        input.removeAttribute('data-source');
    }
}

async function quickTransfer(direction) {
    const input = document.getElementById('quick-transfer-amount');
    let amount = parseInt(input.value);
    
    if (!amount || amount <= 0) {
        showModal('❌ Please enter a valid amount');
        return;
    }
    
    // Validate the source matches the direction (if set via All button)
    const dataSource = input.getAttribute('data-source');
    if (dataSource) {
        const expectedSource = direction === 'checking_to_savings' ? 'checking' : 'savings';
        if (dataSource !== expectedSource) {
            showModal(`❌ You selected "All ${dataSource}" but are trying to transfer from ${expectedSource}`);
            return;
        }
    }
    
    try {
        const response = await fetch('/api/quick_transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction, amount })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const from = direction === 'checking_to_savings' ? 'checking' : 'savings';
            const to = direction === 'checking_to_savings' ? 'savings' : 'checking';
            showModal(`✅ Transferred $${data.amount.toLocaleString()} from ${from} to ${to}`);
            input.value = '';
            input.removeAttribute('data-source');
            updateStats();
            loadTransactions(); // Refresh transaction list
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error transferring');
    }
}

async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        const data = await response.json();
        
        const container = document.getElementById('transaction-list');
        
        if (response.ok && data.transactions && data.transactions.length > 0) {
            const transactionsHtml = data.transactions.map(trans => {
                const isIncome = trans.type === 'earn';
                const icon = isIncome ? '💰' : trans.type === 'transfer' ? '🔄' : '📤';
                const color = isIncome ? '#4CAF50' : trans.type === 'transfer' ? '#2196f3' : '#f44336';
                const sign = isIncome ? '+' : '-';
                
                const date = new Date(trans.timestamp);
                const timeStr = date.toLocaleString();
                
                return `
                    <div style="padding: 10px; margin: 5px 0; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid ${color}; display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 1.3em;">${icon}</span>
                                <div>
                                    <div style="font-weight: bold;">${trans.description}</div>
                                    <div style="font-size: 0.85em; color: #888;">${timeStr}</div>
                                </div>
                            </div>
                        </div>
                        <div style="font-size: 1.2em; font-weight: bold; color: ${color};">
                            ${isIncome || trans.type === 'transfer' ? sign : ''}$${Math.abs(trans.amount).toLocaleString()}
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = transactionsHtml;
        } else {
            container.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No transactions yet</p>';
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
        document.getElementById('transaction-list').innerHTML = '<p style="color: #f44336;">Failed to load transactions</p>';
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

// Load business industries data on page load
async function loadBusinessIndustries() {
    try {
        const response = await fetch('/api/business/industries');
        if (response.ok) {
            const data = await response.json();
            businessIndustriesData = data.industries;
            updateBusinessTypes(); // Initialize with default selection
        }
    } catch (error) {
        console.error('Error loading business industries:', error);
    }
}

// Filter industry options based on business model
function filterBusinessIndustries() {
    const modelFilter = document.getElementById('business-model-filter').value;
    const industrySelect = document.getElementById('business-industry');
    
    // Get all optgroups
    const productOptgroup = industrySelect.querySelector('optgroup[label*="Product"]');
    const serviceOptgroup = industrySelect.querySelector('optgroup[label*="Service"]');
    const mixedOptgroup = industrySelect.querySelector('optgroup[label*="Mixed"]');
    
    // Show/hide based on filter
    if (modelFilter === 'all') {
        productOptgroup.style.display = '';
        serviceOptgroup.style.display = '';
        mixedOptgroup.style.display = '';
    } else if (modelFilter === 'Product') {
        productOptgroup.style.display = '';
        serviceOptgroup.style.display = 'none';
        mixedOptgroup.style.display = 'none';
        // Select first visible option
        industrySelect.value = productOptgroup.querySelector('option').value;
    } else if (modelFilter === 'Service') {
        productOptgroup.style.display = 'none';
        serviceOptgroup.style.display = '';
        mixedOptgroup.style.display = 'none';
        industrySelect.value = serviceOptgroup.querySelector('option').value;
    } else if (modelFilter === 'Mixed') {
        productOptgroup.style.display = 'none';
        serviceOptgroup.style.display = 'none';
        mixedOptgroup.style.display = '';
        industrySelect.value = mixedOptgroup.querySelector('option').value;
    }
    
    updateBusinessTypes();
}

// Update specific business types based on selected industry
function updateBusinessTypes() {
    const industry = document.getElementById('business-industry').value;
    const typeSelect = document.getElementById('business-type');
    
    // Clear current options
    typeSelect.innerHTML = '';
    
    // Get types for selected industry
    if (businessIndustriesData[industry] && businessIndustriesData[industry].types) {
        const types = businessIndustriesData[industry].types;
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeSelect.appendChild(option);
        });
    } else {
        // Fallback
        const option = document.createElement('option');
        option.value = 'General Business';
        option.textContent = 'General Business';
        typeSelect.appendChild(option);
    }
}

async function createBusiness() {
    const name = document.getElementById('business-name').value.trim();
    const type = document.getElementById('business-type').value;
    const industry = document.getElementById('business-industry') ? document.getElementById('business-industry').value : 'general';
    
    if (!name || name.length < 3) {
        showModal('❌ Business name must be at least 3 characters');
        return;
    }
    
    try {
        const response = await fetch('/api/create_business', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, industry })
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
        // Fetch businesses and aggregated management summary
        const [respBiz, respSummary] = await Promise.all([
            fetch('/api/businesses'),
            fetch('/api/businesses/management_summary')
        ]);

        const data = await respBiz.json();
        const summary = await respSummary.json();

        const container = document.getElementById('businesses-list');
        const summaryNode = document.getElementById('business-management-summary');

        // Render aggregated summary (show even if no businesses)
        if (summaryNode) {
            summaryNode.style.display = 'block';
            summaryNode.innerHTML = `
                <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                    <div><strong>Total Businesses Managed:</strong> ${summary.per_business.length}</div>
                    <div><strong>Total Employees:</strong> ${summary.total_employees}</div>
                    <div><strong>Active Upgrades:</strong> ${summary.total_upgrades}</div>
                    <div><strong>Total Revenue (lifetime):</strong> $${summary.total_revenue_sum.toLocaleString()}</div>
                    <div><strong>Available to Collect:</strong> $${summary.total_accumulated_revenue.toLocaleString()}</div>
                    <div><strong>Revenue Rate:</strong> $${summary.total_revenue_rate.toLocaleString()}/hour</div>
                </div>
            `;
        }

        // Render business cards
        if (!data.businesses || data.businesses.length === 0) {
            container.innerHTML = '<p class="text-muted">No businesses yet. Create one to start earning passive income!</p>';
        } else {
            // Build lookup from management summary
            const perMap = {};
            if (summary && Array.isArray(summary.per_business)) {
                summary.per_business.forEach(p => { perMap[p.id] = p; });
            }

            container.innerHTML = data.businesses.map(b => {
                const pb = perMap[b.id] || {};
                const empCount = pb.employees || 0;
                const upCount = pb.upgrades || 0;
                const acc = pb.accumulated_revenue || 0;
                const accHtml = acc > 0 ? `<span class="badge badge-accumulated">💰 ${acc.toLocaleString()}</span>` : '';
                const collectBtn = acc > 0 ? `<button onclick="collectBusinessRevenueFor('${b.id}')" class="btn btn-collect">Collect</button>` : '';

                // NEW: Show regular workers info
                const regularWorkers = b.regular_workers || 0;
                const workerWage = b.worker_wage || 100;
                const businessSize = b.size || 'solo';
                const industry = b.industry || 'general';
                
                // Get business type (Product/Service) from industry data
                const industryData = businessIndustriesData[industry] || {};
                const businessModel = industryData.business_type || 'Mixed';
                const industryName = industryData.name || industry;
                
                const sizeLabels = {
                    'solo': 'Solo',
                    'partnership': 'Partnership',
                    'major_service': 'Major Service',
                    'corporation': 'Corporation'
                };
                const sizeLabel = sizeLabels[businessSize] || 'Solo';
                
                const staffLabel = `${empCount} AI + ${regularWorkers.toLocaleString()} workers`;
                const workforceSection = `
                    <div style="margin-top:8px; padding:8px; background:rgba(50,150,200,0.1); border-radius:5px;">
                        <strong>Workforce:</strong> ${regularWorkers.toLocaleString()} Regular Workers @ $${workerWage}/day
                        <div style="margin-top:5px;">
                            <button onclick="hireRegularWorkers('${b.id}')" class="btn btn-sm">Hire Workers</button>
                            <button onclick="fireRegularWorkers('${b.id}')" class="btn btn-sm">Fire Workers</button>
                            <button onclick="setWorkerWage('${b.id}')" class="btn btn-sm">Set Wage</button>
                        </div>
                    </div>
                `;

                return `
                <div class="card business-item">
                    <div class="business-item-main">
                        <h4>${b.name} <span style="font-size:0.75em; color:#888;">[${sizeLabel}]</span></h4>
                        <p>Type: ${b.type} | Model: <strong>${businessModel}</strong> | Industry: ${industryName}</p>
                        <p>Staff: ${staffLabel}</p>
                        <p>Hourly Profit Rate: $${(b.revenue || 0).toLocaleString()} | Total Earnings: $${(b.totalEarnings || 0).toLocaleString()}</p>
                        <div class="business-meta">
                            <span class="badge badge-employees">👥 ${empCount} AI</span>
                            <span class="badge badge-employees">👷 ${regularWorkers.toLocaleString()} Workers</span>
                            <span class="badge badge-upgrades">⚙️ ${upCount}</span>
                            ${accHtml}
                        </div>
                        ${workforceSection}
                    </div>
                    <div class="business-item-actions">
                        <button onclick="hireWorker('${b.id}')" class="btn btn-primary">Hire Cashier</button>
                        <button onclick="upgradeBusinessSize('${b.id}', '${businessSize}')" class="btn btn-secondary">Upgrade Size</button>
                        <button onclick="sendPartnershipRequest('${b.id}')" class="btn btn-secondary">Add Partner</button>
                        <button onclick="toggleBusinessPanel('${b.id}')" class="btn btn-secondary">Details</button>
                        ${collectBtn}
                    </div>
                    <div id="bm-inline-${b.id}" class="business-inline-panel" style="display:none; margin-top:12px;"></div>
                </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Error loading businesses:', error);
    }
}

function openBusinessModeFor(businessId, businessName) {
    try {
        // Open the Businesses tab and show the inline panel for the selected business
        window.focusBusiness = { id: businessId, name: businessName };
        switchTab('businesses');
        // ensure panel is open
        setTimeout(() => toggleBusinessPanel(businessId), 150);
    } catch (e) {
        console.error('Error opening Business Management for business:', e);
    }
}

// Toggle inline per-business panel (loads on first open)
function toggleBusinessPanel(businessId) {
    const panelId = `bm-inline-${businessId}`;
    const node = document.getElementById(panelId);
    if (!node) return;
    if (node.style.display === 'block') {
        node.style.display = 'none';
        return;
    }
    // Load inline panel content
    node.style.display = 'block';
    node.innerHTML = '<div class="loading">Loading business details...</div>';
    loadBusinessInline(businessId, node);
}

async function loadBusinessInline(businessId, containerNode) {
    try {
        const url = `/api/business_mode/status?business_id=${encodeURIComponent(businessId)}`;
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) {
            containerNode.innerHTML = `<div class="text-muted">Failed to load: ${data.error || 'unknown'}</div>`;
            return;
        }

        // Build inline UI
        const employeesHtml = (data.employees || []).map(emp => {
            const typeLabel = (emp.type || '').toString().replace(/_/g, ' ');
            const hired = emp.hired_at ? new Date(emp.hired_at).toLocaleDateString() : '';
            const salary = (emp.salary_per_day || 0);
            const rev = (emp.revenue_per_day || 0);
            return `
                <div class="employee-mini">
                    <strong>${typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)}</strong>
                    <small style="margin-left:6px; opacity:0.9;">${hired ? `Hired ${hired}` : ''}</small>
                    <div style="margin-top:4px; font-size:0.9em; opacity:0.9;">
                        Revenue/day: $${rev.toLocaleString()} · Salary/day: $${salary.toLocaleString()}
                    </div>
                </div>
            `;
        }).join('') || '<div class="text-muted">No staff hired yet</div>';

        const hiresHtml = (data.available_hires || []).slice(0, 6).map(h => `
            <div class="hire-mini">
                <div class="hire-skill-mini">${(h.name || h.type || 'Employee')}</div>
                <div class="hire-cost-mini">$${(h.cost || 0).toLocaleString()}</div>
                <button class="btn btn-sm" onclick="hireEmployeeFor('${businessId}', '${h.type}', ${h.cost || 0})">Hire</button>
            </div>
        `).join('') || '<div class="text-muted">No hires available</div>';

        const upgradesHtml = (data.available_upgrades || []).map(u => `
            <div class="upgrade-mini">
                <div><strong>${u.name}</strong> — ${u.tier_name}</div>
                <div class="upgrade-cost-mini">$${u.cost.toLocaleString()}</div>
                <button class="btn btn-sm btn-success" onclick="purchaseUpgradeFor('${businessId}', '${u.category}', ${u.tier}, ${u.cost})">Buy</button>
            </div>
        `).join('') || '<div class="text-muted">No upgrades</div>';

        containerNode.innerHTML = `
            <div class="bm-inline-header">
                <div class="bm-inline-stats">
                    <div>Total Earnings: <strong>$${(data.total_revenue || 0).toLocaleString()}</strong></div>
                    <div>Profit Rate: <strong>$${(data.revenue_rate || 0).toLocaleString()}/hour</strong></div>
                    <div>Available to Collect: <strong>$${(data.accumulated_revenue || 0).toLocaleString()}</strong></div>
                    <div>Gross/day: <strong>$${(data.gross_per_day || 0).toLocaleString()}</strong></div>
                    <div>Salaries/day: <strong>$${(data.salary_per_day || 0).toLocaleString()}</strong></div>
                    <div>Tax Rate: <strong>${(data.tax_rate_percent ?? 0).toLocaleString()}%</strong></div>
                    ${data.max_employees ? `<div>Staff Capacity: <strong>${(data.employees || []).length}/${data.max_employees}</strong></div>` : ''}
                </div>
                <div class="bm-inline-actions">
                    <button class="btn btn-success" onclick="collectBusinessRevenueFor('${businessId}')" ${data.accumulated_revenue > 0 ? '' : 'disabled'}>Collect</button>
                    <button class="btn btn-outline" onclick="toggleBusinessPanel('${businessId}')">Close</button>
                </div>
            </div>
            <div class="bm-inline-section">
                <h4>Employees</h4>
                <div class="bm-inline-employees">${employeesHtml}</div>
            </div>
            <div class="bm-inline-section">
                <h4>Available Hires</h4>
                <div class="bm-inline-hires">${hiresHtml}</div>
            </div>
            <div class="bm-inline-section">
                <h4>Upgrades</h4>
                <div class="bm-inline-upgrades">${upgradesHtml}</div>
            </div>
        `;

    } catch (err) {
        console.error('Error loading inline business:', err);
        containerNode.innerHTML = '<div class="text-muted">Error loading business details.</div>';
    }
}

async function hireEmployeeFor(businessId, employeeType, cost) {
    const label = (employeeType || '').toString().replace(/_/g, ' ');
    if (!confirm(`Hire ${label} for $${(cost || 0).toLocaleString()}?`)) return;
    try {
        const response = await fetch('/api/business_mode/hire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ employee_type: employeeType, business_id: businessId })
        });
        const data = await response.json();
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
            // refresh inline panel
            const node = document.getElementById(`bm-inline-${businessId}`);
            if (node) loadBusinessInline(businessId, node);
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (err) {
        showModal('❌ Error hiring employee');
    }
}

async function purchaseUpgradeFor(businessId, category, tier, cost) {
    if (!confirm(`Purchase this upgrade for $${cost.toLocaleString()}?`)) return;
    try {
        const response = await fetch('/api/business_mode/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, tier, business_id: businessId })
        });
        const data = await response.json();
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
            const node = document.getElementById(`bm-inline-${businessId}`);
            if (node) loadBusinessInline(businessId, node);
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (err) {
        showModal('❌ Error purchasing upgrade');
    }
}

async function collectBusinessRevenueFor(businessId) {
    try {
        const response = await fetch('/api/business_mode/collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId })
        });
        const data = await response.json();
        if (response.ok) {
            showModal(`${data.message}`);
            updateStats();
            const node = document.getElementById(`bm-inline-${businessId}`);
            if (node) loadBusinessInline(businessId, node);
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (err) {
        showModal('❌ Error collecting revenue');
    }
}

async function hireWorker(businessId) {
    // Quick-hire a cashier into the business staff system
    try {
        const response = await fetch('/api/business_mode/hire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ employee_type: 'cashier', business_id: businessId })
        });

        const data = await response.json();
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error hiring cashier');
    }
}

// ==================== NEW BUSINESS FEATURES ====================

async function hireRegularWorkers(businessId) {
    const count = prompt('How many regular workers to hire? (e.g., 100, 1000, 55000)');
    const numWorkers = parseInt(count);
    
    if (!numWorkers || numWorkers <= 0) {
        showModal('❌ Invalid number');
        return;
    }
    
    try {
        const response = await fetch('/api/business/hire_regular_workers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId, count: numWorkers })
        });
        
        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error hiring workers');
    }
}

async function fireRegularWorkers(businessId) {
    const count = prompt('How many regular workers to fire?');
    const numWorkers = parseInt(count);
    
    if (!numWorkers || numWorkers <= 0) {
        showModal('❌ Invalid number');
        return;
    }
    
    try {
        const response = await fetch('/api/business/fire_regular_workers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId, count: numWorkers })
        });
        
        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error firing workers');
    }
}

async function setWorkerWage(businessId) {
    const wage = prompt('Set daily wage per regular worker ($50-$1,000):');
    const dailyWage = parseInt(wage);
    
    if (!dailyWage || dailyWage < 50 || dailyWage > 1000) {
        showModal('❌ Wage must be between $50-$1,000');
        return;
    }
    
    try {
        const response = await fetch('/api/business/set_worker_wage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId, wage: dailyWage })
        });
        
        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error setting wage');
    }
}

async function upgradeBusinessSize(businessId, currentSize) {
    const sizes = ['solo', 'partnership', 'major_service', 'corporation'];
    const currentIdx = sizes.indexOf(currentSize);
    
    if (currentIdx >= sizes.length - 1) {
        showModal('❌ Already at maximum size');
        return;
    }
    
    const nextSize = sizes[currentIdx + 1];
    const sizeNames = {
        'partnership': 'Partnership ($100K)',
        'major_service': 'Major Service ($500K)',
        'corporation': 'Corporation ($5M)'
    };
    
    if (!confirm(`Upgrade business to ${sizeNames[nextSize]}?`)) return;
    
    try {
        const response = await fetch('/api/business/upgrade_size', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId, size: nextSize })
        });
        
        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
            updateStats();
            loadBusinesses();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error upgrading business');
    }
}

async function sendPartnershipRequest(businessId) {
    const targetUsername = prompt('Enter username of player to invite as partner:');
    if (!targetUsername || !targetUsername.trim()) return;
    
    const ownershipPct = prompt('What percentage ownership to offer? (e.g., 30 for 30%)');
    const pct = parseFloat(ownershipPct);
    
    if (!pct || pct <= 0 || pct >= 100) {
        showModal('❌ Ownership must be between 0-100%');
        return;
    }
    
    try {
        const response = await fetch('/api/business/send_partnership_request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                business_id: businessId, 
                target_username: targetUsername.trim(), 
                ownership_pct: pct 
            })
        });
        
        const data = await response.json();
        if (response.ok) {
            showModal(data.message);
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error sending partnership request');
    }
}

async function createIllegalBusiness() {
    const name = document.getElementById('illegal-business-name').value.trim();
    const  type = document.getElementById('illegal-business-type').value;
    const category = document.getElementById('illegal-business-category').value;

    if (!name || name.length < 3) {
        showModal('❌ Operation name must be at least 3 characters');
        return;
    }

    try {
        const response = await fetch('/api/create_illegal_business', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, category })
        });

        const data = await response.json();
        if (response.ok) {
            showModal(`✅ Illegal operation created: ${data.business.name} (Cost: $${data.startup_cost.toLocaleString()})\n🔥 Heat Level: ${Math.round(data.business.heat_level * 100)}%`);
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

// Load illegal business categories on page load
async function loadIllegalBusinessCategories() {
    try {
        const response = await fetch('/api/illegal_business/categories');
        if (response.ok) {
            const data = await response.json();
            illegalBusinessCategoriesData = data.categories;
            updateIllegalBusinessTypes(); // Initialize with default selection
        }
    } catch (error) {
        console.error('Error loading illegal business categories:', error);
    }
}

// Update specific illegal business types based on selected category
function updateIllegalBusinessTypes() {
    const category = document.getElementById('illegal-business-category').value;
    const typeSelect = document.getElementById('illegal-business-type');
    
    // Clear current options
    typeSelect.innerHTML = '';
    
    // Get types for selected category
    if (illegalBusinessCategoriesData[category] && illegalBusinessCategoriesData[category].types) {
        const types = illegalBusinessCategoriesData[category].types;
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeSelect.appendChild(option);
        });
    } else {
        // Fallback
        const option = document.createElement('option');
        option.value = 'Black Market Stall';
        option.textContent = 'Black Market Stall';
        typeSelect.appendChild(option);
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
        container.innerHTML = Object.entries(data.stocks).map(([symbol, stock]) => {
            const changePoints = stock.change_points || 0;
            const changePercent = stock.price > 0 ? ((changePoints / stock.price) * 100) : 0;
            const changeColor = changePoints >= 0 ? '#4CAF50' : '#f44336';
            const changeSymbol = changePoints >= 0 ? '▲' : '▼';
            const changeDisplay = changePoints !== 0 
                ? `<span style="color: ${changeColor}; font-size: 0.9em;">${changeSymbol} $${Math.abs(changePoints).toFixed(2)} (${Math.abs(changePercent).toFixed(2)}%)</span>`
                : '<span style="color: #888; font-size: 0.9em;">No change</span>';
            
            return `
                <div class="card stock-item" style="position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <div>
                            <h4>${stock.name} (${symbol})</h4>
                            <p class="stock-price">$${stock.price.toLocaleString()}</p>
                            ${changeDisplay}
                        </div>
                        <button onclick="showStockOwnership('${symbol}')" class="btn btn-secondary btn-sm" style="font-size: 0.8em; padding: 5px 10px;">
                            👥 Owners
                        </button>
                    </div>
                    <div class="trade-controls">
                        <input type="number" id="buy-${symbol}-qty" placeholder="Quantity" min="1" value="1" 
                               oninput="updateStockCostPreview('${symbol}', ${stock.price})">
                        <button onclick="buyStock('${symbol}')" class="btn btn-success">Buy</button>
                        <div id="cost-preview-${symbol}" class="cost-preview">Total: $${stock.price.toLocaleString()}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading stocks:', error);
    }
}

function updateStockCostPreview(symbol, price) {
    const quantity = parseInt(document.getElementById(`buy-${symbol}-qty`).value) || 0;
    const totalCost = price * quantity;
    const previewElement = document.getElementById(`cost-preview-${symbol}`);
    if (previewElement && quantity > 0) {
        previewElement.textContent = `Total: $${totalCost.toLocaleString()}`;
        previewElement.style.display = 'block';
    } else if (previewElement) {
        previewElement.style.display = 'none';
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
    const quantity = await showInputModal(`💰 Sell ${symbol}`, '1', `How many shares? (You own ${owned})`);
    
    if (!quantity || parseInt(quantity) <= 0) return;
    
    try {
        const response = await fetch('/api/sell_stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity: parseInt(quantity) })
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

async function loadSP12Index() {
    try {
        const response = await fetch('/api/sp12_index');
        const data = await response.json();
        
        if (response.ok) {
            const indexValue = data.index_value || 0;
            const changePercent = data.change_percent || 0;
            const totalMarketCap = data.total_market_cap || 0;
            const components = data.components || [];
            
            // Update index display
            document.getElementById('sp12-value').textContent = indexValue.toFixed(2);
            
            const changeColor = changePercent >= 0 ? '#4CAF50' : '#f44336';
            const changeSymbol = changePercent >= 0 ? '▲' : '▼';
            document.getElementById('sp12-change').innerHTML = `
                <span style="color: ${changeColor};">${changeSymbol} ${Math.abs(changePercent).toFixed(2)}%</span>
            `;
            document.getElementById('sp12-change').style.color = changeColor;
            
            document.getElementById('sp12-marketcap').textContent = `$${(totalMarketCap / 1000000).toFixed(1)}M`;
            
            // Render components
            const componentsHtml = components.map(comp => {
                const priceChange = comp.change_points || 0;
                const changeColor = priceChange >= 0 ? '#4CAF50' : '#f44336';
                const changeSymbol = priceChange >= 0 ? '▲' : '▼';
                const marketCapM = (comp.market_cap / 1000000).toFixed(1);
                
                return `
                    <div style="padding: 10px; margin: 5px 0; background: rgba(0,0,0,0.2); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: bold; color: #fff;">${comp.name} (${comp.symbol})</div>
                            <div style="font-size: 0.9em; color: rgba(255,255,255,0.7);">Cap: $${marketCapM}M</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #fff;">$${comp.price.toFixed(2)}</div>
                            <div style="font-size: 0.9em; color: ${changeColor};">${changeSymbol} $${Math.abs(priceChange).toFixed(2)}</div>
                        </div>
                    </div>
                `;
            }).join('');
            
            document.getElementById('sp12-components').innerHTML = componentsHtml;
        }
    } catch (error) {
        console.error('Error loading S&P12 index:', error);
    }
}

function toggleSP12Components() {
    const componentsDiv = document.getElementById('sp12-components');
    const toggleBtn = document.getElementById('sp12-toggle-btn');
    
    if (componentsDiv.style.display === 'none') {
        componentsDiv.style.display = 'block';
        toggleBtn.innerHTML = 'Hide Components ▲';
    } else {
        componentsDiv.style.display = 'none';
        toggleBtn.innerHTML = 'Show Components ▼';
    }
}

async function showStockOwnership(symbol) {
    try {
        document.getElementById('ownership-modal').style.display = 'flex';
        document.getElementById('ownership-content').innerHTML = 'Loading...';
        
        const response = await fetch(`/api/stock/${symbol}/ownership`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('ownership-title').textContent = `👥 ${data.stock_name} (${symbol}) Ownership`;
            
            const totalShares = data.total_shares || 0;
            const ownersCount = data.owners ? data.owners.length : 0;
            const publicFloat = data.public_float_percent || 0;
            
            let ownersHtml = '';
            
            if (ownersCount > 0) {
                ownersHtml = data.owners.map((owner, index) => {
                    const bgColor = index === 0 ? 'rgba(255, 215, 0, 0.2)' : 
                                  index === 1 ? 'rgba(192, 192, 192, 0.2)' : 
                                  index === 2 ? 'rgba(205, 127, 50, 0.2)' : 
                                  'rgba(255,255,255,0.05)';
                    const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
                    
                    return `
                        <div style="padding: 12px; margin: 8px 0; background: ${bgColor}; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.2em; min-width: 30px;">${medal}</span>
                                <div>
                                    <div style="font-weight: bold;">${owner.username}</div>
                                    <div style="font-size: 0.85em; color: #888;">${owner.shares.toLocaleString()} shares</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.2em; font-weight: bold; color: #4CAF50;">${owner.percentage.toFixed(2)}%</div>
                                <div style="font-size: 0.85em; color: #888;">$${owner.value.toLocaleString()}</div>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                ownersHtml = '<p style="text-align: center; color: #888; padding: 20px;">No shareholders yet. Be the first!</p>';
            }
            
            document.getElementById('ownership-content').innerHTML = `
                <div style="display: flex; justify-content: space-around; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.9em; color: #888;">Total Shares</div>
                        <div style="font-size: 1.5em; font-weight: bold;">${totalShares.toLocaleString()}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.9em; color: #888;">Shareholders</div>
                        <div style="font-size: 1.5em; font-weight: bold;">${ownersCount}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.9em; color: #888;">Public Float</div>
                        <div style="font-size: 1.5em; font-weight: bold;">${publicFloat.toFixed(1)}%</div>
                    </div>
                </div>
                <h3 style="margin-bottom: 10px;">Top Shareholders</h3>
                <div style="max-height: 400px; overflow-y: auto;">
                    ${ownersHtml}
                </div>
            `;
        } else {
            document.getElementById('ownership-content').innerHTML = `<p style="color: #f44336;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error loading stock ownership:', error);
        document.getElementById('ownership-content').innerHTML = `<p style="color: #f44336;">Failed to load ownership data</p>`;
    }
}

function closeOwnershipModal() {
    document.getElementById('ownership-modal').style.display = 'none';
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
                    <input type="number" id="buy-${symbol}-amt" placeholder="Amount" min="0.01" step="0.01" value="1"
                           oninput="updateCryptoCostPreview('${symbol}', ${coin.price})">
                    <button onclick="buyCrypto('${symbol}')" class="btn btn-success">Buy</button>
                    <div id="cost-preview-crypto-${symbol}" class="cost-preview">Total: $${coin.price.toLocaleString()}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading crypto:', error);
    }
}

function updateCryptoCostPreview(symbol, price) {
    const amount = parseFloat(document.getElementById(`buy-${symbol}-amt`).value) || 0;
    const totalCost = Math.floor(price * amount);
    const previewElement = document.getElementById(`cost-preview-crypto-${symbol}`);
    if (previewElement && amount > 0) {
        previewElement.textContent = `Total: $${totalCost.toLocaleString()}`;
        previewElement.style.display = 'block';
    } else if (previewElement) {
        previewElement.style.display = 'none';
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
    const amount = await showInputModal(`🪙 Sell ${symbol}`, '1', `How much to sell? (You own ${owned.toFixed(4)})`);
    
    if (!amount || parseFloat(amount) <= 0) return;
    
    try {
        const response = await fetch('/api/sell_crypto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, amount: parseFloat(amount) })
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
    const amount = await showInputModal('💸 Pay Back Loan', '1000', 'How much do you want to pay?');
    
    if (!amount || parseInt(amount) <= 0) return;
    
    try {
        const response = await fetch('/api/pay_loan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: parseInt(amount), type })
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
                const items = data && data.items ? data.items : {};
                
                // Store all items globally for filtering
                allShopItems = items;
                
                // Apply current filters
                renderShopItems();
        } catch (error) {
                console.error('Error loading shop:', error);
        }
}

function renderShopItems() {
        const container = document.getElementById('shop-items');
        
        // Filter items based on current filters
        const filteredItems = Object.entries(allShopItems).filter(([id, item]) => {
                const category = item.category || 'other';
                const vehicleClass = item.class || '';
                
                // Category filter
                if (currentShopFilter !== 'all' && category !== currentShopFilter) {
                        return false;
                }
                
                // Vehicle class filter (only applies when filtering vehicles)
                if (currentShopFilter === 'vehicle' && currentVehicleClassFilter !== 'all') {
                        if (vehicleClass !== currentVehicleClassFilter) {
                                return false;
                        }
                }
                
                return true;
        });

        const cards = filteredItems.map(([id, item]) => {
                const type = (item.type || 'other').toString();
                const typeLabel = type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                const price = Number(item.price) || 0;
                const rentHourly = item.rentHourly ? Number(item.rentHourly) : 0;
                const rentDaily = item.rentDaily ? Number(item.rentDaily) : 0;
                const maxOwn = item.maxOwn;
                const hasMaxOwn = Number.isFinite(maxOwn);
                const maxOwnText = hasMaxOwn ? `${maxOwn}` : 'Unlimited';
                const category = item.category || 'other';
                const vehicleClass = item.class || '';

                return `
                    <div class="card shop-card" data-type="${type}" data-category="${category}" data-class="${vehicleClass}">
                        <div class="shop-card-top">
                            <div class="shop-title-row">
                                <h4 class="shop-title">${item.name}</h4>
                                <span class="shop-badge">${typeLabel}</span>
                            </div>
                            <div class="shop-price">$${price.toLocaleString()}</div>
                            <div class="shop-meta">
                                <div class="shop-chip">Max: <strong>${maxOwnText}</strong></div>
                                ${rentHourly ? `<div class="shop-chip">Rent: <strong>$${rentHourly.toLocaleString()}</strong>/hr</div>` : ''}
                                ${rentDaily ? `<div class="shop-chip">Rent: <strong>$${rentDaily.toLocaleString()}</strong>/day</div>` : ''}
                            </div>
                        </div>

                        <div class="shop-card-bottom">
                            <div class="shop-buy-row">
                                <input class="shop-qty" type="number" id="buy-shop-${id}-qty" min="1" value="1"
                                    oninput="updateShopCostPreview('${id}', ${price})" aria-label="Quantity">
                                <button onclick="buyItem('${id}')" class="btn btn-success shop-buy-btn">Buy</button>
                            </div>
                            <div id="cost-preview-shop-${id}" class="cost-preview">Total: $${price.toLocaleString()}</div>
                        </div>
                    </div>
                `;
        }).join('');

        const resultText = filteredItems.length === 0 
                ? '<p style="text-align: center; color: #888; padding: 20px;">No items match your filters</p>'
                : `<div class="shop-grid">${cards}</div>`;
        
        container.innerHTML = resultText;
}

function filterShop(category) {
        currentShopFilter = category;
        currentVehicleClassFilter = 'all'; // Reset vehicle class filter
        
        // Update button styles
        document.querySelectorAll('[id^="filter-"]').forEach(btn => {
                btn.style.background = '';
        });
        document.getElementById(`filter-${category}`).style.background = '#4CAF50';
        
        // Show/hide vehicle subfilters
        const subfilters = document.getElementById('vehicle-subfilters');
        if (subfilters) {
                subfilters.style.display = category === 'vehicle' ? 'block' : 'none';
        }
        
        // Reset vehicle class button styles
        document.querySelectorAll('[id^="vclass-"]').forEach(btn => {
                btn.style.background = '';
        });
        const vclassAll = document.getElementById('vclass-all');
        if (vclassAll) vclassAll.style.background = '#4CAF50';
        
        renderShopItems();
}

function filterVehicleClass(vehicleClass) {
        currentVehicleClassFilter = vehicleClass;
        
        // Update button styles
        document.querySelectorAll('[id^="vclass-"]').forEach(btn => {
                btn.style.background = '';
        });
        document.getElementById(`vclass-${vehicleClass}`).style.background = '#4CAF50';
        
        renderShopItems();
}

function updateShopCostPreview(itemId, price) {
    const quantity = parseInt(document.getElementById(`buy-shop-${itemId}-qty`).value) || 0;
    const totalCost = price * quantity;
    const previewElement = document.getElementById(`cost-preview-shop-${itemId}`);
    if (previewElement && quantity > 0) {
        previewElement.textContent = `Total: $${totalCost.toLocaleString()}`;
        previewElement.style.display = 'block';
    } else if (previewElement) {
        previewElement.style.display = 'none';
    }
}

async function buyItem(itemId) {
    const quantity = parseInt(document.getElementById(`buy-shop-${itemId}-qty`).value) || 1;
    
    if (!quantity || quantity <= 0) {
        showModal('❌ Invalid quantity');
        return;
    }
    
    try {
        const response = await fetch('/api/buy_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, quantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Check if this is a mystery box with rewards
            if (data.rewards && data.rewards.length > 0) {
                showMysteryBoxRewards(data.rewards, data.tier);
            } else {
                showModal(`✅ Purchased ${quantity} item(s) for $${data.total_cost.toLocaleString()}`);
            }
            updateStats();
            loadInventory();
        } else {
            showModal(`❌ ${data.error}`);
        }
    } catch (error) {
        showModal('❌ Error buying item');
    }
}

function showMysteryBoxRewards(rewards, tier = 'Unknown') {
    const tierNames = { '1': 'Tier 1 (Premium)', '2': 'Tier 2', '3': 'Tier 3' };
    const tierName = tierNames[tier] || `Tier ${tier}`;
    
    const rewardsHtml = rewards.map(reward => {
        const emoji = getRewardEmoji(reward.item);
        const rarity = getRewardRarity(reward.item);
        const rarityColor = getRarityColor(rarity);
        
        return `
            <div style="padding: 12px; margin: 8px 0; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid ${rarityColor};">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 2em;">${emoji}</span>
                    <div style="flex: 1; text-align: left;">
                        <div style="font-weight: bold; font-size: 1.1em;">${reward.item}</div>
                        <div style="color: #888; font-size: 0.9em;">Quantity: ${reward.quantity}</div>
                        <div style="color: ${rarityColor}; font-size: 0.85em; font-weight: bold;">${rarity}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('mysterybox-rewards').innerHTML = `
        <div style="font-size: 1.2em; color: #4CAF50; margin-bottom: 15px;">
            🎁 ${tierName} Mystery Box
        </div>
        ${rewardsHtml}
    `;
    
    document.getElementById('mysterybox-modal').style.display = 'flex';
}

function closeMysteryBoxModal() {
    document.getElementById('mysterybox-modal').style.display = 'none';
}

function getRewardEmoji(itemName) {
    const lower = itemName.toLowerCase();
    if (lower.includes('car') || lower.includes('vehicle') || lower.includes('sedan') || lower.includes('suv')) return '🚗';
    if (lower.includes('gold')) return '🏆';
    if (lower.includes('silver')) return '🥈';
    if (lower.includes('diamond')) return '💎';
    if (lower.includes('ruby')) return '💍';
    if (lower.includes('emerald')) return '💚';
    if (lower.includes('platinum')) return '⭐';
    if (lower.includes('watch')) return '⌚';
    if (lower.includes('art')) return '🖼️';
    if (lower.includes('cookie')) return '🍪';
    if (lower.includes('jar')) return '🏺';
    return '🎁';
}

function getRewardRarity(itemName) {
    const lower = itemName.toLowerCase();
    // Luxury/Sports cars and high-value items
    if (lower.includes('sports') || lower.includes('luxury') || lower.includes('diamond') || lower.includes('art') || lower.includes('watch')) {
        return 'LEGENDARY';
    }
    // Gold, vehicles, precious gems
    if (lower.includes('gold') || lower.includes('ruby') || lower.includes('emerald') || lower.includes('platinum') || lower.includes('car')) {
        return 'RARE';
    }
    // Silver and collectibles
    if (lower.includes('silver') || lower.includes('jar')) {
        return 'UNCOMMON';
    }
    // Basic items
    return 'COMMON';
}

function getRarityColor(rarity) {
    switch(rarity) {
        case 'LEGENDARY': return '#ff9800';
        case 'RARE': return '#9c27b0';
        case 'UNCOMMON': return '#2196f3';
        case 'COMMON': return '#4CAF50';
        default: return '#888';
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
    
    const confirmed = await showConfirmModal(`Are you sure you want to rob player ${targetId}? You could get caught and jailed!`);
    if (!confirmed) {
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
                    <span>${player.username ?? player.id ?? ''}</span>
                </div>
                <span class="leaderboard-worth">$${player.total_worth.toLocaleString()}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// ==================== ECONOMY ====================

async function loadEconomy() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Tax Information
        document.getElementById('tax-rate').textContent = (config.taxRate * 100).toFixed(1) + '%';
        document.getElementById('high-income-rate').textContent = (config.highIncomeRate * 100).toFixed(1) + '%';
        document.getElementById('gov-tax-percent').textContent = config.govTaxPercent + '%';
        document.getElementById('inflation-rate').textContent = (config.inflation * 100).toFixed(1) + '%';
        
        // Economic Status
        document.getElementById('economy-interest-rate').textContent = config.interestRate + '% daily';
        document.getElementById('bank-vault').innerHTML = `<span class="value-positive">$${config.centralBankVault.toLocaleString()}</span>`;
        
        // Status indicators with color coding
        document.getElementById('economy-recession').innerHTML = config.recession 
            ? '<span style="color: #ff9800; font-weight: bold;">⚠️ Active</span>' 
            : '<span style="color: #4CAF50;">✅ Normal</span>';
        
        document.getElementById('economy-depression').innerHTML = config.depression 
            ? '<span style="color: #f44336; font-weight: bold;">🚨 Active</span>' 
            : '<span style="color: #4CAF50;">✅ Normal</span>';
        
        document.getElementById('economy-shutdown').innerHTML = config.govShutdown 
            ? '<span style="color: #f44336; font-weight: bold;">⚠️ Active</span>' 
            : '<span style="color: #4CAF50;">✅ Operating</span>';
        
        document.getElementById('economy-strike').innerHTML = config.strikeMode 
            ? '<span style="color: #ff9800; font-weight: bold;">⚠️ Active</span>' 
            : '<span style="color: #4CAF50;">✅ Normal</span>';
        
        // Department Budgets
        const budgets = config.departmentBudgets || {
            transportation: 0,
            justice: 0,
            defense: 0,
            homeland: 0,
            health: 0,
            housing: 0,
            education: 0
        };
        
        document.getElementById('dept-transportation').textContent = '$' + Math.floor(budgets.transportation).toLocaleString();
        document.getElementById('dept-justice').textContent = '$' + Math.floor(budgets.justice).toLocaleString();
        document.getElementById('dept-defense').textContent = '$' + Math.floor(budgets.defense).toLocaleString();
        document.getElementById('dept-homeland').textContent = '$' + Math.floor(budgets.homeland).toLocaleString();
        document.getElementById('dept-health').textContent = '$' + Math.floor(budgets.health).toLocaleString();
        document.getElementById('dept-housing').textContent = '$' + Math.floor(budgets.housing).toLocaleString();
        document.getElementById('dept-education').textContent = '$' + Math.floor(budgets.education).toLocaleString();
        
    } catch (error) {
        console.error('Error loading economy data:', error);
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

        // Update bell badge
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.textContent = data.unread > 0 ? data.unread : '';
        }

        // Update dropdown list
        const container = document.getElementById('notifications-dropdown-list');
        if (!container) return;

        if (!data.notifications || data.notifications.length === 0) {
            container.innerHTML = '<div class="notification-empty">No notifications yet.</div>';
            return;
        }

        container.innerHTML = data.notifications.slice(0, 15).map(n => {
            const level = (n.level || 'info').toLowerCase();
            const levelClass = ['success', 'warning', 'danger', 'info'].includes(level) ? level : 'info';
            const levelLabel = levelClass.toUpperCase();

            return `
            <div class="notification-dropdown-item ${n.read ? 'read' : 'unread'}">
                <div class="notification-content">
                    <p style="margin: 0; font-size: 0.9rem;">${n.message}</p>
                    <div class="notification-meta">
                        <span class="status-badge ${levelClass}">${levelLabel}</span>
                        <small class="text-muted">${new Date(n.createdAt).toLocaleString()}</small>
                    </div>
                </div>
                ${n.read ? '' : `
                <div class="notification-actions">
                    <button class="btn-mark-read" onclick="markNotificationRead(${n.id}); event.stopPropagation();">Read</button>
                </div>
                `}
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    if (!dropdown) return;
    
    const isVisible = dropdown.style.display === 'block';
    dropdown.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
        loadNotifications();
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const bellContainer = document.querySelector('.notification-bell-container');
    const dropdown = document.getElementById('notification-dropdown');
    
    if (bellContainer && dropdown && !bellContainer.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

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
        await loadPlayerInfo(balance);
        loadFriends();
        loadProfileStats(); // Load profile statistics
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadProfileStats() {
    try {
        const response = await fetch('/api/profile/stats');
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('stat-total-earned').textContent = `$${data.totalEarned.toLocaleString()}`;
            document.getElementById('stat-total-spent').textContent = `$${data.totalSpent.toLocaleString()}`;
            document.getElementById('stat-total-worked').textContent = data.totalWorked.toLocaleString();
            
            const loginStreakText = data.loginStreak > 0 ? `${data.loginStreak} days 🔥` : '0 days';
            document.getElementById('stat-login-streak').textContent = loginStreakText;
            
            const workStreakText = data.workStreak > 0 ? `${data.workStreak} days 🔥` : '0 days';
            document.getElementById('stat-work-streak').textContent = workStreakText;
            
            document.getElementById('stat-account-age').textContent = data.accountAge;
        }
    } catch (error) {
        console.error('Error loading profile stats:', error);
    }
}

async function loadPlayerInfo(balance) {
    try {
        // Load inventory for properties
        const inventoryRes = await fetch('/api/inventory');
        const inventory = await inventoryRes.json();
        
        // Update insurance status
        const insuranceElement = document.getElementById('insurance-status');
        if (insuranceElement) {
            if (balance && balance.hasInsurance) {
                insuranceElement.innerHTML = '<span style="color: #4CAF50;">✅ Insured</span>';
            } else {
                insuranceElement.innerHTML = '<span style="color: #f44336;">❌ Not Insured</span>';
            }
        }
        
        // Update properties list
        const propertiesList = document.getElementById('properties-list');
        if (propertiesList) {
            const housingItems = inventory.inventory.filter(item => item.type === 'housing');
            
            if (housingItems.length === 0) {
                propertiesList.innerHTML = '<li style="color: #999;">No properties owned</li>';
            } else {
                propertiesList.innerHTML = housingItems.map(item => 
                    `<li>${item.name} (x${item.quantity})</li>`
                ).join('');
            }
        }
        
    } catch (error) {
        console.error('Error loading player info:', error);
        // Set fallback values on error
        const insuranceElement = document.getElementById('insurance-status');
        if (insuranceElement) {
            insuranceElement.innerHTML = '<span style="color: #999;">Error loading</span>';
        }
        const propertiesList = document.getElementById('properties-list');
        if (propertiesList) {
            propertiesList.innerHTML = '<li style="color: #999;">Error loading properties</li>';
        }
    }
}

async function loadFriends() {
    try {
        const response = await fetch('/api/friends');
        const data = await response.json();

        // Me / friend code
        const myCodeEl = document.getElementById('my-friend-code');
        if (myCodeEl) {
            const code = data?.me?.friend_code;
            myCodeEl.textContent = code ? code : '—';
        }
        
        // Friend requests
        const requestsList = document.getElementById('friend-requests-list');
        if (data.requests.length === 0) {
            requestsList.innerHTML = '<p style="color: #999; margin: 5px 0;">No pending requests</p>';
        } else {
            requestsList.innerHTML = data.requests.map(req => `
                <div style="padding: 8px; background: #f0f0f0; margin: 5px 0; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span>${req.from_display}${req.from_code ? ` <small style=\"color:#666\">(#${req.from_code})</small>` : ''}</span>
                    <div>
                        <button onclick="acceptFriend('${req.from}')" class="btn btn-success" style="padding: 4px 8px; font-size: 12px; margin-right: 5px;">Accept</button>
                    </div>
                </div>
            `).join('');
        }
        
        // Friends list
        const friendsList = document.getElementById('friends-list');
        if (data.friends.length === 0) {
            friendsList.innerHTML = '<p style="color: #999; margin: 5px 0;">No friends yet</p>';
        } else {
            friendsList.innerHTML = data.friends.map(friend => `
                <div style="padding: 8px; background: #e3f2fd; margin: 5px 0; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span>${friend.username}${friend.friend_code ? ` <small style=\"color:#1e3a8a\">(#${friend.friend_code})</small>` : ''}</span>
                    <button onclick="removeFriend('${friend.username}')" class="btn btn-danger" style="padding: 4px 8px; font-size: 12px;">Remove</button>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading friends:', error);
    }
}

async function sendFriendRequest() {
    const targetId = document.getElementById('friend-request-id').value.trim();
    
    if (!targetId) {
        showModal('❌ Please enter a username or 6-digit ID');
        return;
    }
    
    try {
        const response = await fetch('/api/friends/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: targetId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ ' + data.message);
            document.getElementById('friend-request-id').value = '';
            loadFriends();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error sending friend request');
    }
}

async function lookupFriendCode() {
    const input = document.getElementById('friend-lookup-username');
    const out = document.getElementById('friend-lookup-result');
    if (!input || !out) return;

    const username = input.value.trim();
    if (!username) {
        out.textContent = 'Enter a username.';
        return;
    }

    out.textContent = 'Looking up...';
    try {
        const res = await fetch('/api/users/lookup?username=' + encodeURIComponent(username));
        const data = await res.json();
        if (!res.ok) {
            out.textContent = data?.error || 'Not found.';
            return;
        }
        out.textContent = `${data.username} → ${data.friend_code}`;
    } catch (e) {
        out.textContent = 'Lookup failed.';
    }
}

async function acceptFriend(fromId) {
    try {
        const response = await fetch('/api/friends/accept', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from_id: fromId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ ' + data.message);
            loadFriends();
            loadNotifications();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error accepting friend request');
    }
}

// ============================================================================
// MODERATOR: Economic Rate Change Requests
// ============================================================================

async function loadCurrentRatesForRequest() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Fill in the current rates
        document.getElementById('mod-request-tax').value = (config.taxRate * 100).toFixed(1);
        document.getElementById('mod-request-high-income').value = (config.highIncomeRate * 100).toFixed(1);
        document.getElementById('mod-request-gov').value = config.govTaxPercent;
        document.getElementById('mod-request-inflation').value = (config.inflation * 100).toFixed(1);
        
        const statusEl = document.getElementById('mod-request-status');
        statusEl.textContent = '✅ Current rates loaded';
        statusEl.style.color = '#16a34a';
        setTimeout(() => {
            statusEl.textContent = '';
            statusEl.style.color = '';
        }, 2000);
    } catch (error) {
        console.error('Error loading rates:', error);
        showModal('❌ Failed to load current rates');
    }
}

async function submitModeratorRateRequest() {
    const taxRate = document.getElementById('mod-request-tax').value;
    const highIncomeRate = document.getElementById('mod-request-high-income').value;
    const govTaxPercent = document.getElementById('mod-request-gov').value;
    const inflation = document.getElementById('mod-request-inflation').value;
    const reason = document.getElementById('mod-request-reason').value.trim();
    
    // Build changes object (only include fields that were filled)
    const changes = {};
    if (taxRate) changes.taxRate = parseFloat(taxRate) / 100;
    if (highIncomeRate) changes.highIncomeRate = parseFloat(highIncomeRate) / 100;
    if (govTaxPercent) changes.govTaxPercent = parseInt(govTaxPercent);
    if (inflation) changes.inflation = parseFloat(inflation) / 100;
    
    if (Object.keys(changes).length === 0) {
        showModal('❌ Please fill in at least one rate to request changes');
        return;
    }
    
    if (!reason) {
        showModal('❌ Please provide a reason for the rate changes');
        return;
    }
    
    try {
        const response = await fetch('/api/moderator/request-rate-change', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ changes, reason })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Rate change request sent to owner!');
            
            // Clear form
            document.getElementById('mod-request-tax').value = '';
            document.getElementById('mod-request-high-income').value = '';
            document.getElementById('mod-request-gov').value = '';
            document.getElementById('mod-request-inflation').value = '';
            document.getElementById('mod-request-reason').value = '';
            
            const statusEl = document.getElementById('mod-request-status');
            statusEl.textContent = '✅ Request submitted successfully!';
            statusEl.style.color = '#16a34a';
            setTimeout(() => {
                statusEl.textContent = '';
                statusEl.style.color = '';
            }, 3000);
        } else {
            showModal('❌ ' + (data.error || 'Failed to submit request'));
        }
    } catch (error) {
        console.error('Error submitting rate request:', error);
        showModal('❌ Error submitting request');
    }
}

// ============================================================================
// ADVISOR HELP SYSTEM
// ============================================================================

const ADVISOR_HELP = {
    'none': {
        name: 'No Advisor',
        description: 'No modifiers applied.',
        effects: ['Standard gameplay with no bonuses or penalties'],
        image: null
    },
    'helper': {
        name: 'Helper Advisor',
        description: 'Provides guidance notifications only.',
        effects: [
            '💡 Receives helpful tips and notifications',
            '📊 No gameplay modifiers',
            '✨ Perfect for learning the game'
        ],
        image: null
    },
    'miranda': {
        name: 'Miranda (Lawyer)',
        description: 'Better legal protection, but slower growth.',
        effects: [
            '⚖️ Better legal protection in criminal activities',
            '📉 Slower income and growth rates',
            '🔒 Reduced penalties when caught',
            '💼 Business ventures more stable but less profitable'
        ],
        image: 'game_images/Miranda_Advisor.png'
    },
    'gina': {
        name: 'Gina (Hotel Owner)',
        description: 'Business gains stronger, stocks less effective.',
        effects: [
            '🏨 Business profits increased significantly',
            '📈 Property and real estate bonuses',
            '📉 Stock trading returns reduced',
            '💰 Real-world business focus over speculation'
        ],
        image: 'game_images/Gina_Advisor.png'
    },
    'katie': {
        name: 'Katie (Hollywood Star)',
        description: 'Lifestyle is more expensive.',
        effects: [
            '✨ Glamorous lifestyle with premium costs',
            '💸 Higher living expenses',
            '🎬 Celebrity status perks',
            '⚠️ Luxury comes at a price'
        ],
        image: 'game_images/Katie_Advisor.png'
    },
    'rivera': {
        name: 'Rivera (Criminal)',
        description: 'Lower crime detection, harsher penalties.',
        effects: [
            '🎭 Lower chance of getting caught in crimes',
            '⚡ Criminal activities more successful',
            '⚠️ Much harsher penalties if caught',
            '🔴 High risk, high reward strategy'
        ],
        image: 'game_images/Rivera_Advisor.png'
    }
};

function showAdvisorHelp() {
    const select = document.getElementById('advisor-select');
    const selectedAdvisor = select ? select.value : 'none';
    
    const advisorInfo = ADVISOR_HELP[selectedAdvisor] || ADVISOR_HELP['none'];
    
    let modalHTML = `
        <div style="text-align: left; max-width: 500px;">
            <h2 style="margin-bottom: 15px; color: #667eea;">🎭 ${advisorInfo.name}</h2>
            ${advisorInfo.image ? `<img src="/${advisorInfo.image}" alt="${advisorInfo.name}" style="width: 100%; max-width: 300px; border-radius: 10px; margin: 15px auto; display: block;">` : ''}
            <p style="margin: 15px 0; font-size: 1.1em; color: #555;">${advisorInfo.description}</p>
            <h3 style="margin: 20px 0 10px 0; color: #333;">Effects:</h3>
            <ul style="padding-left: 20px; line-height: 1.8;">
                ${advisorInfo.effects.map(effect => `<li>${effect}</li>`).join('')}
            </ul>
            <div style="margin-top: 20px; padding: 15px; background: #f0f4ff; border-radius: 8px; border-left: 4px solid #667eea;">
                <strong>💡 Tip:</strong> Choose an advisor that matches your playstyle! You can change advisors anytime from the Advisor section.
            </div>
        </div>
    `;
    
    showModal(modalHTML);
}

async function removeFriend(friendId) {
    const confirmed = await showConfirmModal('Are you sure you want to remove this friend?');
    if (!confirmed) return;
    
    try {
        const response = await fetch('/api/friends/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ friend_id: friendId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ ' + data.message);
            loadFriends();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error removing friend');
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
            showModal('✅ ' + (data.message || 'Hourly updates processed.'));
            updateStats();
            try { loadDashboard(); } catch (e) { /* ignore */ }
            try { loadStocks(); } catch (e) { /* ignore */ }
            try { loadCrypto(); } catch (e) { /* ignore */ }
            try { loadEconomy(); } catch (e) { /* ignore */ }
        } else {
            showModal('❌ ' + (data.error || 'Failed to process hourly updates'));
        }
    } catch (error) {
        showModal('❌ Error processing hourly updates');
    }
}

// ==================== FEEDBACK WIDGET ====================

let feedbackSelectedRating = null;

function toggleFeedbackPanel(forceOpen = null) {
    const panel = document.getElementById('feedback-panel');
    if (!panel) return;
    const isOpen = panel.classList.contains('open');
    const shouldOpen = forceOpen === null ? !isOpen : !!forceOpen;
    panel.classList.toggle('open', shouldOpen);
}

function selectFeedbackRating(rating) {
    feedbackSelectedRating = rating;
    document.querySelectorAll('.feedback-rating-dot').forEach(el => {
        el.classList.toggle('selected', Number(el.dataset.rating) === Number(rating));
    });
}

async function submitFeedback() {
    const messageEl = document.getElementById('feedback-message');
    if (!messageEl) return;

    const message = messageEl.value.trim();
    if (!message) {
        showModal('❌ Please type feedback before submitting');
        return;
    }

    const payload = { message };
    if (feedbackSelectedRating !== null) payload.rating = feedbackSelectedRating;

    try {
        const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            showModal('❌ ' + (data?.error || 'Error sending feedback'));
            return;
        }

        showModal('✅ Thanks! Feedback sent.');
        messageEl.value = '';
        feedbackSelectedRating = null;
        document.querySelectorAll('.feedback-rating-dot').forEach(el => el.classList.remove('selected'));
        toggleFeedbackPanel(false);
    } catch (e) {
        showModal('❌ Error sending feedback');
    }
}

function setupFeedbackWidget() {
    const openBtn = document.getElementById('feedback-fab');
    const closeBtn = document.getElementById('feedback-close');
    const submitBtn = document.getElementById('feedback-submit');
    if (openBtn) openBtn.addEventListener('click', () => toggleFeedbackPanel());
    if (closeBtn) closeBtn.addEventListener('click', () => toggleFeedbackPanel(false));
    if (submitBtn) submitBtn.addEventListener('click', submitFeedback);

    document.querySelectorAll('.feedback-rating-dot').forEach(el => {
        el.addEventListener('click', () => selectFeedbackRating(Number(el.dataset.rating)));
    });
}

// ==================== ACHIEVEMENTS ====================

async function loadAchievements() {
    try {
        const response = await fetch('/api/achievements');
        const data = await response.json();
        
        if (!response.ok) {
            showModal('❌ Error loading achievements');
            return;
        }
        
        // Update stats
        const totalAchievements = Object.values(data.achievements).reduce((sum, category) => sum + category.length, 0);
        document.getElementById('achievement-count').textContent = `${data.total_unlocked}/${totalAchievements}`;
        
        // Calculate total rewards
        const totalRewards = Object.values(data.achievements)
            .flat()
            .filter(ach => ach.unlocked)
            .reduce((sum, ach) => sum + ach.reward, 0);
        document.getElementById('achievement-rewards').textContent = `$${totalRewards.toLocaleString()}`;
        
        // Render each category
        renderAchievementCategory('wealth', data.achievements.wealth);
        renderAchievementCategory('work', data.achievements.work);
        renderAchievementCategory('crime', data.achievements.crime);
        renderAchievementCategory('social', data.achievements.social);
        renderAchievementCategory('special', data.achievements.special);
        
    } catch (error) {
        console.error('Error loading achievements:', error);
        showModal('❌ Error loading achievements');
    }
}

function renderAchievementCategory(category, achievements) {
    const container = document.getElementById(`achievements-${category}`);
    if (!container) return;
    
    if (!achievements || achievements.length === 0) {
        container.innerHTML = '<p class="no-achievements">No achievements in this category yet.</p>';
        return;
    }
    
    container.innerHTML = achievements.map(ach => {
        const isUnlocked = ach.unlocked;
        const progress = ach.progress || 0;
        
        return `
            <div class="achievement-card ${isUnlocked ? 'unlocked' : 'locked'}">
                <div class="achievement-icon">${isUnlocked ? ach.icon : '🔒'}</div>
                <div class="achievement-info">
                    <h4 class="achievement-name">${ach.name}</h4>
                    <p class="achievement-description">${ach.description}</p>
                    ${!isUnlocked ? `
                        <div class="achievement-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progress}%"></div>
                            </div>
                            <span class="progress-text">${progress}%</span>
                        </div>
                    ` : `
                        <div class="achievement-reward">
                            💰 Reward: $${ach.reward.toLocaleString()}
                        </div>
                    `}
                </div>
                ${isUnlocked ? '<div class="achievement-unlocked-badge">✓ UNLOCKED</div>' : ''}
            </div>
        `;
    }).join('');
}

// ==================== CASINO SYSTEM ====================

let currentSlotBet = 1000;

async function loadCasinoStats() {
    try {
        const response = await fetch('/api/casino/stats');
        const stats = await response.json();

        const formatSigned = (value) => {
            const n = Number(value) || 0;
            const abs = Math.abs(n);
            const base = abs.toLocaleString();
            if (n > 0) return `+${base}`;
            if (n < 0) return `-${base}`;
            return '0';
        };

        const setValueClass = (el, value) => {
            if (!el) return;
            el.classList.add('casino-stat-value');
            el.classList.remove('is-pos', 'is-neg', 'is-zero');
            const n = Number(value) || 0;
            if (n > 0) el.classList.add('is-pos');
            else if (n < 0) el.classList.add('is-neg');
            else el.classList.add('is-zero');
        };
        
        const elSlotsPlayed = document.getElementById('stat-slots-played');
        const elSlotsWagered = document.getElementById('stat-slots-wagered');
        const elSlotsProfit = document.getElementById('stat-slots-won');
        const elSlotsBiggest = document.getElementById('stat-biggest-slots-win');
        const elBjPlayed = document.getElementById('stat-blackjack-played');
        const elBjWagered = document.getElementById('stat-blackjack-wagered');
        const elBjProfit = document.getElementById('stat-blackjack-won');

        if (elSlotsPlayed) elSlotsPlayed.textContent = stats.slots_played || 0;
        if (elSlotsWagered) elSlotsWagered.textContent = (stats.slots_wagered || 0).toLocaleString();
        if (elSlotsProfit) elSlotsProfit.textContent = formatSigned(stats.slots_won || 0);
        if (elSlotsBiggest) elSlotsBiggest.textContent = formatSigned(stats.biggest_slots_win || 0);
        if (elBjPlayed) elBjPlayed.textContent = stats.blackjack_played || 0;
        if (elBjWagered) elBjWagered.textContent = (stats.blackjack_wagered || 0).toLocaleString();
        if (elBjProfit) elBjProfit.textContent = formatSigned(stats.blackjack_won || 0);

        // Color-code the profit stats only.
        setValueClass(elSlotsProfit, stats.slots_won || 0);
        setValueClass(elSlotsBiggest, stats.biggest_slots_win || 0);
        setValueClass(elBjProfit, stats.blackjack_won || 0);
    } catch (error) {
        console.error('Error loading casino stats:', error);
    }
}

function selectSlotBet(amount) {
    currentSlotBet = amount;
    document.getElementById('slot-current-bet').textContent = amount.toLocaleString();
    document.getElementById('spin-bet-display').textContent = amount.toLocaleString();
    
    // Update button styling
    document.querySelectorAll('.bet-btn').forEach(btn => {
        btn.classList.remove('selected-bet');
    });
    event.target.classList.add('selected-bet');
}

async function spinSlots() {
    const spinButton = document.getElementById('spin-button');
    const slotMachine = document.querySelector('#tab-casino .slot-machine');
    const resultDiv = document.getElementById('slot-result');

    spinButton.disabled = true;
    spinButton.textContent = '🎰 SPINNING...';

    if (resultDiv) {
        resultDiv.style.display = 'none';
    }
    if (slotMachine) {
        slotMachine.classList.add('spinning');
    }
    
    // Animate reels
    const reels = [
        document.getElementById('reel-1'),
        document.getElementById('reel-2'),
        document.getElementById('reel-3')
    ];
    
    // Fast spin animation
    const symbols = ['💰', '💎', '🍒', '🔔', '7️⃣', '⭐', '🎰'];
    let spinCount = 0;
    const spinInterval = setInterval(() => {
        reels.forEach(reel => {
            reel.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        });
        spinCount++;
        if (spinCount > 20) {
            clearInterval(spinInterval);
        }
    }, 50);
    
    try {
        const response = await fetch('/api/casino/slots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet: currentSlotBet })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Wait for animation to finish
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Show final result
            reels[0].textContent = data.reels[0];
            reels[1].textContent = data.reels[1];
            reels[2].textContent = data.reels[2];
            
            // Show result message
            if (resultDiv) {
                resultDiv.textContent = data.message;
                resultDiv.className = 'slot-result ' + (data.profit > 0 ? 'win' : 'lose');
                resultDiv.style.display = 'block';
            }
            
            // Update stats
            updateStats();
            loadCasinoStats();
            
            if (data.profit >= 50000) {
                showModal('🎉 ' + data.message + '\n\n🏆 Check your achievements!');
            }
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error playing slots');
    }

    clearInterval(spinInterval);
    if (slotMachine) {
        slotMachine.classList.remove('spinning');
    }
    
    spinButton.disabled = false;
    spinButton.textContent = `🎰 SPIN ($${currentSlotBet.toLocaleString()})`;
}

// Blackjack functions
async function startBlackjack() {
    const bet = parseInt(document.getElementById('blackjack-bet').value);
    
    if (!bet || bet < 100) {
        showModal('❌ Minimum bet is $100');
        return;
    }
    
    try {
        const response = await fetch('/api/casino/blackjack/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayBlackjackHands(data);
            
            if (data.game_over) {
                // Blackjack or push
                document.getElementById('blackjack-result').textContent = data.message;
                document.getElementById('blackjack-result').className = 'blackjack-result ' + data.result;
                document.getElementById('blackjack-result').style.display = 'block';
                document.getElementById('blackjack-start').style.display = 'block';
                document.getElementById('blackjack-actions').style.display = 'none';
                updateStats();
                loadCasinoStats();
            } else {
                // Game continues
                document.getElementById('blackjack-start').style.display = 'none';
                document.getElementById('blackjack-actions').style.display = 'block';
                document.getElementById('blackjack-result').style.display = 'none';
            }
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error starting blackjack');
    }
}

async function blackjackHit() {
    try {
        const response = await fetch('/api/casino/blackjack/hit', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayBlackjackHands(data);
            
            if (data.game_over) {
                // Bust
                document.getElementById('blackjack-result').textContent = data.message;
                document.getElementById('blackjack-result').className = 'blackjack-result ' + data.result;
                document.getElementById('blackjack-result').style.display = 'block';
                document.getElementById('blackjack-start').style.display = 'block';
                document.getElementById('blackjack-actions').style.display = 'none';
                updateStats();
                loadCasinoStats();
            }
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error hitting');
    }
}

async function blackjackStand() {
    try {
        const response = await fetch('/api/casino/blackjack/stand', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayBlackjackHands(data);
            
            // Game over - show result
            document.getElementById('blackjack-result').textContent = data.message;
            document.getElementById('blackjack-result').className = 'blackjack-result ' + data.result;
            document.getElementById('blackjack-result').style.display = 'block';
            document.getElementById('blackjack-start').style.display = 'block';
            document.getElementById('blackjack-actions').style.display = 'none';
            updateStats();
            loadCasinoStats();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error standing');
    }
}

function displayBlackjackHands(data) {
    // Display dealer hand
    const dealerHandDiv = document.getElementById('dealer-hand');
    dealerHandDiv.innerHTML = data.dealer_hand.map(card => 
        `<div class="playing-card ${card.suit === '♥' || card.suit === '♦' ? 'red' : 'black'}">
            <div class="card-rank">${card.rank}</div>
            <div class="card-suit">${card.suit}</div>
        </div>`
    ).join('');
    
    document.getElementById('dealer-value').textContent = `(${data.dealer_value})`;
    
    // Display player hand
    const playerHandDiv = document.getElementById('player-hand');
    playerHandDiv.innerHTML = data.player_hand.map(card => 
        `<div class="playing-card ${card.suit === '♥' || card.suit === '♦' ? 'red' : 'black'}">
            <div class="card-rank">${card.rank}</div>
            <div class="card-suit">${card.suit}</div>
        </div>`
    ).join('');
    
    document.getElementById('player-value').textContent = `(${data.player_value})`;
}

// ==================== TRADING SYSTEM ====================

let tradingUIInitialized = false;
let offerInventoryCache = null;
let offerInventoryCacheTime = 0;
let offerInventorySelectedId = null;

function toggleTradingGuide() {
    const panel = document.getElementById('trading-guide-panel');
    const btn = document.querySelector('.trade-guide-trigger');
    if (!panel) return;

    const isOpen = panel.classList.toggle('open');
    panel.setAttribute('aria-hidden', (!isOpen).toString());
    if (btn) btn.setAttribute('aria-expanded', isOpen.toString());
}

function setOfferAvailabilityText(text) {
    const el = document.getElementById('offer-item-available');
    if (!el) return;
    el.textContent = text || '';
}

function closeOfferInventoryPicker() {
    const picker = document.getElementById('offer-inventory-picker');
    const btn = document.querySelector('button[aria-controls="offer-inventory-picker"]');
    if (!picker) return;
    picker.classList.remove('open');
    picker.setAttribute('aria-hidden', 'true');
    if (btn) btn.setAttribute('aria-expanded', 'false');
}

function openOfferInventoryPicker() {
    const picker = document.getElementById('offer-inventory-picker');
    const btn = document.querySelector('button[aria-controls="offer-inventory-picker"]');
    if (!picker) return;
    picker.classList.add('open');
    picker.setAttribute('aria-hidden', 'false');
    if (btn) btn.setAttribute('aria-expanded', 'true');
}

function toggleOfferInventoryPicker() {
    const picker = document.getElementById('offer-inventory-picker');
    if (!picker) return;
    if (picker.classList.contains('open')) {
        closeOfferInventoryPicker();
        return;
    }
    openOfferInventoryPicker();
    ensureOfferInventoryLoaded({ force: false, silent: true });
}

function refreshOfferInventory() {
    ensureOfferInventoryLoaded({ force: true, silent: false });
}

function renderOfferInventoryList(items) {
    const listEl = document.getElementById('offer-inventory-list');
    if (!listEl) return;

    listEl.innerHTML = '';

    if (!items || items.length === 0) {
        const empty = document.createElement('div');
        empty.style.color = '#999';
        empty.textContent = 'Your inventory is empty.';
        listEl.appendChild(empty);
        return;
    }

    for (const item of items) {
        const row = document.createElement('div');
        row.className = 'inventory-item' + (offerInventorySelectedId === item.id ? ' selected' : '');
        row.tabIndex = 0;

        const main = document.createElement('div');
        main.className = 'inventory-item-main';

        const name = document.createElement('div');
        name.className = 'inventory-item-name';
        name.textContent = item.name || item.id;

        const id = document.createElement('div');
        id.className = 'inventory-item-id';
        id.textContent = item.id;

        main.appendChild(name);
        main.appendChild(id);

        const qty = document.createElement('div');
        qty.className = 'inventory-item-qty';
        qty.textContent = 'x' + (item.quantity ?? 0);

        row.appendChild(main);
        row.appendChild(qty);

        const select = () => selectOfferInventoryItem(item);
        row.addEventListener('click', select);
        row.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') select();
        });

        listEl.appendChild(row);
    }
}

function selectOfferInventoryItem(item) {
    const idInput = document.getElementById('offer-item-id');
    const qtyInput = document.getElementById('offer-item-qty');
    if (!idInput || !qtyInput) return;

    offerInventorySelectedId = item.id;
    idInput.value = item.id;

    const maxQty = Math.max(0, parseInt(item.quantity, 10) || 0);
    if (maxQty > 0) {
        qtyInput.max = String(maxQty);
        const current = parseInt(qtyInput.value, 10) || 0;
        const next = current > 0 ? Math.min(current, maxQty) : 1;
        qtyInput.value = String(next);
        setOfferAvailabilityText(`You have ${maxQty}`);
    } else {
        qtyInput.removeAttribute('max');
        setOfferAvailabilityText('');
    }

    if (offerInventoryCache) renderOfferInventoryList(offerInventoryCache);
    closeOfferInventoryPicker();
}

async function ensureOfferInventoryLoaded({ force = false, silent = false } = {}) {
    const listEl = document.getElementById('offer-inventory-list');

    const now = Date.now();
    const isFresh = offerInventoryCache && (now - offerInventoryCacheTime) < 30000;
    if (!force && isFresh) {
        renderOfferInventoryList(offerInventoryCache);
        return offerInventoryCache;
    }

    if (listEl) {
        listEl.innerHTML = '';
        const loading = document.createElement('div');
        loading.style.color = '#999';
        loading.textContent = 'Loading your inventory…';
        listEl.appendChild(loading);
    }

    try {
        const res = await fetch('/api/inventory');
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data?.error || 'Failed to load inventory');
        }

        const items = Array.isArray(data.inventory) ? data.inventory : [];
        items.sort((a, b) => (a.name || a.id || '').localeCompare((b.name || b.id || '')));

        offerInventoryCache = items;
        offerInventoryCacheTime = now;
        renderOfferInventoryList(items);
        return items;
    } catch (err) {
        console.error('Failed to load inventory for trading:', err);
        if (listEl) {
            listEl.innerHTML = '';
            const error = document.createElement('div');
            error.style.color = '#999';
            error.textContent = 'Could not load inventory.';
            listEl.appendChild(error);
        }
        if (!silent) {
            showModal('❌ Could not load your inventory for trading');
        }
        return [];
    }
}

function setupTradingUI() {
    if (tradingUIInitialized) return;

    const idInput = document.getElementById('offer-item-id');
    const qtyInput = document.getElementById('offer-item-qty');
    const picker = document.getElementById('offer-inventory-picker');
    const listEl = document.getElementById('offer-inventory-list');
    if (!idInput || !qtyInput || !picker || !listEl) return;

    tradingUIInitialized = true;

    idInput.addEventListener('input', () => {
        const current = idInput.value.trim();
        if (!current) {
            offerInventorySelectedId = null;
            qtyInput.removeAttribute('max');
            setOfferAvailabilityText('');
            if (offerInventoryCache) renderOfferInventoryList(offerInventoryCache);
            return;
        }

        if (offerInventorySelectedId && current !== offerInventorySelectedId) {
            offerInventorySelectedId = null;
            qtyInput.removeAttribute('max');
            setOfferAvailabilityText('');
            if (offerInventoryCache) renderOfferInventoryList(offerInventoryCache);
        }
    });

    qtyInput.addEventListener('input', () => {
        const maxAttr = qtyInput.getAttribute('max');
        const max = maxAttr ? parseInt(maxAttr, 10) : 0;
        const current = parseInt(qtyInput.value, 10) || 0;
        if (max > 0 && current > max) {
            qtyInput.value = String(max);
        }
    });

    // Preload inventory quietly so the picker feels instant.
    ensureOfferInventoryLoaded({ force: false, silent: true });
}

async function loadTrades() {
    try {
        // Load active trades
        const activeRes = await fetch('/api/trades/active');
        const activeTrades = await activeRes.json();
        
        // Display received trades
        const receivedDiv = document.getElementById('trades-received');
        if (activeTrades.received && activeTrades.received.length > 0) {
            receivedDiv.innerHTML = activeTrades.received.map(trade => `
                <div class="trade-card">
                    <div class="trade-header">
                        <span class="trade-from">From: <strong>${trade.initiator}</strong></span>
                        <span class="trade-time">${new Date(trade.created_at).toLocaleString()}</span>
                    </div>
                    <div class="trade-details">
                        <div class="trade-offer">
                            <h5>They Offer:</h5>
                            ${formatTradeItems(trade.offer)}
                        </div>
                        <div class="trade-request">
                            <h5>They Want:</h5>
                            ${formatTradeItems(trade.request)}
                        </div>
                    </div>
                    <div class="trade-actions">
                        <button onclick="acceptTrade('${trade.id}')" class="btn btn-success">✅ Accept</button>
                        <button onclick="declineTrade('${trade.id}')" class="btn btn-danger">❌ Decline</button>
                    </div>
                </div>
            `).join('');
        } else {
            receivedDiv.innerHTML = '<p style="color: #999;">No pending trade requests</p>';
        }
        
        // Display sent trades
        const sentDiv = document.getElementById('trades-sent');
        if (activeTrades.sent && activeTrades.sent.length > 0) {
            sentDiv.innerHTML = activeTrades.sent.map(trade => `
                <div class="trade-card">
                    <div class="trade-header">
                        <span class="trade-to">To: <strong>${trade.target}</strong></span>
                        <span class="trade-time">${new Date(trade.created_at).toLocaleString()}</span>
                    </div>
                    <div class="trade-details">
                        <div class="trade-offer">
                            <h5>You Offer:</h5>
                            ${formatTradeItems(trade.offer)}
                        </div>
                        <div class="trade-request">
                            <h5>You Want:</h5>
                            ${formatTradeItems(trade.request)}
                        </div>
                    </div>
                    <div class="trade-actions">
                        <button onclick="cancelTrade('${trade.id}')" class="btn btn-warning">🚫 Cancel</button>
                    </div>
                </div>
            `).join('');
        } else {
            sentDiv.innerHTML = '<p style="color: #999;">No outgoing trade requests</p>';
        }
        
        // Load trade history
        const historyRes = await fetch('/api/trades/history');
        const history = await historyRes.json();
        
        const historyDiv = document.getElementById('trade-history');
        if (history.history && history.history.length > 0) {
            historyDiv.innerHTML = history.history.reverse().map(trade => `
                <div class="trade-card history">
                    <div class="trade-header">
                        <span class="trade-partner">Partner: <strong>${trade.partner}</strong></span>
                        <span class="trade-time">${new Date(trade.completed_at).toLocaleString()}</span>
                    </div>
                    <div class="trade-details">
                        <div class="trade-sent">
                            <h5>You Gave:</h5>
                            ${formatTradeItems(trade.gave)}
                        </div>
                        <div class="trade-received">
                            <h5>You Received:</h5>
                            ${formatTradeItems(trade.received)}
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            historyDiv.innerHTML = '<p style="color: #999;">No completed trades</p>';
        }
    } catch (error) {
        console.error('Error loading trades:', error);
    }
}

function formatTradeItems(items) {
    const parts = [];
    
    if (items.money > 0) {
        parts.push(`💵 $${items.money.toLocaleString()}`);
    }
    
    for (const [itemId, qty] of Object.entries(items.items || {})) {
        if (qty > 0) {
            parts.push(`📦 ${itemId} (x${qty})`);
        }
    }
    
    for (const [symbol, shares] of Object.entries(items.stocks || {})) {
        if (shares > 0) {
            parts.push(`📈 ${symbol} (${shares} shares)`);
        }
    }
    
    for (const [symbol, amount] of Object.entries(items.crypto || {})) {
        if (amount > 0) {
            parts.push(`🪙 ${symbol} (${amount})`);
        }
    }
    
    if (parts.length === 0) {
        return '<p style="color: #999;">Nothing</p>';
    }
    
    return '<ul>' + parts.map(p => `<li>${p}</li>`).join('') + '</ul>';
}

async function createTrade() {
    const target = document.getElementById('trade-target').value.trim();
    
    if (!target) {
        showModal('❌ Please enter a username');
        return;
    }
    
    // Collect offer
    const offer = {
        money: parseInt(document.getElementById('offer-money').value) || 0,
        items: {},
        stocks: {},
        crypto: {}
    };
    
    const offerItemId = document.getElementById('offer-item-id').value.trim();
    const offerItemQty = parseInt(document.getElementById('offer-item-qty').value) || 0;
    if (offerItemId && offerItemQty > 0) {
        offer.items[offerItemId] = offerItemQty;
    }
    
    const offerStockSymbol = document.getElementById('offer-stock-symbol').value.trim();
    const offerStockShares = parseInt(document.getElementById('offer-stock-shares').value) || 0;
    if (offerStockSymbol && offerStockShares > 0) {
        offer.stocks[offerStockSymbol] = offerStockShares;
    }
    
    const offerCryptoSymbol = document.getElementById('offer-crypto-symbol').value.trim();
    const offerCryptoAmt = parseFloat(document.getElementById('offer-crypto-amt').value) || 0;
    if (offerCryptoSymbol && offerCryptoAmt > 0) {
        offer.crypto[offerCryptoSymbol] = offerCryptoAmt;
    }
    
    // Collect request
    const request = {
        money: parseInt(document.getElementById('request-money').value) || 0,
        items: {},
        stocks: {},
        crypto: {}
    };
    
    const requestItemId = document.getElementById('request-item-id').value.trim();
    const requestItemQty = parseInt(document.getElementById('request-item-qty').value) || 0;
    if (requestItemId && requestItemQty > 0) {
        request.items[requestItemId] = requestItemQty;
    }
    
    const requestStockSymbol = document.getElementById('request-stock-symbol').value.trim();
    const requestStockShares = parseInt(document.getElementById('request-stock-shares').value) || 0;
    if (requestStockSymbol && requestStockShares > 0) {
        request.stocks[requestStockSymbol] = requestStockShares;
    }
    
    const requestCryptoSymbol = document.getElementById('request-crypto-symbol').value.trim();
    const requestCryptoAmt = parseFloat(document.getElementById('request-crypto-amt').value) || 0;
    if (requestCryptoSymbol && requestCryptoAmt > 0) {
        request.crypto[requestCryptoSymbol] = requestCryptoAmt;
    }
    
    // Validate at least something is being traded
    const hasOffer = offer.money > 0 || Object.keys(offer.items).length > 0 || 
                     Object.keys(offer.stocks).length > 0 || Object.keys(offer.crypto).length > 0;
    const hasRequest = request.money > 0 || Object.keys(request.items).length > 0 || 
                       Object.keys(request.stocks).length > 0 || Object.keys(request.crypto).length > 0;
    
    if (!hasOffer && !hasRequest) {
        showModal('❌ Please specify what you want to trade');
        return;
    }
    
    try {
        const response = await fetch('/api/trades/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target,
                offer_money: offer.money,
                offer_items: offer.items,
                offer_stocks: offer.stocks,
                offer_crypto: offer.crypto,
                request_money: request.money,
                request_items: request.items,
                request_stocks: request.stocks,
                request_crypto: request.crypto
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Trade request sent!');
            
            // Clear form
            document.getElementById('trade-target').value = '';
            document.getElementById('offer-money').value = '0';
            document.getElementById('offer-item-id').value = '';
            document.getElementById('offer-item-qty').value = '0';
            document.getElementById('offer-stock-symbol').value = '';
            document.getElementById('offer-stock-shares').value = '0';
            document.getElementById('offer-crypto-symbol').value = '';
            document.getElementById('offer-crypto-amt').value = '0';
            document.getElementById('request-money').value = '0';
            document.getElementById('request-item-id').value = '';
            document.getElementById('request-item-qty').value = '0';
            document.getElementById('request-stock-symbol').value = '';
            document.getElementById('request-stock-shares').value = '0';
            document.getElementById('request-crypto-symbol').value = '';
            document.getElementById('request-crypto-amt').value = '0';
            
            loadTrades();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error creating trade');
    }
}

async function acceptTrade(tradeId) {
    if (!confirm('Accept this trade? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/trades/accept/${tradeId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Trade completed!');
            updateStats();
            loadTrades();
        } else {
            showModal('❌ ' + data.error);
            loadTrades(); // Refresh in case trade expired
        }
    } catch (error) {
        showModal('❌ Error accepting trade');
    }
}

async function declineTrade(tradeId) {
    try {
        const response = await fetch(`/api/trades/decline/${tradeId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Trade declined');
            loadTrades();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error declining trade');
    }
}

async function cancelTrade(tradeId) {
    try {
        const response = await fetch(`/api/trades/cancel/${tradeId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal('✅ Trade cancelled');
            loadTrades();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error cancelling trade');
    }
}

// ==================== BUSINESS MODE ====================

async function loadBusinessMode(focusBusinessId = null, focusBusinessName = '') {
    try {
        // If a business is focused, pass its id as a query parameter
        const bizId = focusBusinessId || (window.focusBusiness && window.focusBusiness.id) || null;
        const url = bizId ? `/api/business_mode/status?business_id=${encodeURIComponent(bizId)}` : '/api/business_mode/status';
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            console.error('Failed to load business mode:', data.error);
            return;
        }

        // If called with a business focus, display the focused business header
        const focusNode = document.getElementById('bm-focus');
        if (focusBusinessName && focusNode) {
            document.getElementById('bm-focus-name').textContent = focusBusinessName;
            focusNode.style.display = 'block';
        } else if (focusNode) {
            focusNode.style.display = 'none';
        }

        // Update stats (animated)
        animateCurrencyEl('bm-total-revenue', data.total_revenue);
        document.getElementById('bm-employee-count').textContent = data.employees.length;
        document.getElementById('bm-upgrade-count').textContent = Object.keys(data.upgrades).reduce((sum, key) => sum + (data.upgrades[key] > 0 ? 1 : 0), 0);

        // revenue rate - animate then append suffix
        const revEl = document.getElementById('bm-revenue-rate');
        if (revEl) {
            const start = parseInt(revEl.textContent.replace(/[^0-9]/g, '')) || 0;
            animateNumber(revEl, start, data.revenue_rate, 900, (v) => '$' + v.toLocaleString() + '/hour');
        }

        // accumulated revenue
        animateCurrencyEl('bm-accumulated-revenue', data.accumulated_revenue);

        // Enable/disable collect button with micro-interaction
        const collectBtn = document.getElementById('collect-revenue-btn');
        if (data.accumulated_revenue > 0) {
            collectBtn.disabled = false;
            collectBtn.classList.add('pulse');
        } else {
            collectBtn.disabled = true;
            collectBtn.classList.remove('pulse');
        }

        // Display current employees
        const employeeList = document.getElementById('current-employees');
        if (data.employees.length === 0) {
            employeeList.innerHTML = '<p style="color: #999;">No employees hired yet</p>';
        } else {
            employeeList.innerHTML = data.employees.map(emp => `
                <div class="employee-card">
                    <div class="employee-info">
                        <div class="employee-role">${emp.role}</div>
                        <div class="employee-skill">${emp.skill.charAt(0).toUpperCase() + emp.skill.slice(1)}</div>
                        <div class="employee-multiplier">${emp.multiplier}x multiplier</div>
                    </div>
                    <div class="employee-date">Hired: ${new Date(emp.hired_at).toLocaleDateString()}</div>
                </div>
            `).join('');
        }

        // Display available hires
        const hiresGrid = document.getElementById('available-hires');
        if (data.available_hires.length === 0) {
            hiresGrid.innerHTML = '<p style="color: #999;">All employees hired!</p>';
        } else {
            // Group by role
            const roles = ['Marketing', 'Operations', 'Finance', 'Tech'];
            hiresGrid.innerHTML = roles.map(role => {
                const roleHires = data.available_hires.filter(h => h.role === role);
                if (roleHires.length === 0) return '';

                return `
                    <div class="hire-role-section">
                        <h4>${role}</h4>
                        <div class="hire-cards">
                            ${roleHires.map(hire => `
                                <div class="hire-card">
                                    <div class="hire-skill">${hire.skill.charAt(0).toUpperCase() + hire.skill.slice(1)}</div>
                                    <div class="hire-cost">$${hire.cost.toLocaleString()}</div>
                                    <div class="hire-multiplier">${hire.multiplier}x multiplier</div>
                                    <button onclick="hireEmployee('${hire.role}', '${hire.skill}', ${hire.cost})" class="btn btn-primary">Hire</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Display available upgrades
        const upgradesGrid = document.getElementById('business-upgrades');
        if (data.available_upgrades.length === 0) {
            upgradesGrid.innerHTML = '<p style="color: #999;">All upgrades purchased!</p>';
        } else {
            upgradesGrid.innerHTML = data.available_upgrades.map(upgrade => `
                <div class="upgrade-card">
                    <div class="upgrade-header">
                        <div class="upgrade-name">${upgrade.name}</div>
                        <div class="upgrade-tier">Tier ${upgrade.tier}</div>
                    </div>
                    <div class="upgrade-description">${upgrade.description}</div>
                    <div class="upgrade-tier-name">${upgrade.tier_name}</div>
                    <div class="upgrade-effect">+${(upgrade.effect * 100).toFixed(0)}% revenue</div>
                    <div class="upgrade-cost">$${upgrade.cost.toLocaleString()}</div>
                    <button onclick="purchaseUpgrade('${upgrade.category}', ${upgrade.tier}, ${upgrade.cost})" class="btn btn-success">Purchase</button>
                </div>
            `).join('');
        }

        // Display current upgrades (show purchased tiers)
        const currentUpgrades = Object.entries(data.upgrades).filter(([_, tier]) => tier > 0);
        if (currentUpgrades.length > 0) {
            const upgradesSummary = currentUpgrades.map(([category, tier]) => 
                `<span class="upgrade-badge">${category}: Tier ${tier}</span>`
            ).join(' ');

            // Add after upgrades grid
            if (!document.getElementById('current-upgrades-summary')) {
                const summary = document.createElement('div');
                summary.id = 'current-upgrades-summary';
                summary.className = 'current-upgrades';
                summary.innerHTML = `<h4>Active Upgrades:</h4><div>${upgradesSummary}</div>`;
                upgradesGrid.parentElement.insertBefore(summary, upgradesGrid);
            } else {
                document.querySelector('#current-upgrades-summary div').innerHTML = upgradesSummary;
            }
        }

    } catch (error) {
        console.error('Error loading business mode:', error);
    }
}

async function hireEmployee(role, skill, cost) {
    if (!confirm(`Hire ${skill.charAt(0).toUpperCase() + skill.slice(1)} ${role} for $${cost.toLocaleString()}?`)) {
        return;
    }
    
    try {
            const response = await fetch('/api/business_mode/hire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, skill, business_id: (window.focusBusiness && window.focusBusiness.id) || null })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
            loadBusinessMode((window.focusBusiness && window.focusBusiness.id) || null, (window.focusBusiness && window.focusBusiness.name) || '');
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error hiring employee');
    }
}

async function purchaseUpgrade(category, tier, cost) {
    if (!confirm(`Purchase this upgrade for $${cost.toLocaleString()}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/business_mode/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, tier, business_id: (window.focusBusiness && window.focusBusiness.id) || null })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`✅ ${data.message}`);
            updateStats();
            loadBusinessMode((window.focusBusiness && window.focusBusiness.id) || null, (window.focusBusiness && window.focusBusiness.name) || '');
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error purchasing upgrade');
    }
}

async function collectBusinessRevenue() {
    try {
        const response = await fetch('/api/business_mode/collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: (window.focusBusiness && window.focusBusiness.id) || null })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showModal(`💰 Collected ${data.message.split('$')[1]}!`);
            updateStats();
            loadBusinessMode();
        } else {
            showModal('❌ ' + data.error);
        }
    } catch (error) {
        showModal('❌ Error collecting revenue');
    }
}

// Mobile helpers: toggle and setup UI for small screens
function toggleMobileStats() {
    const stats = document.querySelector('.header-stats');
    if (!stats) return;
    if (stats.style.display === 'flex') {
        stats.style.display = 'none';
        localStorage.setItem('mobileStatsVisible', '0');
    } else {
        stats.style.display = 'flex';
        localStorage.setItem('mobileStatsVisible', '1');
    }
}

function setupMobileUI() {
    const isMobile = window.innerWidth <= 768;
    const mobileHeader = document.getElementById('mobile-header');
    const mobileNav = document.querySelector('.mobile-nav');
    if (mobileHeader) mobileHeader.style.display = isMobile ? 'flex' : 'none';
    if (mobileNav) mobileNav.style.display = isMobile ? 'flex' : 'none';

    const stats = document.querySelector('.header-stats');
    if (stats) {
        if (isMobile) {
            const visible = localStorage.getItem('mobileStatsVisible');
            stats.style.display = visible === '1' ? 'flex' : 'none';
        } else {
            stats.style.display = 'flex';
        }
    }
}

window.addEventListener('resize', setupMobileUI);

// Ensure mobile UI is initialized on page load
try { setupMobileUI(); } catch (e) { /* ignore in case of early load */ }

// ==================== INITIALIZATION ====================

// Update stats every 5 seconds
setInterval(updateStats, 5000);

// Initial load
updateStats();
loadDashboard();
loadNotifications();
loadBusinessIndustries(); // Load business categories data
loadIllegalBusinessCategories(); // Load illegal business categories data
try { setupFeedbackWidget(); } catch (e) { /* ignore */ }

// Close modal on background click
document.getElementById('message-modal').addEventListener('click', (e) => {
    if (e.target.id === 'message-modal') {
        closeModal();
    }
});
