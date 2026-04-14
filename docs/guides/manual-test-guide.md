# Manual Testing Environment - Active Services

## 🟢 All Services Running

### Backend API
- **URL**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Status**: ✅ Running
- **Database**: SQLite (manual_test.db)
- **Process ID**: Check `backend_manual_test.pid`

### Telegram Bot
- **Status**: ✅ Running (Polling Mode)
- **Backend Connection**: http://localhost:8001
- **Process ID**: Check `bot_manual_test.pid`
- **Log File**: `bot_manual_test.log`

### Dashboard (Frontend)
- **Login URL**: http://localhost:3000/login.html
- **Dashboard URL**: http://localhost:3000/index.html
- **Status**: ✅ Running
- **Process ID**: Check `dashboard_manual_test.pid`

---

## 🔑 Admin Credentials

**Email**: `admin@test.local`  
**Password**: `admin123`  
**Role**: `admin` ✅

**Login URL**: http://localhost:3000/login.html

> **Note**: The admin account has been created and the role has been fixed to "admin". You should now be able to log in successfully!

---

## 📋 Testing Checklist

### Bot Testing (via Telegram)
1. ✅ Open your Telegram app
2. ✅ Search for your bot
3. ✅ Send `/start` to begin
4. ✅ Send `/report` to create a complaint
5. ✅ Test the full flow:
   - Select hostel
   - Enter room number (format: A101, B202, etc.)
   - Select category
   - Enter description (10-500 chars)
   - Select severity
   - Upload photos (optional)
6. ✅ Send `/mycomplaints` to view your complaints
7. ✅ Send `/status` to check complaint status

### Dashboard Testing
1. ✅ Open http://localhost:3000/login.html
2. ✅ Login with credentials:
   - Email: `admin@test.local`
   - Password: `admin123`
3. ✅ Verify real-time updates:
   - New complaints appear instantly
   - Images load correctly
   - Categories display properly
   - Status changes reflect immediately
4. ✅ Test admin actions:
   - Update complaint status
   - Assign complaints to porters
   - View complaint details
   - Filter by status/category

### Real-Time Verification
- ✅ Submit complaint via bot
- ✅ Check dashboard updates immediately (WebSocket)
- ✅ Update status in dashboard
- ✅ Verify bot shows updated status

---

## 🛑 Stopping Services

When testing is complete, run:

```bash
# Stop backend
kill $(cat backend_manual_test.pid)

# Stop bot
kill $(cat bot_manual_test.pid)

# Stop dashboard
kill $(cat dashboard_manual_test.pid)

# Or stop all at once
pkill -f "uvicorn app.main:app"
pkill -f "python3.*src.bot.main"
pkill -f "http.server 3000"
```

---

## 📊 Service Logs

- **Backend**: `backend_manual_test.log`
- **Bot**: `bot_manual_test.log`
- **Dashboard**: `dashboard_manual_test.log`

Monitor logs in real-time:
```bash
tail -f backend_manual_test.log
tail -f bot_manual_test.log
```

---

## 🔍 Health Checks

```bash
# Backend health
curl http://localhost:8001/docs

# Dashboard health
curl http://localhost:3000/login.html

# Check running processes
ps aux | grep -E "(uvicorn|python3.*src.bot.main|http.server)"

# Check ports
lsof -i :8001 -i :3000

# Test login API
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.local&password=admin123"
```

---

## 🔧 Troubleshooting

### Login Issues
If login fails:
1. Check backend is running: `curl http://localhost:8001/docs`
2. Verify admin role: Run the curl command in Health Checks section
3. Check browser console for errors (F12)
4. Clear browser cache and sessionStorage

### Bot Not Responding
1. Check bot log: `tail -f bot_manual_test.log`
2. Verify TELEGRAM_BOT_TOKEN is set in `.env`
3. Ensure backend is accessible: `curl http://localhost:8001/docs`

### Dashboard Not Loading
1. Check dashboard is serving: `curl http://localhost:3000/login.html`
2. Verify port 3000 is not blocked
3. Check browser console for CORS errors

### Real-Time Updates Not Working
1. Check WebSocket connection in browser DevTools (Network tab)
2. Verify backend WebSocket endpoint: `ws://localhost:8001/ws/dashboard`
3. Check backend logs for WebSocket errors
