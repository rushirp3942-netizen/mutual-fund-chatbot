// Mutual Fund Assistant - Frontend JavaScript
// Configure your API backend URL here
// For local testing: 'http://localhost:5000'
// For Render deployment: 'https://your-app.onrender.com'
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : 'https://your-api-backend.onrender.com';

// Fund data (embedded for static deployment)
const FUNDS_DATA = [
    {
        "fund_name": "Bandhan Small Cap Fund Direct Growth",
        "category": "Equity Small Cap",
        "amc": "Bandhan Mutual Fund",
        "nav": "₹102.45",
        "expense_ratio": "0.49%",
        "risk_level": "Very High",
        "minimum_sip": "₹100",
        "benchmark": "Nifty Smallcap 250 Index"
    },
    {
        "fund_name": "Parag Parikh Flexi Cap Fund Direct Growth",
        "category": "ELSS",
        "amc": "Parag Parikh Mutual Fund",
        "nav": "₹91.59",
        "expense_ratio": "0.63%",
        "risk_level": "Very High",
        "minimum_sip": "₹1,000",
        "benchmark": "NIFTY 500 Total Return Index"
    },
    {
        "fund_name": "HDFC Mid Cap Fund Direct Growth",
        "category": "Equity Mid Cap",
        "amc": "HDFC Mutual Fund",
        "nav": "₹217.05",
        "expense_ratio": "0.76%",
        "risk_level": "Very High",
        "minimum_sip": "₹100",
        "benchmark": "NIFTY Midcap 150 Total Return Index"
    },
    {
        "fund_name": "Nippon India Small Cap Fund Direct Growth",
        "category": "Equity Small Cap",
        "amc": "Nippon India Mutual Fund",
        "nav": "₹150.23",
        "expense_ratio": "0.78%",
        "risk_level": "Very High",
        "minimum_sip": "₹100",
        "benchmark": "Nifty Smallcap 250 Index"
    },
    {
        "fund_name": "ICICI Prudential Large Cap Fund Direct Growth",
        "category": "Equity Large Cap",
        "amc": "ICICI Prudential Mutual Fund",
        "nav": "₹85.67",
        "expense_ratio": "1.05%",
        "risk_level": "High",
        "minimum_sip": "₹100",
        "benchmark": "NIFTY 100 Total Return Index"
    },
    {
        "fund_name": "Tata Small Cap Fund Direct Growth",
        "category": "Equity Small Cap",
        "amc": "Tata Mutual Fund",
        "nav": "₹45.32",
        "expense_ratio": "0.42%",
        "risk_level": "Very High",
        "minimum_sip": "₹150",
        "benchmark": "Nifty Smallcap 250 Index"
    },
    {
        "fund_name": "Axis Small Cap Fund Direct Growth",
        "category": "Equity Small Cap",
        "amc": "Axis Mutual Fund",
        "nav": "₹115.86",
        "expense_ratio": "0.46%",
        "risk_level": "Very High",
        "minimum_sip": "₹100",
        "benchmark": "Nifty Smallcap 250 Index"
    },
    {
        "fund_name": "SBI Small Cap Fund Direct Growth",
        "category": "Equity Small Cap",
        "amc": "SBI Mutual Fund",
        "nav": "₹130.45",
        "expense_ratio": "0.77%",
        "risk_level": "Very High",
        "minimum_sip": "₹500",
        "benchmark": "Nifty Smallcap 250 Index"
    },
    {
        "fund_name": "SBI ELSS Tax Saver Fund Direct Growth",
        "category": "ELSS",
        "amc": "SBI Mutual Fund",
        "nav": "₹95.78",
        "expense_ratio": "0.92%",
        "risk_level": "Very High",
        "minimum_sip": "₹500",
        "benchmark": "Nifty 500 Total Return Index"
    }
];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set welcome time
    document.getElementById('welcome-time').textContent = formatTime(new Date());
    
    // Setup navigation
    setupNavigation();
    
    // Setup chat input
    setupChatInput();
    
    // Load funds
    loadFunds();
});

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            
            // Update active nav
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show page
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`${page}-page`).classList.add('active');
        });
    });
}

// Chat functionality
function setupChatInput() {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Try to call API backend first
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (response.ok) {
            const data = await response.json();
            hideTypingIndicator();
            addMessage(data.message.content, 'assistant', data.sources || []);
        } else {
            // Fallback to local response
            throw new Error('API failed');
        }
    } catch (error) {
        // Use local fallback response
        console.log('API unavailable, using local fallback:', error);
        setTimeout(() => {
            const response = getBotResponse(message);
            hideTypingIndicator();
            addMessage(response.content, 'assistant', response.sources);
        }, 500);
    }
}

function sendSuggestion(text) {
    document.getElementById('message-input').value = text;
    sendMessage();
}

function addMessage(content, role, sources = []) {
    const messagesArea = document.getElementById('messages-area');
    const time = formatTime(new Date());
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = role === 'user' ? 'You' : 'AI';
    const avatarClass = role === 'user' ? 'user-avatar' : 'assistant-avatar';
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `<div style="margin-top: 8px; font-size: 0.8rem; opacity: 0.8;">Source: `;
        sources.forEach((source, index) => {
            const displayName = source.fund_name || `Source ${index + 1}`;
            sourcesHtml += `<a href="${source.source_url}" target="_blank" style="color: inherit; text-decoration: underline; font-weight: 500;">${displayName}</a>`;
        });
        sourcesHtml += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar ${avatarClass}">${avatar}</div>
        <div class="message-content">
            <div class="message-bubble">
                ${content}
                ${sourcesHtml}
            </div>
            <span class="message-time">${time}</span>
        </div>
    `;
    
    messagesArea.appendChild(messageDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function showTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'flex';
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'none';
}

// Bot response logic (same as backend fallback)
function getBotResponse(message) {
    const messageLower = message.toLowerCase();
    
    // Check for investment advice
    if (messageLower.includes('should i invest') || 
        messageLower.includes('recommend') || 
        messageLower.includes('should i buy') || 
        messageLower.includes('good investment')) {
        return {
            content: "I can't provide investment advice or recommendations. I'm designed to share factual information about mutual funds in my knowledge base.\n\nI can tell you about:\n• Expense ratios and fees\n• Risk levels and benchmarks\n• Minimum investment amounts\n• Fund categories and types\n\nFor investment advice, please consult a SEBI-registered investment advisor.",
            sources: []
        };
    }
    
    // Identify fund
    const fund = identifyFund(message);
    
    if (fund) {
        const queryType = identifyQueryType(message);
        return getFundResponse(fund, queryType);
    }
    
    // General question
    return {
        content: getAllFundsSummary(),
        sources: []
    };
}

function identifyFund(query) {
    const queryLower = query.toLowerCase();
    
    for (const fund of FUNDS_DATA) {
        const fundName = fund.fund_name.toLowerCase();
        const shortName = fundName.replace(' direct growth', '');
        
        if (fundName.includes(queryLower) || shortName.includes(queryLower)) {
            return fund;
        }
        
        // Check key parts
        const parts = shortName.split(' ');
        let matches = 0;
        for (const part of parts) {
            if (part.length > 2 && queryLower.includes(part)) {
                matches++;
            }
        }
        if (matches >= 2) {
            return fund;
        }
    }
    
    return null;
}

function identifyQueryType(query) {
    const queryLower = query.toLowerCase();
    
    if (queryLower.includes('expense ratio') || queryLower.includes('expense') || queryLower.includes('cost')) {
        return 'expense_ratio';
    }
    if (queryLower.includes('exit load') || queryLower.includes('exit') || queryLower.includes('redemption')) {
        return 'exit_load';
    }
    if (queryLower.includes('minimum sip') || queryLower.includes('min sip') || queryLower.includes('sip amount')) {
        return 'minimum_sip';
    }
    if (queryLower.includes('lock-in') || queryLower.includes('lock in') || queryLower.includes('locking period')) {
        return 'lock_in';
    }
    if (queryLower.includes('risk') || queryLower.includes('riskometer') || queryLower.includes('risk level')) {
        return 'risk_level';
    }
    if (queryLower.includes('benchmark') || queryLower.includes('index')) {
        return 'benchmark';
    }
    if (queryLower.includes('download') || queryLower.includes('statement') || queryLower.includes('how to get')) {
        return 'download';
    }
    
    return 'general';
}

function getFundResponse(fund, queryType) {
    const fundName = fund.fund_name;
    const source = {
        id: '1',
        fund_name: fundName.replace(' Direct Growth', ''),
        source_url: `https://groww.in/mutual-funds/${fundName.toLowerCase().replace(/ /g, '-')}`
    };
    
    let content;
    switch (queryType) {
        case 'expense_ratio':
            content = `The expense ratio of ${fundName} is ${fund.expense_ratio}.`;
            break;
        case 'exit_load':
            content = `The exit load for ${fundName} is: ${fund.exit_load || 'No exit load'}`;
            break;
        case 'minimum_sip':
            content = `The minimum SIP amount for ${fundName} is ${fund.minimum_sip}.`;
            break;
        case 'lock_in':
            if (fund.category === 'ELSS') {
                content = `${fundName} has a lock-in period of 3 years, as required for ELSS tax-saving funds under Section 80C.`;
            } else {
                content = `${fundName} has no lock-in period.`;
            }
            break;
        case 'risk_level':
            content = `${fundName} has a risk level of '${fund.risk_level}' according to the Riskometer.`;
            break;
        case 'benchmark':
            content = `The benchmark for ${fundName} is ${fund.benchmark}.`;
            break;
        case 'download':
            content = "You can download your mutual fund statement through the following methods:\n\n" +
                     "**Through the AMC Website**\n" +
                     "Visit the Asset Management Company (AMC) website where you invested, log in to your account, and download your account statement from the portfolio or statement section.\n\n" +
                     "**Through Registrar Websites (CAMS or KFintech)**\n" +
                     "If your fund is serviced by a registrar such as CAMS or KFintech, you can request a consolidated account statement by entering your registered email ID and PAN.\n\n" +
                     "**Through Your Investment Platform**\n" +
                     "If you invested using a platform such as a broker or investment app, you can download the statement from the portfolio or reports section of that platform.\n\n" +
                     "Statements are usually available in PDF format and include details such as transactions, holdings, and NAV history.";
            return { content, sources: [] };
        default:
            content = `Here is the information for ${fundName}:\n\n` +
                     `• NAV: ${fund.nav}\n` +
                     `• Expense Ratio: ${fund.expense_ratio}\n` +
                     `• Risk Level: ${fund.risk_level}\n` +
                     `• Minimum SIP: ${fund.minimum_sip}\n` +
                     `• Category: ${fund.category}\n` +
                     `• Benchmark: ${fund.benchmark}`;
    }
    
    return { content, sources: [source] };
}

function getAllFundsSummary() {
    const fundList = FUNDS_DATA.map(f => `• ${f.fund_name}`).join('\n');
    return `I have information about ${FUNDS_DATA.length} mutual funds:\n\n${fundList}\n\nYou can ask me about:\n• Expense ratios\n• Exit loads\n• Minimum SIP amounts\n• Lock-in periods\n• Risk levels\n• Benchmark indices\n\nWhat would you like to know?`;
}

// Funds page functionality
function loadFunds() {
    const grid = document.getElementById('funds-grid');
    grid.innerHTML = '';
    
    FUNDS_DATA.forEach(fund => {
        const card = createFundCard(fund);
        grid.appendChild(card);
    });
}

function createFundCard(fund) {
    const card = document.createElement('div');
    card.className = 'fund-card';
    card.dataset.name = fund.fund_name.toLowerCase();
    
    card.innerHTML = `
        <h3>${fund.fund_name}</h3>
        <span class="category">${fund.category}</span>
        <div class="fund-metrics">
            <div class="fund-metric">
                <div class="fund-metric-label">NAV</div>
                <div class="fund-metric-value">${fund.nav}</div>
            </div>
            <div class="fund-metric">
                <div class="fund-metric-label">Expense Ratio</div>
                <div class="fund-metric-value">${fund.expense_ratio}</div>
            </div>
            <div class="fund-metric">
                <div class="fund-metric-label">Risk</div>
                <div class="fund-metric-value">${fund.risk_level}</div>
            </div>
            <div class="fund-metric">
                <div class="fund-metric-label">Min SIP</div>
                <div class="fund-metric-value">${fund.minimum_sip}</div>
            </div>
        </div>
        <button class="view-details-btn" onclick="viewFundDetails('${fund.fund_name}')">View Details</button>
    `;
    
    return card;
}

function filterFunds() {
    const searchTerm = document.getElementById('fund-search').value.toLowerCase();
    const cards = document.querySelectorAll('.fund-card');
    
    cards.forEach(card => {
        const name = card.dataset.name;
        if (name.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function viewFundDetails(fundName) {
    const fund = FUNDS_DATA.find(f => f.fund_name === fundName);
    if (!fund) return;
    
    // Switch to chat and ask about this fund
    document.querySelector('[data-page="chat"]').click();
    document.getElementById('message-input').value = `Tell me about ${fund.fund_name}`;
    sendMessage();
}

// Utility functions
function formatTime(date) {
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}
