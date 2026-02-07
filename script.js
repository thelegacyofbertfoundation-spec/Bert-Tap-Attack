/**
 * Turbo Tapper - Core Game Logic
 * Handles Tapping, Energy, Upgrades, and Telegram Integration
 */

const tg = window.Telegram.WebApp;

// --- 1. GAME STATE ---
let score = 0;
let energy = 1000;
let maxEnergy = 1000;
let tapPower = 1;
let tapLevel = 1;
let energyLevel = 1;

// --- 2. UI ELEMENTS ---
const scoreEl = document.getElementById('score');
const energyBar = document.getElementById('energy-bar');
const energyVal = document.getElementById('energy-val');
const energyMaxEl = document.getElementById('energy-max');
const powerValEl = document.getElementById('power-val');
const levelValEl = document.getElementById('level-val');
const coinWrapper = document.getElementById('coin-wrapper');
const shop = document.getElementById('shop-container');

// --- 3. INITIALIZATION ---
function init() {
    tg.expand(); // Make the app full screen
    tg.enableClosingConfirmation(); // Ask before closing
    updateUI();
    startRegeneration();
}

// --- 4. MAIN TAP LOGIC ---
coinWrapper.addEventListener('touchstart', (e) => {
    e.preventDefault(); // Stop zoom/scroll
    
    // Support for multi-finger tapping
    for (let i = 0; i < e.targetTouches.length; i++) {
        if (energy >= tapPower) {
            score += tapPower;
            energy -= tapPower;
            
            // Physical vibration & Visual feedback
            tg.HapticFeedback.impactOccurred('light');
            createParticle(e.targetTouches[i].clientX, e.targetTouches[i].clientY);
        } else {
            // Out of energy feedback
            tg.HapticFeedback.notificationOccurred('error');
            break; 
        }
    }
    updateUI();
});

// Floating +1 number effect
function createParticle(x, y) {
    const p = document.createElement('div');
    p.innerText = `+${tapPower}`;
    p.className = 'particle';
    p.style.left = `${x - 15}px`;
    p.style.top = `${y - 30}px`;
    document.body.appendChild(p);
    
    // Remove from DOM after animation finishes
    setTimeout(() => p.remove(), 700);
}

// --- 5. SHOP & UPGRADES ---
function toggleShop() {
    shop.classList.toggle('open');
    tg.HapticFeedback.impactOccurred('medium');
}

function buyUpgrade(type) {
    if (type === 'tap') {
        let cost = Math.floor(100 * Math.pow(1.6, tapLevel - 1));
        if (score >= cost) {
            score -= cost;
            tapLevel++;
            tapPower++;
            tg.HapticFeedback.notificationOccurred('success');
        }
    } else if (type === 'energy') {
        let cost = Math.floor(200 * Math.pow(1.5, energyLevel - 1));
        if (score >= cost) {
            score -= cost;
            energyLevel++;
            maxEnergy += 500;
            energy = maxEnergy; // Refill on upgrade
            tg.HapticFeedback.notificationOccurred('success');
        }
    }
    updateUI();
}

// --- 6. REGENERATION ---
function startRegeneration() {
    setInterval(() => {
        if (energy < maxEnergy) {
            energy = Math.min(energy + 2, maxEnergy);
            updateUI();
        }
    }, 1000); // Refills every 1 second
}

// --- 7. VIRAL SHARE LOGIC ---
function shareGame() {
    const botUsername = "YOUR_BOT_USERNAME"; // Change this!
    const inviteLink = `https://t.me/${botUsername}?start=ref_${tg.initDataUnsafe.user?.id || 'newuser'}`;
    const shareText = "🚀 Tap with me on Turbo Tapper and earn rewards!";
    
    // Open Telegram's native share dialog
    tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(shareText)}`);
    
    // Referral incentive
    score += 10000;
    updateUI();
}

// --- 8. UI SYNC ---
function updateUI() {
    // Numbers
    scoreEl.innerText = score.toLocaleString();
    energyVal.innerText = Math.floor(energy);
    energyMaxEl.innerText = maxEnergy;
    powerValEl.innerText = tapPower;
    levelValEl.innerText = tapLevel;

    // Energy Bar Visuals
    const percentage = (energy / maxEnergy) * 100;
    energyBar.style.width = percentage + "%";
    
    // Color warning for low energy
    if (energy < (maxEnergy * 0.2)) {
        energyBar.style.background = "#e74c3c"; // Red
    } else {
        energyBar.style.background = "linear-gradient(90deg, #f1c40f, #f39c12)"; // Gold
    }

    // Dynamic Shop Costs
    const nextTapCost = Math.floor(100 * Math.pow(1.6, tapLevel - 1));
    const nextEnergyCost = Math.floor(200 * Math.pow(1.5, energyLevel - 1));
    
    document.getElementById('tap-cost-text').innerText = `Cost: ${nextTapCost.toLocaleString()}`;
    document.getElementById('energy-cost-text').innerText = `Cost: ${nextEnergyCost.toLocaleString()}`;
    
    // Enable/Disable buttons based on balance
    document.getElementById('buy-tap').disabled = score < nextTapCost;
    document.getElementById('buy-energy').disabled = score < nextEnergyCost;
}

// Run the game
init();
