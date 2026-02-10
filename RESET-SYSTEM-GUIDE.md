# 🔄 Complete Reset System

## How to Reset Everyone's Scores AND Boost Levels

You now have a complete reset system with TWO parts:

---

## PART 1: Reset Leaderboard Scores (Bot Command)

### Use `/reset_all` command:

1. **Make sure your user ID is in bot.py (line ~283):**
   ```python
   ADMIN_USER_IDS = [7137489161]  # Your Telegram user ID
   ```

2. **Deploy bot.py to Render**

3. **Send `/reset_all` to your bot**

**Result:**
- ✅ All scores in leaderboard reset to 0
- ✅ Database cleared
- ✅ Instant effect

---

## PART 2: Reset Everyone's Boost Levels (Version System)

### Change the GAME_VERSION number:

1. **Open index.html (line 129)**

2. **Change the version number:**
   ```javascript
   const GAME_VERSION = 2; // Increment this to 3, 4, 5, etc.
   ```

3. **Deploy index.html to GitHub Pages**

**Result:**
- ✅ Next time ANYONE opens the game, their boosts reset to Level 1
- ✅ Their score stays safe
- ✅ They see: "🔄 Game Updated! Your boost levels have been reset. Your score is safe!"

---

## 🎯 COMPLETE RESET PROCEDURE

To completely reset the game for everyone:

**Step 1:** Send `/reset_all` to bot
```
✅ All Scores Reset

Reset 47 player(s) to 0 points.
```

**Step 2:** Change GAME_VERSION in index.html
```javascript
const GAME_VERSION = 3; // Changed from 2
```

**Step 3:** Deploy index.html to GitHub Pages

**Step 4:** Done! Next time players open:
- Scores: 0
- Boost levels: Reset to 1
- Energy: Full
- Fresh start! 🎮

---

## 📋 Version System Details

### How It Works:

1. **Every player has a version number stored** in Telegram Cloud Storage
2. **When they open the game**, it checks:
   - Their stored version vs current GAME_VERSION
3. **If different:**
   - Reset boost levels to 1
   - Keep their score (unless you used /reset_all)
   - Save new version number
   - Show alert

### Version History Tracking:

You can use version numbers to track major changes:
- `GAME_VERSION = 1` - Initial release
- `GAME_VERSION = 2` - First reset
- `GAME_VERSION = 3` - Second reset
- etc.

---

## ⚠️ Important Notes

### Scores:
- **Database-side**: Use `/reset_all` bot command
- Resets everyone instantly
- Permanent (no undo)

### Boost Levels:
- **Client-side**: Change GAME_VERSION
- Resets when player opens game
- Gradual (as players reconnect)

### Both Together:
- Use both methods for complete fresh start
- Recommended for major game rebalancing
- Announce to players beforehand

---

## 🔒 Security

**Bot Command:**
- Only authorized user IDs can use `/reset_all`
- Unauthorized attempts are logged
- Add/remove admin IDs in bot.py

**Version System:**
- Only you can change GAME_VERSION
- Players can't bypass it
- Automatic enforcement

---

## 📊 Testing

Before resetting for everyone:

1. **Test on yourself first**
2. Check `/debug` to see database
3. Check `/cheaters` to see flagged users
4. Announce to players

---

## 🎮 Player Experience

**When you reset:**

**They see:**
```
🔄 Game Updated!

Your boost levels have been reset.
Your score is safe!
```

**What happens:**
- All boosts → Level 1
- Score → 0 (if you used /reset_all) OR kept
- Energy → Full
- Clean slate!

---

## 💡 Pro Tips

1. **Announce resets in advance** - Be transparent
2. **Reset during low activity** - Night/early morning
3. **Test with small version change first**
4. **Keep version numbers sequential** - Easier to track
5. **Document why you reset** - Future reference

---

## ✅ Quick Reference

| Action | Command | Effect |
|--------|---------|--------|
| **Reset all scores** | `/reset_all` | Leaderboard → 0 |
| **Reset boost levels** | Change `GAME_VERSION` | All players → Level 1 |
| **Complete reset** | Both above | Everything fresh |
| **View leaderboard** | `/leaderboard` | See current scores |
| **Check cheaters** | `/cheaters` | View flagged users |

---

## 🚀 Ready to Reset!

Your game now has a complete, professional reset system! 

Use it wisely and enjoy managing your game! 🎮
