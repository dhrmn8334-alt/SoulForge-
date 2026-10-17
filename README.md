# SoulForge Discord RPG Bot

## Setup
1. Install Python 3.11+ and run `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Set `DISCORD_TOKEN` and `OWNER_ID` (numeric Discord user ID only). Never share your bot token.
4. Run `python bot.py`. Railway can use the included requirements file and start command `python bot.py`.

## Included update
- Gameplay `/tip`, `/weapon_list`, `/weapon_recipe`, `/pet_info`.
- Four-stage pet-slot upgrade system: one default slot, one extra slot per purchase, max five; purchases require player level, Soul Coins and materials. Use `/pet_upgrade_info` then `/pet_upgrade_slots`.
- Ten weapon recipes with requested names, bonuses and abilities listed in the weapon codex.
- Requested cooldowns added for attack, daily-boss attack, work, hunt, mine, explore and dungeon.
- Daily Soul Coin reward reduced to half of the prior formula; XP reward remains unchanged.
- Owner-only admin tools: existing admin commands plus `/admin_give_pet`, `/admin_set_level`, `/admin_reset_player`, `/admin_daily_boss_reset`.
- Invalid non-numeric OWNER_ID no longer crashes startup; it falls back to disabled owner-admin access until configured correctly.
- Existing database file is not bundled or overwritten by the ZIP; keep your Railway persistent volume/game.db to preserve player progress.

## Artwork note
`assets/reference/` contains the generated concept-art reference images available during this build. These are not yet separate production-ready transparent PNGs for every individual pet/material/weapon. The bot currently uses its existing emoji/text presentation for most commands; attach/use individual assets in embeds as a follow-up art-integration step.

## Admin safety
Admin commands check the configured numeric `OWNER_ID`; setting it to `0` or leaving it invalid disables admin access. `/admin_reset_player` is destructive for the selected member's game data in the current server.
