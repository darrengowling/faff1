# UCL Auction Smoke Test Checklist

## 🎯 **Test Environment Setup**

### Prerequisites
- [ ] Application deployed and running
- [ ] All services healthy (check `/health` endpoint)
- [ ] Database initialized with seed data
- [ ] Email configuration working (check SMTP settings)
- [ ] Competition profiles seeded (UCL, Europa, Custom)

### Test Data Reset (if needed)
```bash
# Clear test data
docker-compose exec -T mongodb mongosh ucl_auction --eval "
  db.users.deleteMany({email: {$regex: '@smoketest\\.com$'}});
  db.leagues.deleteMany({name: {$regex: 'Smoke Test'}});
"

# Or run fresh seed data
./deploy.sh production backup
python3 seed_script.py
```

### API Contracts Verification
- [ ] Run API contracts test: `python test_api_contracts.py`
- [ ] Verify PATCH `/leagues/:id/settings` endpoint exists (status 403 not 404)
- [ ] Verify competition profiles have required fields (club_slots, budget_per_manager, league_size)
- [ ] Verify UCL defaults: 3 slots, 100M budget, 4-8 managers

---

## 📋 **SMOKE TEST EXECUTION**

## **TEST 1: League Creation & Competition Profile Defaults**

### 1.1 Create League with Default Settings (Commissioner)
- [ ] Navigate to application: `http://localhost:8000`
- [ ] Click "Login" and enter email: `commissioner.smoke@smoketest.com`
- [ ] Check email for magic link (or check logs: `docker-compose logs app | grep "Magic link"`)
- [ ] Click magic link and verify login
- [ ] Click "Create League"
- [ ] Fill minimal league details (no custom settings):
  ```
  Name: Default Settings League
  Season: 2025-26
  ```
- [ ] Submit and verify league created
- [ ] **EXPECTED**: League uses UCL competition profile defaults:
  - Budget: 100M per manager
  - Club Slots: 3 per manager  
  - League Size: 4-8 managers
  - Scoring: 1 goal, 3 win, 1 draw

### 1.2 Create League with Custom Settings (Commissioner)
- [ ] Create second league with custom settings:
  ```
  Name: Custom Settings League
  Season: 2025-26
  Budget: 150M
  Club Slots: 4
  Min Managers: 2
  Max Managers: 6
  ```
- [ ] Submit and verify custom settings override competition profile defaults
- [ ] **EXPECTED**: League uses explicit settings, not competition profile defaults

### 1.3 Test League Size Enforcement
- [ ] In Custom Settings League (max 6), try to invite 7 members
- [ ] **EXPECTED**: System prevents invites when at max capacity
- [ ] Try to start auction with only 1 manager (below min of 2)
- [ ] **EXPECTED**: "Start Auction" button disabled with warning message

### 1.2 Invite 3 Friends
- [ ] In league dashboard, click "Invite Members"
- [ ] Add emails:
  ```
  manager1.smoke@smoketest.com
  manager2.smoke@smoketest.com  
  manager3.smoke@smoketest.com
  ```
- [ ] Send invitations
- [ ] **EXPECTED**: 3 invitation emails sent (check logs)

### 1.3 Friends Join League
For each manager:
- [ ] Open new incognito window
- [ ] Navigate to application
- [ ] Login with manager email
- [ ] Check for league invitation or navigate to invite link
- [ ] Accept league invitation
- [ ] **EXPECTED**: All 4 members visible in league dashboard

### 1.4 Verify Access Control
- [ ] Open new incognito window
- [ ] Try to access league URL directly without login
- [ ] **EXPECTED**: Redirect to login page
- [ ] Login with unauthorized email: `outsider.smoke@smoketest.com`
- [ ] Try to access league data
- [ ] **EXPECTED**: 403 Forbidden or "Access Denied" message

---

## **TEST 2: Auction Management & Bidding**

### 2.1 Start Auction (Commissioner)
- [ ] Login as commissioner
- [ ] Go to league dashboard
- [ ] Click "Admin Panel"
- [ ] Click "Start Auction" 
- [ ] **EXPECTED**: Auction status changes to "Active"
- [ ] **EXPECTED**: Admin log entry created for "start_auction"

### 2.2 Join Auction Room
For all 4 members:
- [ ] Navigate to auction room
- [ ] Verify current lot displayed
- [ ] Check WebSocket connection (real-time updates working)
- [ ] **EXPECTED**: All members see same auction state

### 2.3 Place Simultaneous Bids
**Setup**: Have all 4 members ready to bid on same club
- [ ] Manager 1: Place bid of 5M
- [ ] Manager 2: Place bid of 6M (quickly after)
- [ ] Manager 3: Place bid of 7M (quickly after)
- [ ] Manager 4: Place bid of 8M (quickly after)
- [ ] **EXPECTED**: Only highest bid (8M) accepted
- [ ] **EXPECTED**: Other bids rejected with appropriate error messages
- [ ] **EXPECTED**: Real-time updates show current bid to all users

### 2.4 Anti-Snipe Trigger Test
- [ ] Wait for auction timer to reach < 30 seconds
- [ ] Place bid in last 10 seconds
- [ ] **EXPECTED**: Timer extends by additional time
- [ ] **EXPECTED**: Toast notification: "Timer Extended! Anti-snipe activated"
- [ ] **EXPECTED**: All users see timer extension in real-time

### 2.5 Club Sells
- [ ] Let timer run down to zero
- [ ] **EXPECTED**: Club marked as "SOLD" to highest bidder
- [ ] **EXPECTED**: Winner gets success toast: "Congratulations! You won [Club] for [Price]M"
- [ ] **EXPECTED**: Others get info toast: "[Winner] won [Club] for [Price]M"
- [ ] **EXPECTED**: Next lot starts automatically
- [ ] **EXPECTED**: Winner's budget reduced by bid amount

---

## **TEST 3: Budget Enforcement & Validation**

### 3.1 Fill Club Slots
For each manager, repeat auction process:
- [ ] Manager wins 1st club (budget: 100M → ~75M remaining)
- [ ] Manager wins 2nd club (budget: ~75M → ~50M remaining)  
- [ ] Manager wins 3rd club (budget: ~50M → ~25M remaining)
- [ ] **EXPECTED**: Each manager owns exactly 3 clubs
- [ ] **EXPECTED**: Budget constraints enforced at each step

### 3.2 Budget Constraint Validation
- [ ] Try to bid amount that would leave insufficient budget for remaining slots
- [ ] **EXPECTED**: Bid rejected with error: "Would leave insufficient budget for remaining slots"
- [ ] Try to bid more than remaining budget
- [ ] **EXPECTED**: Bid rejected with error: "Insufficient budget for this bid"

### 3.3 Duplicate Ownership Prevention
- [ ] Try to bid on club already owned by someone
- [ ] **EXPECTED**: Bid rejected or club marked as unavailable
- [ ] **EXPECTED**: No duplicate ownership in database

---

## **TEST 4: Match Results & Scoring**

### 4.1 POST Match Result
**API Call**:
```bash
curl -X POST http://localhost:8000/api/scoring/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat /tmp/admin_token)" \
  -d '{
    "league_id": "YOUR_LEAGUE_ID",
    "match_id": "SMOKE-TEST-001",
    "season": "2025-26",
    "home_ext": "UEFA-MCI",
    "away_ext": "UEFA-PSG", 
    "home_goals": 2,
    "away_goals": 1,
    "kicked_off_at": "2025-01-15T20:00:00Z",
    "status": "final"
  }'
```

### 4.2 Verify Points Applied Once
- [ ] Check leaderboard for updated points
- [ ] **EXPECTED**: Manchester City owner gets +5 points (2 goals + 3 win)
- [ ] **EXPECTED**: PSG owner gets +1 point (1 goal)
- [ ] Navigate to "My Clubs" page
- [ ] **EXPECTED**: Points display shows recent match results

### 4.3 Idempotency Test - Re-POST Same Result
```bash
# POST the exact same result again
curl -X POST http://localhost:8000/api/scoring/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat /tmp/admin_token)" \
  -d '{
    "league_id": "YOUR_LEAGUE_ID",
    "match_id": "SMOKE-TEST-001",
    "season": "2025-26",
    "home_ext": "UEFA-MCI",
    "away_ext": "UEFA-PSG",
    "home_goals": 2,
    "away_goals": 1,
    "kicked_off_at": "2025-01-15T20:00:00Z",
    "status": "final"
  }'
```

- [ ] **EXPECTED**: API returns success but no double scoring
- [ ] **EXPECTED**: Points totals remain unchanged
- [ ] **EXPECTED**: Settlement record prevents duplicate processing

### 4.4 Leaderboard Updates
- [ ] Navigate to leaderboard page
- [ ] **EXPECTED**: Updated rankings based on match results
- [ ] **EXPECTED**: Weekly breakdown shows match points
- [ ] **EXPECTED**: Total points calculated correctly

---

## **TEST 5: Admin Functionality & Audit Trail**

### 5.1 Admin Log Verification
- [ ] Login as commissioner
- [ ] Navigate to Admin Panel → Audit & Logs
- [ ] **EXPECTED**: All actions logged with timestamps:
  ```
  ✓ create_league
  ✓ invite_member (3 entries)
  ✓ start_auction
  ✓ [Any other admin actions]
  ```
- [ ] Check bid audit trail
- [ ] **EXPECTED**: All bids recorded with user, amount, timestamp

### 5.2 Admin Controls Test
- [ ] Pause auction
- [ ] **EXPECTED**: Bidding disabled, toast notification sent
- [ ] Resume auction  
- [ ] **EXPECTED**: Bidding re-enabled, timer recalculated correctly
- [ ] **EXPECTED**: All actions logged in admin logs

---

## **TEST 6: Access Control Verification**

### 6.1 Non-Member Access Control
- [ ] Create new user: `intruder.smoke@smoketest.com`
- [ ] Try to access league API endpoints:
```bash
# Test API access without proper membership
curl -H "Authorization: Bearer $(cat /tmp/intruder_token)" \
  http://localhost:8000/api/leagues/YOUR_LEAGUE_ID/members
```
- [ ] **EXPECTED**: 403 Forbidden response
- [ ] Try to access auction endpoints
- [ ] **EXPECTED**: Access denied consistently

### 6.2 Role-Based Access
- [ ] Login as regular manager
- [ ] Try to access admin panel
- [ ] **EXPECTED**: Admin panel not visible or access denied
- [ ] Try to access admin API endpoints
- [ ] **EXPECTED**: 403 Forbidden response

---

## **TEST 7: Frontend UX Validation**

### 7.1 Empty States
- [ ] Create new league with no members
- [ ] **EXPECTED**: "No Members Yet" empty state with invite action
- [ ] Check "My Clubs" before owning any
- [ ] **EXPECTED**: "No Clubs Owned Yet" with auction navigation
- [ ] Check fixtures before any are loaded
- [ ] **EXPECTED**: "No Fixtures Scheduled" message

### 7.2 Tooltips & Help
- [ ] Hover over points displays
- [ ] **EXPECTED**: Scoring tooltip shows: "Goals: +1, Wins: +3, Draws: +1" with examples
- [ ] Hover over budget information
- [ ] **EXPECTED**: Budget tooltip shows remaining budget and slot constraints

### 7.3 Real-time Notifications
- [ ] During auction, verify toast notifications appear for:
  - [ ] Bid placed successfully
  - [ ] Outbid by another user
  - [ ] Club sold notifications
  - [ ] Timer extended (anti-snipe)
  - [ ] Invalid bid attempts

---

## **🔍 MONITORING & LOGS**

### Where to View Logs
```bash
# Application logs
docker-compose logs -f app

# Database logs  
docker-compose logs -f mongodb

# All services
docker-compose logs -f

# Specific log files
tail -f ./logs/application.log
tail -f ./logs/auction.log
tail -f ./logs/admin.log
```

### Key Log Entries to Monitor
- Magic link generation: `Magic link sent to user@email.com`
- Auction events: `Bid placed: user123 bid 25 on lot456`
- Admin actions: `Admin action logged: start_auction by commissioner123`
- Scoring events: `Points awarded: +5 to user123 for match SMOKE-TEST-001`
- Access control: `Access denied: user456 attempted to access league789`

### Database Queries for Verification
```javascript
// Connect to MongoDB
mongosh ucl_auction

// Check admin logs
db.admin_logs.find().sort({created_at: -1}).limit(10).pretty()

// Check settlements (idempotency)
db.settlements.find({match_id: "SMOKE-TEST-001"}).pretty()

// Check weekly points
db.weekly_points.find().sort({created_at: -1}).limit(5).pretty()

// Check bid audit
db.bids.find().sort({placed_at: -1}).limit(10).pretty()
```

---

## **🔄 ROLLBACK PROCEDURE**

### Quick Rollback Commands
```bash
# Rollback to previous version
./deploy.sh production rollback

# Manual rollback steps:
1. Stop current application:
   docker-compose down

2. Restore database backup:
   BACKUP_DATE=$(ls -t ./backups | head -n1)
   docker-compose up -d mongodb
   docker cp "./backups/$BACKUP_DATE/backup" ucl-auction-mongodb:/tmp/
   docker-compose exec -T mongodb mongorestore /tmp/backup

3. Start previous application version:
   git checkout [PREVIOUS_COMMIT]
   docker-compose build
   docker-compose up -d

4. Verify health:
   curl http://localhost:8000/health
```

### Emergency Contacts & Procedures
- **System Admin**: admin@uclauction.com
- **Database Issues**: Check `./logs/mongodb.log`  
- **Application Issues**: Check `./logs/application.log`
- **Email Issues**: Verify SMTP settings in environment file

---

## **✅ SMOKE TEST COMPLETION CHECKLIST**

### Critical Path Tests (Must Pass)
- [ ] **Authentication**: Magic link login working
- [ ] **League Creation**: Commissioner can create and manage league
- [ ] **Auction Mechanics**: Bidding, anti-snipe, and sales working
- [ ] **Budget Enforcement**: All constraints properly enforced
- [ ] **Scoring System**: Points calculation and idempotency working
- [ ] **Access Control**: Non-members properly blocked
- [ ] **Admin Logging**: All actions properly audited

### Nice-to-Have Tests (Should Pass)
- [ ] **Real-time Updates**: WebSocket functionality working
- [ ] **UI/UX**: Empty states and tooltips displaying correctly
- [ ] **Email Notifications**: All emails sending properly
- [ ] **Mobile Responsiveness**: Application usable on mobile devices

### Performance Tests (Monitor)
- [ ] **Response Times**: API calls < 2 seconds
- [ ] **WebSocket Latency**: Real-time updates < 1 second
- [ ] **Database Queries**: No slow queries in logs
- [ ] **Memory Usage**: Application memory < 512MB

---

## **🎯 SUCCESS CRITERIA**

**All Critical Path Tests Must Pass** ✅

**Test Results Summary**:
- League Creation: ✅ PASS / ❌ FAIL
- Auction Mechanics: ✅ PASS / ❌ FAIL  
- Budget Enforcement: ✅ PASS / ❌ FAIL
- Scoring System: ✅ PASS / ❌ FAIL
- Access Control: ✅ PASS / ❌ FAIL
- Admin Logging: ✅ PASS / ❌ FAIL

**Deployment Status**: ✅ READY FOR PRODUCTION / ❌ NEEDS FIXES

**Notes**: _[Record any issues found or special configurations needed]_