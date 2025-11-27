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

**Login URL**: http://localhost:3000/login.html

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
2. ✅ Login with admin credentials above
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
pkill -f "python3.*main.py"
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
ps aux | grep -E "(uvicorn|python3.*main.py|http.server)"

# Check ports
lsof -i :8001 -i :3000
```
