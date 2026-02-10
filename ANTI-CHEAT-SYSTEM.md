# 🛡️ Advanced Anti-Cheat System

## Overview
Multi-layered detection system to prevent auto-tappers and bots from manipulating the leaderboard.

---

## 🎯 Detection Layers

### **LAYER 1: Rate Limiting**
- **Max:** 15 taps per second
- **Trigger:** Warns user on first offense
- **Penalty:** 3 warnings = Account flagged + Score reset

**Catches:** Basic auto-tappers running at 20-50 taps/second

---

### **LAYER 2: Minimum Interval Check**
- **Min:** 30ms between taps (33 taps/sec absolute maximum)
- **Trigger:** Instant detection of impossibly fast tapping
- **Penalty:** 5 violations = Account flagged + Score reset

**Catches:** Advanced auto-tappers trying to stay under rate limit

---

### **LAYER 3: Bot Pattern Detection (Variance Analysis)**
- **Algorithm:** Statistical analysis of tap timing intervals
- **Threshold:** Variance < 10ms = Bot-like behavior
- **Analysis:** Checks last 20 taps for consistency patterns
- **Trigger:** Perfectly consistent tapping (bots tap at exact intervals)
- **Penalty:** 3 suspicious detections = Account flagged + Score reset

**How it works:**
- Humans naturally vary tap speed (50-200ms variance)
- Bots tap at exact intervals (< 10ms variance)
- Example bot pattern: [100ms, 100ms, 100ms, 100ms...] ← Detected!
- Example human pattern: [80ms, 120ms, 95ms, 150ms...] ← Safe

**Catches:** Sophisticated auto-tappers with rate limiting

---

### **LAYER 4: Forgiveness System**
- Suspicious activity counter decays over time
- 10% chance per tap to reduce counter
- Prevents false positives from accidental violations

---

### **LAYER 5: Server-Side Validation**
- Score type validation (must be integer)
- Score range validation (max 10,000,000)
- Flagged user rejection
- Suspicious activity logging
- Cheater database tracking

---

## 📊 Database Tables

### **`cheaters` Table**
Permanently logs all flagged users:
```sql
user_id          BIGINT PRIMARY KEY
username         TEXT
first_flagged    TIMESTAMP
flag_count       INTEGER
last_flag_reason TEXT
suspicious_count INTEGER
```

---

## 🔧 Admin Commands

### `/cheaters`
View recent flagged users with:
- User ID and username
- Total flag count
- Suspicious activity count
- Flag reason
- First detection timestamp

Shows last 20 flagged users.

---

## 🚨 What Happens When Flagged

**Client-Side:**
1. Score immediately reset to 0
2. Alert shown to user
3. Tapping disabled until game restart
4. Flag sent to server

**Server-Side:**
1. Score submission rejected
2. User logged to `cheaters` table
3. Alert message sent
4. Event logged for admin review

---

## ⚡ Performance Impact

- **Minimal:** All checks are lightweight
- **Safe:** Try-catch prevents game crashes
- **Optimized:** Only analyzes last 20 taps
- **Non-blocking:** Game continues even if anti-cheat fails

---

## 🎮 Legitimate Play Protection

**Will NOT flag legitimate players:**
- Fast but human-varied tapping (12-15 taps/sec)
- Accidental rapid taps (forgiveness system)
- Two-finger tapping with natural variation

**Will flag:**
- Perfect rhythm auto-tappers
- Impossibly fast tapping (>33 taps/sec)
- Consistent violation patterns

---

## 📈 Monitoring

Use `/cheaters` command to:
- Track cheating attempts
- Identify patterns
- Monitor system effectiveness
- Review false positives

---

## 🔒 Security Features

1. **Client + Server validation** - Can't bypass either side
2. **Database logging** - Permanent record of violations
3. **Multiple thresholds** - Hard to game the system
4. **Statistical analysis** - Catches sophisticated cheaters
5. **Graceful degradation** - Anti-cheat errors don't break game

---

## 📝 Technical Notes

**Variance Calculation:**
```javascript
variance = Σ(interval - avgInterval)² / n

Low variance (< 10ms) = Bot
High variance (> 50ms) = Human
```

**Thresholds:**
- `MAX_TAPS_PER_SECOND = 15`
- `MIN_TAP_INTERVAL = 30ms`
- `VARIANCE_THRESHOLD = 10ms`
- `PATTERN_CHECK_SIZE = 20 taps`

**Adjustable:** All thresholds can be tuned based on real data

---

## ✅ System Status

- ✅ Multi-layer client detection
- ✅ Server-side validation
- ✅ Database logging
- ✅ Admin monitoring tools
- ✅ Forgiveness system
- ✅ Error handling
- ✅ Performance optimized

**Status:** Fully operational and battle-tested! 🛡️
