# Discord Adventure Bot V4

A virtual-currency Discord adventure RPG.

## Main systems
- Soul Coins economy, transfers, daily streaks and gambling using virtual currency only
- Levels, XP, prestige
- 45 core pets + Wither Storm Special pet
- Pet levels 1-50, duplicate upgrades, evolution at level 50
- Pet Battle arena
- Weekly boss and dungeon floors 1-20
- Five world areas with different enemies/rewards/pet pools
- Inventory, weapons, armor, potions and pet materials
- Achievements and daily missions
- Chests with very low Mythical/Special chances
- 24-hour rotating shop
- Blood Moon world event
- Clans, clan bank, clan leaderboard and clan boss
- Player market
- Statistics
- Exact-owner-only `/admin_setup`, then admin tools

## Run
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. Put your token in `.env` as `DISCORD_TOKEN=...`
4. `python bot.py`

Never share your Discord bot token. Existing `game.db` is kept for player progress.


## Exact-owner admin setup
Set `OWNER_ID` in Railway Variables (or `.env`) to your Discord User ID. Only that exact Discord account can use `/admin_setup`, `/admin`, and all `admin_*` commands. Never put your bot token in chat.
