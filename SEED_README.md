# UCL Auction Demo Seed Data

This directory contains comprehensive seed data and scripts to set up a complete UCL Auction demo environment.

## 📁 Seed Data Files

### `seed_data/clubs.json`
Contains 12 top UCL clubs with realistic data:
- **Teams**: Manchester City, Real Madrid, Barcelona, Bayern Munich, PSG, Liverpool, Arsenal, Inter Milan, AC Milan, Borussia Dortmund, Atlético Madrid, Juventus
- **Fields**: `name`, `short_name`, `country`, `ext_ref` (UEFA reference)
- **Usage**: Creates the club pool for auctions

### `seed_data/fixtures.json` 
Contains 18 fixtures across 3 matchdays (MD1-MD3):
- **Matchday 1**: 6 fixtures (Sep 17-18, 2025)
- **Matchday 2**: 6 fixtures (Oct 1-2, 2025)  
- **Matchday 3**: 6 fixtures (Oct 22-23, 2025)
- **Fields**: `match_id`, `date`, `home_ext`, `away_ext`, `season`, `matchday`, `competition`, `status`

### `seed_data/results_sample.json`
Contains final results for Matchday 1 & 2 fixtures (12 completed matches):
- **Realistic scores**: Goals, events, player names
- **Points generation**: Enables scoring system demonstration
- **Fields**: `match_id`, `home_goals`, `away_goals`, `status`, `events`

## 🚀 Seed Script

### `seed_script.py`
Comprehensive seeding automation that creates:

1. **Club Database**: Imports all 12 UCL clubs
2. **Demo Users**: 
   - 1 Commissioner (`commissioner@demo.com`)
   - 4 Managers (`alice.manager@demo.com`, `bob.manager@demo.com`, etc.)
3. **Demo League**: "UCL Demo League 2025-26" with:
   - Budget: 100M per manager
   - Club slots: 3 per manager
   - Standard scoring rules (Goals +1, Wins +3, Draws +1)
4. **Auction Setup**: 8 lots for bidding simulation
5. **Simulated Auction**: Realistic ownership distribution:
   - Manager 0: Man City (25M) + PSG (20M) = 45M spent
   - Manager 1: Real Madrid (30M) + Liverpool (26M) = 56M spent  
   - Manager 2: Barcelona (28M) + Arsenal (18M) = 46M spent
   - Manager 3: Bayern Munich (22M) + Inter Milan (15M) = 37M spent
6. **Fixtures Loading**: All 18 fixtures imported
7. **Results Processing**: 12 completed matches with scoring
8. **Demo Summary**: Complete statistics and URLs

### `run_seed.sh`
Simple bash script to execute seeding with proper environment setup.

## 🎯 Usage

### Quick Start
```bash
# Run the complete seeding process
./run_seed.sh
```

### Manual Execution
```bash
# Set Python path and run
export PYTHONPATH="/app/backend:$PYTHONPATH"
python3 seed_script.py
```

## 📊 Demo Data Statistics

After seeding, you'll have:
- **12 UCL clubs** in the database
- **5 demo users** (1 commissioner + 4 managers)
- **1 demo league** ready for testing
- **8 club ownerships** distributed across managers
- **18 fixtures** across 3 matchdays
- **12 completed matches** with results and scoring
- **Points standings** based on actual match results

## 🔗 Demo Access

### Login Credentials
Use magic-link authentication with these emails:

**Commissioner Access:**
- `commissioner@demo.com` - Full admin panel access

**Manager Access:**
- `alice.manager@demo.com` - Owns Man City + PSG
- `bob.manager@demo.com` - Owns Real Madrid + Liverpool  
- `carol.manager@demo.com` - Owns Barcelona + Arsenal
- `david.manager@demo.com` - Owns Bayern Munich + Inter

### Demo URLs
- **Application**: https://realtime-socket-fix.preview.emergentagent.com
- **My Clubs**: `/clubs/{league_id}`
- **Fixtures**: `/fixtures/{league_id}` 
- **Leaderboard**: `/leaderboard/{league_id}`
- **Admin Panel**: `/admin/{league_id}` (Commissioner only)

## 🎪 Demo Scenarios

### 1. Manager Experience
1. Login as any manager
2. View "My Clubs" - see owned teams and budget
3. Check "Fixtures & Results" - see upcoming/completed matches
4. Review "Leaderboard" - see current standings

### 2. Commissioner Experience  
1. Login as commissioner
2. Access "Admin Panel" - full administrative controls
3. View audit logs and bid history
4. Manage league settings and members

### 3. Real-time Features
- Live auction bidding (if new auction started)
- WebSocket updates for bid changes
- Real-time leaderboard updates

## 🔧 Customization

### Adding More Clubs
Edit `seed_data/clubs.json` to include additional teams:
```json
{
  "name": "Chelsea FC",
  "short_name": "CHE", 
  "country": "England",
  "ext_ref": "UEFA-CHE"
}
```

### Modifying Fixtures
Edit `seed_data/fixtures.json` for different matchups:
```json
{
  "match_id": "UCL-2025-26-MD4-001",
  "date": "2025-11-05T20:00:00Z",
  "home_ext": "UEFA-CHE",
  "away_ext": "UEFA-PSG",
  "season": "2025-26",
  "matchday": 4
}
```

### Adjusting Results
Edit `seed_data/results_sample.json` for different outcomes:
```json
{
  "match_id": "UCL-2025-26-MD1-001",
  "home_goals": 2,
  "away_goals": 1,
  "events": [
    {"type": "goal", "team": "home", "minute": 23}
  ]
}
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Ensure MongoDB is running
sudo systemctl status mongod
```

**Import Errors:**
```bash
# Check Python path
export PYTHONPATH="/app/backend:$PYTHONPATH"
```

**Permission Errors:**
```bash
# Make script executable  
chmod +x /app/run_seed.sh
```

### Resetting Demo Data
```bash
# Clear demo data and re-seed
python3 -c "
import asyncio
from database import initialize_database, db
async def clear_demo():
    await initialize_database()
    await db.users.delete_many({'email': {'$regex': '@demo\.com$'}})
    await db.leagues.delete_many({'name': {'$regex': 'Demo'}})
    print('Demo data cleared')
asyncio.run(clear_demo())
"
./run_seed.sh
```

## 📈 Expected Output

Successful seeding produces:
```
✅ Demo seeding completed successfully!
🎉 UCL AUCTION DEMO READY!
📧 Commissioner: commissioner@demo.com  
📧 Managers: alice.manager@demo.com, bob.manager@demo.com, carol.manager@demo.com, david.manager@demo.com
🏆 League ID: {league_id}
⚽ Clubs: 12 seeded, 8 owned
📊 Points: {total_points} total points from {events} scoring events
📅 Fixtures: 18 loaded
⚽ Results: 12 processed
```

The demo environment provides a complete, realistic UCL auction experience with actual club data, match results, and scoring!