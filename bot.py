import os, random, sqlite3
from datetime import datetime, timedelta, timezone, date
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Discord User ID of the bot creator. Only this account can use admin commands.

try:
    OWNER_ID = int(os.getenv('OWNER_ID', '0') or '0')
except (TypeError, ValueError):
    OWNER_ID = 0  # Invalid usernames are ignored; OWNER_ID must be a numeric Discord user ID.

DB = 'game.db'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

RARITIES = {
    'Common': {'weight': 6000, 'base': (8, 15), 'emoji': '⚪'},
    'Uncommon': {'weight': 2400, 'base': (16, 28), 'emoji': '🟢'},
    'Rare': {'weight': 900, 'base': (30, 48), 'emoji': '🔵'},
    'Epic': {'weight': 400, 'base': (52, 78), 'emoji': '🟣'},
    'Legendary': {'weight': 200, 'base': (85, 125), 'emoji': '🟡'},
    'Mythical': {'weight': 80, 'base': (140, 200), 'emoji': '🔴'},
    'Special': {'weight': 20, 'base': (250, 350), 'emoji': '🌈'},
}
PET_NAMES = {
    'Common': ['Forest Fox','Stone Pup','Meadow Hare','Tiny Boar','Moss Turtle','River Otter','Cave Bat','Snow Mouse','Wild Chick','Dust Lizard', 'Ashen Kit', 'Copper Beetle', 'Lantern Mouse', 'Boulder Toad', 'Pine Marten', 'Dusty Raccoon', 'Pebble Ram', 'Thorn Hedgehog', 'Cinder Chick', 'Willow Ferret', 'Muddy Mole', 'Cloud Pigeon', 'Rusty Gecko', 'Fern Squirrel', 'Cobalt Crab'],
    'Uncommon': ['Silver Wolf','Ember Fox','Frost Lynx','Moon Rabbit','Thunder Crow','Marsh Croc','Iron Badger','Dusk Owl','Coral Serpent','Bramble Bear', 'Rune Wolf', 'Blizzard Fox', 'Copper Falcon', 'Magma Badger', 'Twilight Lynx', 'Storm Ferret', 'Jade Turtle', 'Duskwater Eel', 'Ironhorn Goat', 'Sapphire Crow', 'Bramble Lynx', 'Frostbite Hare', 'Thunder Mantis', 'Gloom Gecko', 'Sunset Crane'],
    'Rare': ['Shadow Panther','Storm Hawk','Crystal Wolf','Inferno Lynx','Void Raven','Glacier Hound','Spirit Deer','Venom Viper', 'Obsidian Stag', 'Tempest Wyvern', 'Crystal Manta', 'Phantom Coyote', 'Frostfang Tiger', 'Ember Roc', 'Moonlit Serpent', 'Venomous Jackal', 'Rift Scorpion', 'Thunder Elk', 'Azure Basilisk', 'Wraith Falcon', 'Glacier Boar', 'Solar Panther', 'Abyssal Shark'],
    'Epic': ['Demon Hound','Phoenix Cub','Abyss Panther','Thunder Dragon','Nightmare Stag','Soul Reaper Cat','Arcane Griffin','Blood Moon Wolf', 'Void Knight Wolf', 'Stormcaller Drake', 'Molten Phoenix', 'Spectral Kitsune', 'Dreadnought Bear', 'Runebound Griffin', 'Frostfire Dragon', 'Soulstorm Raven', 'Nightfall Chimera', 'Eclipse Panther', 'Astral Manticore', 'Doomfang Hound', 'Crimson Wyvern', 'Tempest Kirin', 'Phantom Leviathan'],
    'Legendary': ['Ancient Dragon','Celestial Tiger','Leviathan Pup','Astral Phoenix','King Cobra', 'Worldfire Dragon', 'Titan Wolf', 'Empress Phoenix', 'Void Emperor', 'Storm Seraph', 'Eternal Leviathan', 'Solar Dragonlord', 'Frost Queen Lynx', 'Abyssal Behemoth', 'Celestial Kirin', 'Infernal Hydra', 'Moonbreaker Tiger', 'Astral World Turtle', 'Rift Sovereign', 'Thunder God Roc'],
    'Mythical': ['World Eater','Eternal Kitsune','Cosmic Dragon'],
    'Special': ['Wither Storm']
}
PET_EMOJIS = {
    'Forest Fox':'🦊','Stone Pup':'🐶','Meadow Hare':'🐇','Tiny Boar':'🐗','Moss Turtle':'🐢','River Otter':'🦦','Cave Bat':'🦇','Snow Mouse':'🐭','Wild Chick':'🐥','Dust Lizard':'🦎',
    'Silver Wolf':'🐺','Ember Fox':'🦊','Frost Lynx':'🐈','Moon Rabbit':'🐇','Thunder Crow':'🐦','Marsh Croc':'🐊','Iron Badger':'🦡','Dusk Owl':'🦉','Coral Serpent':'🐍','Bramble Bear':'🐻',
    'Shadow Panther':'🐆','Storm Hawk':'🦅','Crystal Wolf':'🐺','Inferno Lynx':'🐈','Void Raven':'🐦‍⬛','Glacier Hound':'🐕','Spirit Deer':'🦌','Venom Viper':'🐍',
    'Demon Hound':'🐕‍🦺','Phoenix Cub':'🔥','Abyss Panther':'🐈‍⬛','Thunder Dragon':'🐉','Nightmare Stag':'🦌','Soul Reaper Cat':'😼','Arcane Griffin':'🦅','Blood Moon Wolf':'🐺',
    'Ancient Dragon':'🐲','Celestial Tiger':'🐯','Leviathan Pup':'🌊','Astral Phoenix':'🪽','King Cobra':'🐍',
    'World Eater':'🌌','Eternal Kitsune':'🦊','Cosmic Dragon':'🐉','Wither Storm':'🌪️'
}
PET_DAMAGE = {}
for rarity, names in PET_NAMES.items():
    lo, hi = RARITIES[rarity]['base']
    for name in names:
        PET_DAMAGE[name] = random.randint(lo, hi)

QUESTS = {
    1: ('Hunter', 'hunt', 3, 500, 150),
    2: ('Worker', 'work', 5, 650, 175),
    3: ('Gambler', 'game_win', 3, 800, 200),
    4: ('Fighter', 'boss_damage', 1000, 1200, 300),
    5: ('Adventurer', 'xp', 500, 1000, 250),
}


def db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db(); c = con.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        guild_id INTEGER, user_id INTEGER, cash INTEGER DEFAULT 100, xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, attack INTEGER DEFAULT 10, defense INTEGER DEFAULT 5,
        luck INTEGER DEFAULT 0, last_daily TEXT, daily_streak INTEGER DEFAULT 0,
        last_hunt TEXT, last_work TEXT, last_boss_attack TEXT,
        PRIMARY KEY(guild_id,user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS pets (
        guild_id INTEGER, user_id INTEGER, pet_id INTEGER, name TEXT, rarity TEXT,
        damage INTEGER, pet_level INTEGER DEFAULT 1,
        PRIMARY KEY(guild_id,user_id,pet_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS equipped (
        guild_id INTEGER, user_id INTEGER, pet_id INTEGER,
        PRIMARY KEY(guild_id,user_id,pet_id))''')
    try:
        info=c.execute('PRAGMA table_info(equipped)').fetchall()
        pkcols=[row['name'] for row in info if row['pk']]
        if pkcols == ['guild_id','user_id']:
            c.execute('ALTER TABLE equipped RENAME TO equipped_legacy')
            c.execute('CREATE TABLE equipped (guild_id INTEGER, user_id INTEGER, pet_id INTEGER, PRIMARY KEY(guild_id,user_id,pet_id))')
            c.execute('INSERT OR IGNORE INTO equipped SELECT guild_id,user_id,pet_id FROM equipped_legacy')
            c.execute('DROP TABLE equipped_legacy')
    except Exception: pass
    c.execute('''CREATE TABLE IF NOT EXISTS mining (guild_id INTEGER, user_id INTEGER, ore TEXT, amount INTEGER DEFAULT 0, PRIMARY KEY(guild_id,user_id,ore))''')
    c.execute('''CREATE TABLE IF NOT EXISTS crafted_weapons (guild_id INTEGER, user_id INTEGER, weapon TEXT, ability TEXT, attack_bonus INTEGER, PRIMARY KEY(guild_id,user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_bosses (guild_id INTEGER PRIMARY KEY, name TEXT, hp INTEGER, max_hp INTEGER, reward INTEGER, xp_reward INTEGER, day_key TEXT, defeated INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bosses (
        guild_id INTEGER PRIMARY KEY, name TEXT, hp INTEGER, max_hp INTEGER,
        reward INTEGER, xp_reward INTEGER, week_key TEXT, defeated INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quest_progress (
        guild_id INTEGER, user_id INTEGER, quest_id INTEGER, quest_date TEXT,
        progress INTEGER DEFAULT 0, claimed INTEGER DEFAULT 0,
        PRIMARY KEY(guild_id,user_id,quest_id,quest_date))''')
    # Migrate older database files made by the first version.
    for col, definition in [
        ('daily_streak', 'INTEGER DEFAULT 0'), ('last_boss_attack', 'TEXT')
    ]:
        try: c.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        except sqlite3.OperationalError: pass
    try: c.execute('ALTER TABLE pets ADD COLUMN pet_level INTEGER DEFAULT 1')
    except sqlite3.OperationalError: pass
    for col, definition in [('xp_reward','INTEGER DEFAULT 0'),('week_key','TEXT'),('defeated','INTEGER DEFAULT 0')]:
        try: c.execute(f'ALTER TABLE bosses ADD COLUMN {col} {definition}')
        except sqlite3.OperationalError: pass
    con.commit(); con.close()


def ensure_user(gid, uid):
    con=db(); con.execute('INSERT OR IGNORE INTO users(guild_id,user_id) VALUES(?,?)',(gid,uid)); con.commit(); con.close()


def get_user(gid, uid):
    ensure_user(gid,uid); con=db(); r=con.execute('SELECT * FROM users WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); con.close(); return r


def add_xp(gid, uid, amount):
    con=db(); r=con.execute('SELECT xp,level FROM users WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()
    pr=con.execute('SELECT prestige FROM prestige WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()
    bonus=(pr['prestige']*5 if pr else 0)
    amount=int(amount*(1+bonus/100))
    xp=r['xp']+amount; lvl=r['level']; ups=0
    needed=100+((lvl-1)*50)
    while xp>=needed:
        xp-=needed; lvl+=1; ups+=1; needed=100+((lvl-1)*50)
    con.execute('UPDATE users SET xp=?,level=? WHERE guild_id=? AND user_id=?',(xp,lvl,gid,uid)); con.commit(); con.close()
    return ups,lvl


def money(gid, uid, delta):
    con=db(); con.execute('UPDATE users SET cash=cash+? WHERE guild_id=? AND user_id=?',(delta,gid,uid)); con.commit(); con.close()
    if delta > 0:
        try: stat_inc(gid, uid, 'soul_earned', delta); mission_inc(gid, uid, 3, delta)
        except Exception: pass


def cooldown_ok(row, field, minutes):
    v=row[field]
    if not v: return True, 0
    t=datetime.fromisoformat(v); left=timedelta(minutes=minutes)-(datetime.now(timezone.utc)-t)
    return left.total_seconds()<=0, max(0,int(left.total_seconds()))


def cooldown_seconds_ok(row, field, seconds):
    v = row[field]
    if not v: return True, 0
    t = datetime.fromisoformat(v)
    left = seconds - (datetime.now(timezone.utc)-t).total_seconds()
    return left <= 0, max(0, int(left))

def fmt_time(sec):
    return f'{sec//3600}h {(sec%3600)//60}m {sec%60}s' if sec >= 3600 else f'{sec//60}m {sec%60}s'


def today_key(): return datetime.now(timezone.utc).date().isoformat()


def week_key():
    now=datetime.now(timezone.utc).date()
    y,w,_=now.isocalendar()
    return f'{y}-W{w:02d}'


def quest_add(gid, uid, event, amount=1):
    qdate=today_key(); con=db()
    for qid, q in QUESTS.items():
        if q[1] != event: continue
        con.execute('INSERT OR IGNORE INTO quest_progress(guild_id,user_id,quest_id,quest_date,progress,claimed) VALUES(?,?,?,?,0,0)',(gid,uid,qid,qdate))
        con.execute('UPDATE quest_progress SET progress=progress+? WHERE guild_id=? AND user_id=? AND quest_id=? AND quest_date=? AND claimed=0',(amount,gid,uid,qid,qdate))
    con.commit(); con.close()


def pick_pet():
    total=sum(x['weight'] for x in RARITIES.values())
    roll=random.randint(1,total); acc=0
    for rarity, info in RARITIES.items():
        acc += info['weight']
        if roll <= acc:
            name=random.choice(PET_NAMES[rarity])
            return name, rarity, PET_DAMAGE[name]
    name=PET_NAMES['Common'][0]; return name,'Common',PET_DAMAGE[name]


def pet_power(gid, uid):
    con=db()
    rows=con.execute("""SELECT p.damage,p.pet_level FROM pets p JOIN equipped e ON p.guild_id=e.guild_id AND p.user_id=e.user_id AND p.pet_id=e.pet_id WHERE p.guild_id=? AND p.user_id=?""",(gid,uid)).fetchall()
    con.close()
    return sum(r['damage'] + (r['pet_level']-1)*5 for r in rows)


@bot.event
async def on_ready():
    init_db()
    try: await bot.tree.sync()
    except Exception as e: print('sync:',e)
    print(f'Logged in as {bot.user}')


@bot.tree.command(name='helph', description='Show all registered commands and descriptions')
async def helph(interaction):
    # Build help from the live command tree so new commands cannot silently be omitted.
    commands_list = sorted(bot.tree.get_commands(), key=lambda cmd: cmd.name.casefold())
    total = len(commands_list)
    pages = []
    for offset in range(0, total, 20):
        embed = discord.Embed(
            title=f"🖤 SoulForge Command Help ({offset + 1}–{min(offset + 20, total)} of {total})",
            description="Every registered slash command is listed below with its registered description.",
            color=discord.Color.dark_purple(),
        )
        for command in commands_list[offset:offset + 20]:
            desc = (command.description or 'No description provided').strip()
            embed.add_field(name=f"/{command.name}", value=desc[:250], inline=False)
        if offset + 20 >= total:
            embed.set_footer(text="Important Tip: Upgrade wisely, collect materials, and use your pets and gear strategically.")
        pages.append(embed)
    if not pages:
        return await interaction.response.send_message('No slash commands are currently registered.', ephemeral=True)
    await interaction.response.send_message(embed=pages[0], ephemeral=True)
    for page in pages[1:]:
        await interaction.followup.send(embed=page, ephemeral=True)


@bot.tree.command(name='profile', description='View your level, cash and combat stats')
async def profile(interaction):
    u=get_user(interaction.guild_id,interaction.user.id)
    need=100+((u['level']-1)*50)
    con=db(); pet=con.execute('''SELECT p.* FROM pets p JOIN equipped e ON p.guild_id=e.guild_id AND p.user_id=e.user_id AND p.pet_id=e.pet_id WHERE p.guild_id=? AND p.user_id=?''',(interaction.guild_id,interaction.user.id)).fetchone(); con.close()
    embed=discord.Embed(title=f'⚔️ {interaction.user.display_name}', description=f'Level **{u["level"]}** • XP **{u["xp"]}/{need}**')
    embed.add_field(name='🖤🪙 Soul Coins',value=f'{u["cash"]:,}')
    item_atk,item_def=equipped_bonuses(interaction.guild_id,interaction.user.id)
    embed.add_field(name='⚔️ Attack',value=f'{u["attack"] + item_atk} (+{item_atk} items)'); embed.add_field(name='🛡️ Defense',value=f'{u["defense"] + item_def} (+{item_def} items)'); embed.add_field(name='🍀 Luck',value=str(u['luck']))
    embed.add_field(name='🔥 Daily Streak',value=str(u['daily_streak'])); embed.add_field(name='🐾 Equipped Pet',value=(f'{pet["name"]} Lv.{pet["pet_level"]} (+{pet["damage"]} dmg)' if pet else 'None'),inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='balance', description='Check your virtual cash')
async def balance(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); await interaction.response.send_message(f'🖤🪙 {interaction.user.mention}, you have **{u["cash"]:,} Soul Coins**.')


@bot.tree.command(name='daily', description='Claim daily cash with a streak bonus')
async def daily(interaction):
    u=get_user(interaction.guild_id,interaction.user.id)
    now=datetime.now(timezone.utc).date(); last=None
    if u['last_daily']:
        last=datetime.fromisoformat(u['last_daily']).date()
    if last == now:
        return await interaction.response.send_message('⏳ You already claimed today. Come back tomorrow!')
    streak=u['daily_streak'] if last == now-timedelta(days=1) else 0
    streak += 1
    reward=max(1, (min(500 + streak*150, 5000)) // 2)
    xp_reward=min(25 + streak*10, 150)
    con=db(); con.execute('UPDATE users SET last_daily=?,daily_streak=? WHERE guild_id=? AND user_id=?',(datetime.now(timezone.utc).isoformat(),streak,interaction.guild_id,interaction.user.id)); con.commit(); con.close()
    money(interaction.guild_id,interaction.user.id,reward)
    ups,lvl=add_xp(interaction.guild_id,interaction.user.id,xp_reward); quest_add(interaction.guild_id,interaction.user.id,'xp',xp_reward)
    msg=f'🎁 **Daily Claimed!** +🖤🪙 {reward:,} Soul Coins and +{xp_reward} XP\n🔥 Streak: **{streak} days**'
    if streak >= 7: msg += '\n🏆 7+ day streak bonus active!'
    if ups: msg += f'\n🎉 Level up → **{lvl}**!'
    await interaction.response.send_message(msg)


@bot.tree.command(name='work', description='Work for virtual cash')
async def work(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); ok,left=cooldown_seconds_ok(u,'last_work',5)
    if not ok: return await interaction.response.send_message(f'⏳ You can work again in **{fmt_time(left)}**.')
    reward=random.randint(60,180)+u['level']*10; con=db(); con.execute('UPDATE users SET last_work=? WHERE guild_id=? AND user_id=?',(datetime.now(timezone.utc).isoformat(),interaction.guild_id,interaction.user.id)); con.commit(); con.close(); money(interaction.guild_id,interaction.user.id,reward); add_xp(interaction.guild_id,interaction.user.id,15); quest_add(interaction.guild_id,interaction.user.id,'work')
    await interaction.response.send_message(f'💼 You worked and earned **🖤🪙 {reward:,} Soul Coins**!')


@bot.tree.command(name='transfer', description='Transfer virtual cash to another member')
@app_commands.describe(member='Recipient', amount='Amount of virtual cash')
async def transfer(interaction, member: discord.Member, amount: app_commands.Range[int,1,1_000_000]):
    if member.bot or member.id==interaction.user.id: return await interaction.response.send_message('❌ Choose another real member.',ephemeral=True)
    u=get_user(interaction.guild_id,interaction.user.id)
    if u['cash']<amount: return await interaction.response.send_message('❌ You do not have enough cash.',ephemeral=True)
    con=db(); con.execute('UPDATE users SET cash=cash-? WHERE guild_id=? AND user_id=?',(amount,interaction.guild_id,interaction.user.id)); con.execute('INSERT OR IGNORE INTO users(guild_id,user_id) VALUES(?,?)',(interaction.guild_id,member.id)); con.execute('UPDATE users SET cash=cash+? WHERE guild_id=? AND user_id=?',(amount,interaction.guild_id,member.id)); con.commit(); con.close()
    await interaction.response.send_message(f'💸 {interaction.user.mention} transferred **🖤🪙 {amount:,} Soul Coins** to {member.mention}.')


@bot.tree.command(name='hunt', description='Hunt for a chance to find a pet')
async def hunt(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); ok,left=cooldown_seconds_ok(u,'last_hunt',5)
    if not ok: return await interaction.response.send_message(f'🌲 Hunt again in **{fmt_time(left)}**.')
    stat_inc(interaction.guild_id,interaction.user.id,'hunts')
    con=db(); con.execute('UPDATE users SET last_hunt=? WHERE guild_id=? AND user_id=?',(datetime.now(timezone.utc).isoformat(),interaction.guild_id,interaction.user.id)); con.commit(); con.close()
    if random.random()>0.58:
        add_xp(interaction.guild_id,interaction.user.id,20); quest_add(interaction.guild_id,interaction.user.id,'hunt'); return await interaction.response.send_message('🌲 You searched the wild... nothing found this time. +20 XP')
    name,rarity,dmg=pick_pet()
    con=db(); count=con.execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()['n']; pid=count+1; con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)',(interaction.guild_id,interaction.user.id,pid,name,rarity,dmg,1)); con.commit(); con.close(); add_xp(interaction.guild_id,interaction.user.id,50); quest_add(interaction.guild_id,interaction.user.id,'hunt')
    icon=RARITIES[rarity]['emoji']
    await interaction.response.send_message(f'🌲 **HUNT SUCCESS!** {icon} You found a **{rarity} {name}**! (+{dmg} boss damage)\n💡 Pets can appear again, so duplicates can be used for upgrades!\nUse `/equip_pet pet_id:{pid}`')


@bot.tree.command(name='pets', description='View your collected pets')
async def pets(interaction):
    con=db(); rows=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? ORDER BY pet_id',(interaction.guild_id,interaction.user.id)).fetchall(); eq=con.execute('SELECT pet_id FROM equipped WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone(); con.close()
    if not rows: return await interaction.response.send_message('🐾 You have no pets. Use `/hunt`!')
    lines=[f'`{r["pet_id"]}` {PET_EMOJIS.get(r["name"], RARITIES[r["rarity"]]["emoji"])} **{r["name"]}** — {r["rarity"]} — Lv.{r["pet_level"]}/50 — +{r["damage"]} dmg' + (' ⭐' if eq and eq['pet_id']==r['pet_id'] else '') for r in rows[:50]]
    extra=f'\n…and {len(rows)-50} more.' if len(rows)>50 else ''
    await interaction.response.send_message('🐾 **Your Pets**\n'+'\n'.join(lines)+extra+'\nUse `/equip_pet pet_id:<number>` or `/pet_upgrade pet_id:<number>`')


@bot.tree.command(name='equip_pet', description='Equip one of your pets')
@app_commands.describe(pet_id='Pet ID shown by /pets')
async def equip_pet(interaction, pet_id:int):
    con=db(); r=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)).fetchone()
    if not r: con.close(); return await interaction.response.send_message('❌ Pet not found.',ephemeral=True)
    current=con.execute('SELECT pet_id FROM equipped WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchall()
    if any(x['pet_id']==pet_id for x in current):
        con.close(); return await interaction.response.send_message('That pet is already equipped.',ephemeral=True)
    caprow=con.execute('SELECT slots FROM pet_slot_upgrades WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()
    slot_cap=caprow['slots'] if caprow else 1
    if len(current)>=slot_cap:
        con.close(); return await interaction.response.send_message(f'🐾 You have {slot_cap} pet slot(s). Use `/pet_upgrade_slots` to unlock the next slot.',ephemeral=True)
    con.execute('INSERT OR IGNORE INTO equipped VALUES(?,?,?)',(interaction.guild_id,interaction.user.id,pet_id)); con.commit(); con.close(); await interaction.response.send_message(f'⭐ Equipped **{r["name"]}** Lv.{r["pet_level"]}! ({len(current)+1}/{slot_cap} slots used)')


@bot.tree.command(name='unequip_pet', description='Unequip one of your pets')
@app_commands.describe(pet_id='Pet ID to unequip')
async def unequip_pet(interaction, pet_id:int):
    con=db(); cur=con.execute('DELETE FROM equipped WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)); con.commit(); con.close()
    if not cur.rowcount: return await interaction.response.send_message('That pet was not equipped.',ephemeral=True)
    await interaction.response.send_message(f'🐾 Pet `{pet_id}` unequipped.')


@bot.tree.command(name='pet_upgrade', description='Upgrade a pet by consuming a duplicate and cash')
@app_commands.describe(pet_id='Pet ID to upgrade')
async def pet_upgrade(interaction, pet_id:int):
    u=get_user(interaction.guild_id,interaction.user.id); con=db(); target=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)).fetchone()
    if not target: con.close(); return await interaction.response.send_message('❌ Pet not found.',ephemeral=True)
    dup=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND name=? AND pet_id!=? ORDER BY pet_id LIMIT 1',(interaction.guild_id,interaction.user.id,target['name'],pet_id)).fetchone()
    price=250 + target['pet_level']*200
    if not dup: con.close(); return await interaction.response.send_message(f'❌ You need **one duplicate {target["name"]}** plus **🖤🪙 {price:,} Soul Coins** to upgrade.',ephemeral=True)
    if u['cash']<price: con.close(); return await interaction.response.send_message(f'❌ You need **🖤🪙 {price:,} Soul Coins** for this upgrade.',ephemeral=True)
    new_level=min(50,target['pet_level']+1)
    if target['pet_level'] >= 50:
        con.close(); return await interaction.response.send_message('🏆 This pet is already **MAX LEVEL 50**!',ephemeral=True)
    new_damage=int(target['damage']*1.18)+5
    con.execute('UPDATE pets SET damage=?,pet_level=? WHERE guild_id=? AND user_id=? AND pet_id=?',(new_damage,new_level,interaction.guild_id,interaction.user.id,pet_id)); con.execute('DELETE FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,dup['pet_id'])); con.execute('UPDATE users SET cash=cash-? WHERE guild_id=? AND user_id=?',(price,interaction.guild_id,interaction.user.id)); con.commit(); con.close()
    await interaction.response.send_message(f'⬆️ **{PET_EMOJIS.get(target["name"], RARITIES[target["rarity"]]["emoji"])} {target["name"]} upgraded!** Lv.{new_level}/50 • Damage **+{new_damage}**\n🖤🪙 Upgrade cost: 🖤🪙 {price:,} Soul Coins + 1 duplicate consumed.')


@bot.tree.command(name='trade_pet', description='Give one of your pets to another member')
@app_commands.describe(member='Member receiving the pet', pet_id='Your pet ID')
async def trade_pet(interaction, member: discord.Member, pet_id:int):
    if member.bot or member.id==interaction.user.id: return await interaction.response.send_message('❌ Choose another real member.',ephemeral=True)
    con=db(); pet=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)).fetchone()
    if not pet: con.close(); return await interaction.response.send_message('❌ Pet not found.',ephemeral=True)
    con.execute('INSERT OR IGNORE INTO users(guild_id,user_id) VALUES(?,?)',(interaction.guild_id,member.id))
    maxid=con.execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(interaction.guild_id,member.id)).fetchone()['n']
    con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)',(interaction.guild_id,member.id,maxid+1,pet['name'],pet['rarity'],pet['damage'],pet['pet_level']))
    con.execute('DELETE FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)); con.execute('DELETE FROM equipped WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)); con.commit(); con.close()
    await interaction.response.send_message(f'🤝 {interaction.user.mention} traded **{pet["rarity"]} {pet["name"]}** to {member.mention}.')


async def boss_row(gid):
    wk=week_key(); con=db(); r=con.execute('SELECT * FROM bosses WHERE guild_id=?',(gid,)).fetchone()
    if not r or r['week_key'] != wk:
        name=random.choice(['The Void Titan','The Ancient Overlord','The Abyssal King','The Colossal Wyrm'])
        hp=25000; reward=30000; xp_reward=5000
        con.execute('INSERT OR REPLACE INTO bosses VALUES(?,?,?,?,?,?,?,?)',(gid,name,hp,hp,reward,xp_reward,wk,0)); con.commit(); r=con.execute('SELECT * FROM bosses WHERE guild_id=?',(gid,)).fetchone()
    con.close(); return r


async def daily_boss_row(gid):
    today=today_key(); con=db(); r=con.execute('SELECT * FROM daily_bosses WHERE guild_id=?',(gid,)).fetchone()
    if not r or r['day_key'] != today:
        name=random.choice(['Ashfang the Ravager','The Iron Warden','Cursed Moon Beast','Soul Devourer','Crimson Golem'])
        hp=random.randint(1000,2000); reward=random.randint(1200,2400); xp_reward=random.randint(250,500)
        con.execute('INSERT OR REPLACE INTO daily_bosses VALUES(?,?,?,?,?,?,?,0)',(gid,name,hp,hp,reward,xp_reward,today)); con.commit(); r=con.execute('SELECT * FROM daily_bosses WHERE guild_id=?',(gid,)).fetchone()
    con.close(); return r

@bot.tree.command(name='daily_boss', description='View today’s daily boss')
async def daily_boss(interaction):
    r=await daily_boss_row(interaction.guild_id)
    status='🏆 DEFEATED TODAY' if r['defeated'] else f'❤️ HP: **{r["hp"]:,}/{r["max_hp"]:,}**'
    await interaction.response.send_message(f'☠️ **DAILY BOSS: {r["name"]}**\n{status}\n🖤🪙 Reward: **{r["reward"]:,} Soul Coins** • ✨ **{r["xp_reward"]:,} XP**\nUse `/attack_daily_boss` to fight!')

@bot.tree.command(name='attack_daily_boss', description='Attack today’s daily boss')
async def attack_daily_boss(interaction):
    if not await command_cooldown(interaction,'attack_daily_boss',2): return
    u=get_user(interaction.guild_id,interaction.user.id); r=await daily_boss_row(interaction.guild_id)
    if r['defeated'] or r['hp']<=0: return await interaction.response.send_message('🏆 Daily boss is already defeated. It resets tomorrow!',ephemeral=True)
    petd=pet_power(interaction.guild_id,interaction.user.id); item_atk,_=equipped_bonuses(interaction.guild_id,interaction.user.id)
    dmg=random.randint(max(1,u['attack']+item_atk-4),u['attack']+item_atk+10)+petd+random.randint(0,max(0,u['luck']//2)); dmg, weapon_note=weapon_proc(interaction.guild_id,interaction.user.id,dmg)
    con=db(); con.execute('BEGIN IMMEDIATE'); cur=con.execute('SELECT * FROM daily_bosses WHERE guild_id=?',(interaction.guild_id,)).fetchone()
    if not cur or cur['defeated'] or cur['hp']<=0:
        con.rollback(); con.close(); return await interaction.response.send_message('🏆 Daily boss is already defeated. It resets tomorrow!',ephemeral=True)
    hp=max(0,cur['hp']-dmg); defeated=1 if hp==0 else 0
    con.execute('UPDATE daily_bosses SET hp=?,defeated=? WHERE guild_id=?',(hp,defeated,interaction.guild_id)); con.commit(); con.close()
    add_xp(interaction.guild_id,interaction.user.id,25)
    msg=f'⚔️ You dealt **{dmg} damage** to **{cur["name"]}**!\n❤️ Boss HP: **{hp:,}/{cur["max_hp"]:,}**\n✨ +25 XP' + (f'\n{weapon_note}' if weapon_note else '')
    if defeated:
        money(interaction.guild_id,interaction.user.id,cur['reward']); add_xp(interaction.guild_id,interaction.user.id,cur['xp_reward']); msg+=f'\n🏆 **DAILY BOSS DEFEATED!** +🖤🪙 {cur["reward"]:,} Soul Coins and +{cur["xp_reward"]:,} XP!'
    await interaction.response.send_message(msg)


@bot.tree.command(name='weekly_boss', description='View the extremely hard weekly boss')
async def weekly_boss(interaction):
    r=await boss_row(interaction.guild_id)
    status='🏆 **DEFEATED THIS WEEK**' if r['defeated'] else f'❤️ HP: **{r["hp"]:,}/{r["max_hp"]:,}**'
    action='' if r['defeated'] else '\nUse `/attack` to fight!'
    await interaction.response.send_message(f'👹 **WEEKLY BOSS: {r["name"]}**\n{status}\n🖤🪙 Defeat reward: **🖤🪙 {r["reward"]:,} Soul Coins**\n✨ XP reward: **{r["xp_reward"]:,}**\n\n⚠️ This boss is intentionally VERY hard and resets every week.{action}')


@bot.tree.command(name='boss', description='View today’s daily boss')
async def boss(interaction):
    await daily_boss(interaction)


@bot.tree.command(name='attack', description='Attack the weekly boss')
async def attack(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); await boss_row(interaction.guild_id)
    ok,left=cooldown_seconds_ok(u,'last_boss_attack',2)
    if not ok: return await interaction.response.send_message(f'⏳ Your attack is on cooldown: **{fmt_time(left)}**.',ephemeral=True)
    con=db(); con.execute('BEGIN IMMEDIATE')
    r=con.execute('SELECT * FROM bosses WHERE guild_id=?',(interaction.guild_id,)).fetchone()
    if not r or r['defeated'] or r['hp']<=0:
        con.rollback(); con.close(); return await interaction.response.send_message('🏆 The weekly boss has already been defeated this week. Wait for the next reset!',ephemeral=True)
    petd=pet_power(interaction.guild_id,interaction.user.id)
    item_atk,_=equipped_bonuses(interaction.guild_id,interaction.user.id); atk=u['attack']+item_atk
    base=random.randint(max(1,atk-4),atk+10); dmg=base+petd+random.randint(0,max(0,u['luck']//2)); dmg, weapon_note=weapon_proc(interaction.guild_id,interaction.user.id,dmg)
    newhp=max(0,r['hp']-dmg); defeated=1 if newhp==0 else 0
    con.execute('UPDATE bosses SET hp=?,defeated=? WHERE guild_id=? AND hp=? AND defeated=0',(newhp,defeated,interaction.guild_id,r['hp']))
    if con.total_changes == 0:
        con.rollback(); con.close(); return await interaction.response.send_message('⚠️ Someone else just finished the boss. Try again next week.',ephemeral=True)
    con.execute('UPDATE users SET last_boss_attack=? WHERE guild_id=? AND user_id=?',(datetime.now(timezone.utc).isoformat(),interaction.guild_id,interaction.user.id)); con.commit(); con.close()
    ups,lvl=add_xp(interaction.guild_id,interaction.user.id,20); quest_add(interaction.guild_id,interaction.user.id,'boss_damage',dmg); quest_add(interaction.guild_id,interaction.user.id,'xp',20)
    msg=f'⚔️ {interaction.user.mention} dealt **{dmg} damage**!\n👹 Boss HP: **{newhp:,}/{r["max_hp"]:,}**' + (f'\n{weapon_note}' if weapon_note else '')
    if defeated:
        money(interaction.guild_id,interaction.user.id,r['reward']); stat_inc(interaction.guild_id,interaction.user.id,'boss_kills'); add_xp(interaction.guild_id,interaction.user.id,r['xp_reward']); msg+=f'\n\n🏆 **WEEKLY BOSS DEFEATED!**\n🖤🪙 +{r["reward"]:,} Soul Coins\n✨ +{r["xp_reward"]:,} XP'
    if ups: msg+=f'\n🎉 Level up → **{lvl}**!'
    await interaction.response.send_message(msg)

WEAPONS = {
 'Iron Reaper': {'cost':{'🪨 Iron Ore':8,'💎 Crystal Shard':2},'bonus':15,'ability':'Reaper’s Mark: 15% chance to double weapon bonus damage.'},
 'Venom Fang': {'cost':{'🪨 Iron Ore':6,'💎 Crystal Shard':3},'bonus':22,'ability':'Poison Bite: 20% chance to poison for the next 2 attacks.'},
 'Frostmourne Edge': {'cost':{'🪨 Iron Ore':8,'💎 Crystal Shard':5},'bonus':28,'ability':'Frozen Strike: 15% chance for +40 damage.'},
 'Emberblade': {'cost':{'🪨 Iron Ore':5,'🔥 Ember Core':5},'bonus':35,'ability':'Inferno: every third attack gains +50 bonus damage.'},
 'Stormbreaker Axe': {'cost':{'🪨 Iron Ore':10,'🔥 Ember Core':4},'bonus':42,'ability':'Thunderclap: 20% chance for +60 damage.'},
 'Voidbreaker': {'cost':{'💎 Crystal Shard':6,'🔥 Ember Core':3,'🌑 Void Fragment':2},'bonus':50,'ability':'Void Surge: 15% chance for +100 damage.'},
 'Sunpiercer': {'cost':{'💎 Crystal Shard':8,'🔥 Ember Core':5,'🌑 Void Fragment':2},'bonus':60,'ability':'Solar Burst: 15% chance for +120 damage.'},
 'Bloodmoon Greatsword': {'cost':{'🪨 Iron Ore':12,'🔥 Ember Core':8,'🌑 Void Fragment':3},'bonus':70,'ability':'Blood Frenzy: 20% chance to restore battle health and deal +50 damage.'},
 'Astral Devourer': {'cost':{'💎 Crystal Shard':12,'🔥 Ember Core':8,'🌑 Void Fragment':6},'bonus':85,'ability':'Starfall: 12% chance for +180 damage.'},
 'Soulforge Obliterator': {'cost':{'💎 Crystal Shard':15,'🔥 Ember Core':10,'🌑 Void Fragment':8},'bonus':110,'ability':'Soul Annihilation: 10% chance for +250 damage.'}}


async def command_cooldown(interaction, command, seconds):
    # Serialize read/check/write so simultaneous requests cannot bypass cooldowns.
    gid, uid = interaction.guild_id, interaction.user.id
    con=db()
    try:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT used_at FROM command_cooldowns WHERE guild_id=? AND user_id=? AND command=?',(gid,uid,command)).fetchone()
        now=datetime.now(timezone.utc)
        if row:
            try:
                last=datetime.fromisoformat(row['used_at'])
                if last.tzinfo is None: last=last.replace(tzinfo=timezone.utc)
                left=seconds-(now-last).total_seconds()
            except (TypeError, ValueError):
                left=0
            if left>0:
                con.rollback()
                await interaction.response.send_message(f'⏳ Try again in {int(left)+1}s.',ephemeral=True)
                return False
        con.execute('INSERT INTO command_cooldowns VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id,command) DO UPDATE SET used_at=excluded.used_at',(gid,uid,command,now.isoformat()))
        con.commit()
        return True
    finally:
        con.close()

@bot.tree.command(name='mine', description='Mine ores and crafting materials')
async def mine(interaction):
    if not await command_cooldown(interaction,'mine',5): return
    gid,uid=interaction.guild_id,interaction.user.id; found=[]
    for _ in range(random.randint(2,4)):
        ore=random.choices(['🪨 Iron Ore','💎 Crystal Shard','🔥 Ember Core','🌑 Void Fragment'],weights=[45,30,18,7])[0]
        qty=random.randint(1,3 if ore=='🪨 Iron Ore' else 2); con=db()
        con.execute('INSERT INTO mining VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id,ore) DO UPDATE SET amount=amount+excluded.amount',(gid,uid,ore,qty)); con.commit(); con.close(); found.append(f'{ore} **+{qty}**')
    await interaction.response.send_message('⛏️ **Mining haul**\n'+'\n'.join(found)+'\nUse `/materials` to check ores and `/craft_weapon` to forge a weapon.')

@bot.tree.command(name='materials', description='View your crafting materials')
async def materials(interaction):
    con=db(); rows=con.execute('SELECT ore,amount FROM mining WHERE guild_id=? AND user_id=? AND amount>0 ORDER BY ore',(interaction.guild_id,interaction.user.id)).fetchall(); con.close()
    await interaction.response.send_message('⛏️ **Materials**\n'+('\n'.join(f'{r["ore"]}: **{r["amount"]}**' for r in rows) if rows else 'No materials yet. Use `/mine`!'))

@bot.tree.command(name='craft_weapon', description='Craft a weapon with a unique ability')
@app_commands.choices(weapon=[app_commands.Choice(name=n,value=n) for n in WEAPONS])
async def craft_weapon(interaction, weapon:app_commands.Choice[str]):
    w=WEAPONS[weapon.value]; gid,uid=interaction.guild_id,interaction.user.id; con=db()
    rows=con.execute('SELECT ore,amount FROM mining WHERE guild_id=? AND user_id=?',(gid,uid)).fetchall(); inv={r['ore']:r['amount'] for r in rows}
    missing=[f'{ore} x{qty}' for ore,qty in w['cost'].items() if inv.get(ore,0)<qty]
    if missing: con.close(); return await interaction.response.send_message('❌ Missing materials: '+', '.join(missing),ephemeral=True)
    for ore,qty in w['cost'].items(): con.execute('UPDATE mining SET amount=amount-? WHERE guild_id=? AND user_id=? AND ore=?',(qty,gid,uid,ore))
    con.execute('INSERT OR REPLACE INTO crafted_weapons VALUES(?,?,?,?,?)',(gid,uid,weapon.value,w['ability'],w['bonus'])); con.commit(); con.close()
    await interaction.response.send_message(f'⚒️ **{weapon.value} crafted and equipped!**\n⚔️ Attack bonus: **+{w["bonus"]}**\n✨ Ability: {w["ability"]}')


SHOP={'attack':(150,3),'defense':(150,3),'luck':(250,2)}
@bot.tree.command(name='shop', description='View stat upgrades')
async def shop(interaction):
    await interaction.response.send_message('🛒 **SHOP**\n⚔️ `/buy attack` — 150 Soul Coins → +3 Attack\n🛡️ `/buy defense` — 150 Soul Coins → +3 Defense\n🍀 `/buy luck` — 250 Soul Coins → +2 Luck')


@bot.tree.command(name='buy', description='Buy a stat upgrade')
@app_commands.describe(stat='attack, defense or luck')
async def buy(interaction, stat:str):
    stat=stat.lower()
    if stat not in SHOP: return await interaction.response.send_message('❌ Choose: attack, defense, luck',ephemeral=True)
    price,inc=SHOP[stat]; u=get_user(interaction.guild_id,interaction.user.id)
    if u['cash']<price: return await interaction.response.send_message('❌ Not enough cash.',ephemeral=True)
    con=db(); con.execute(f'UPDATE users SET cash=cash-?, {stat}={stat}+? WHERE guild_id=? AND user_id=?',(price,inc,interaction.guild_id,interaction.user.id)); con.commit(); con.close(); await interaction.response.send_message(f'🛒 Upgrade bought! **{stat.title()} +{inc}** for **${price}**.')


async def gamble(interaction, amount, game):
    u=get_user(interaction.guild_id,interaction.user.id)
    if amount<1 or amount>u['cash'] or amount>10000: return await interaction.response.send_message('❌ Bet must be between 1 Soul Coin and your balance (max 10,000 Soul Coins).',ephemeral=True)
    if game=='coinflip':
        win=random.random()<0.5; payout=amount if win else -amount; result='🖤🪙 HEADS — WIN' if win else '🖤🪙 TAILS — LOSE'
    elif game=='dice':
        guess=1
        win=random.randint(1,6)==guess; payout=amount*4 if win else -amount; result='🎲 Roll 1-6'
    else:
        slots=[random.choice(['🍒','🍋','⭐','💎']) for _ in range(3)]; triple=len(set(slots))==1; pair=len(set(slots))==2
        if triple: payout=amount*4
        elif pair: payout=amount
        else: payout=-amount
        result=' '.join(slots)
    money(interaction.guild_id,interaction.user.id,payout); add_xp(interaction.guild_id,interaction.user.id,5)
    stat_inc(interaction.guild_id,interaction.user.id,'gambles_won' if payout>0 else 'gambles_lost')
    if payout>0: quest_add(interaction.guild_id,interaction.user.id,'game_win')
    await interaction.response.send_message(f'🎰 **{game.upper()}** — {result}\n🖤🪙 Net: **{payout:+,}** | Balance: **🖤🪙 {get_user(interaction.guild_id,interaction.user.id)["cash"]:,}**')


@bot.tree.command(name='coinflip', description='Virtual-cash coinflip')
@app_commands.describe(amount='Virtual cash bet')
async def coinflip(interaction, amount:app_commands.Range[int,1,10000]): await gamble(interaction,amount,'coinflip')


@bot.tree.command(name='slots', description='Virtual-cash slot machine')
@app_commands.describe(amount='Virtual cash bet')
async def slots(interaction, amount:app_commands.Range[int,1,10000]): await gamble(interaction,amount,'slots')


@bot.tree.command(name='dice', description='Roll dice for virtual cash')
@app_commands.describe(amount='Bet amount')
async def dice(interaction, amount:app_commands.Range[int,1,10000]):
    u=get_user(interaction.guild_id,interaction.user.id)
    if amount>u['cash']: return await interaction.response.send_message('❌ Not enough cash.',ephemeral=True)
    roll=random.randint(1,6); payout=amount*4 if roll==6 else -amount
    money(interaction.guild_id,interaction.user.id,payout); stat_inc(interaction.guild_id,interaction.user.id,'gambles_won' if payout>0 else 'gambles_lost'); await interaction.response.send_message(f'🎲 You rolled **{roll}**. Net: **{payout:+,}**')
    if payout>0: quest_add(interaction.guild_id,interaction.user.id,'game_win')


@bot.tree.command(name='roulette', description='Virtual-cash roulette: red, black, green or a number')
@app_commands.describe(amount='Bet amount', choice='red, black, green or number 0-36')
async def roulette(interaction, amount:app_commands.Range[int,1,10000], choice:str):
    u=get_user(interaction.guild_id,interaction.user.id)
    if amount>u['cash']: return await interaction.response.send_message('❌ Not enough cash.',ephemeral=True)
    choice=choice.lower().strip(); n=random.randint(0,36); red={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}; color='green' if n==0 else ('red' if n in red else 'black')
    win=False; multiplier=0
    if choice in ('red','black','green'): win=choice==color; multiplier=2 if choice!='green' else 14
    elif choice.isdigit() and 0<=int(choice)<=36: win=int(choice)==n; multiplier=35
    else: return await interaction.response.send_message('❌ Choice must be red, black, green, or 0-36.',ephemeral=True)
    payout=amount*multiplier if win else -amount; money(interaction.guild_id,interaction.user.id,payout); stat_inc(interaction.guild_id,interaction.user.id,'gambles_won' if win else 'gambles_lost')
    if win: quest_add(interaction.guild_id,interaction.user.id,'game_win')
    await interaction.response.send_message(f'🎡 Roulette: **{n} ({color})**\n🖤🪙 Net: **{payout:+,}**')


@bot.tree.command(name='blackjack', description='Simple virtual-cash blackjack')
@app_commands.describe(amount='Bet amount')
async def blackjack(interaction, amount:app_commands.Range[int,1,10000]):
    u=get_user(interaction.guild_id,interaction.user.id)
    if amount>u['cash']: return await interaction.response.send_message('❌ Not enough cash.',ephemeral=True)
    player=random.randint(14,21); dealer=random.randint(15,21)
    if player>dealer: payout=amount
    elif player==dealer: payout=0
    else: payout=-amount
    money(interaction.guild_id,interaction.user.id,payout); stat_inc(interaction.guild_id,interaction.user.id,'gambles_won' if payout>0 else 'gambles_lost')
    if payout>0: quest_add(interaction.guild_id,interaction.user.id,'game_win')
    await interaction.response.send_message(f'🃏 **BLACKJACK**\nYou: **{player}** • Dealer: **{dealer}**\n🖤🪙 Net: **{payout:+,}**')


@bot.tree.command(name='duel', description='Challenge a friend to a virtual-cash duel')
@app_commands.describe(member='Friend to challenge', amount='Optional wager, 0 for free duel')
async def duel(interaction, member:discord.Member, amount:app_commands.Range[int,0,10000]=0):
    if member.bot or member.id==interaction.user.id: return await interaction.response.send_message('❌ Choose another real member.',ephemeral=True)
    u=get_user(interaction.guild_id,interaction.user.id); v=get_user(interaction.guild_id,member.id)
    if amount>u['cash'] or amount>v['cash']: return await interaction.response.send_message('❌ Both players need enough cash for this wager.',ephemeral=True)
    winner=interaction.user if random.random()<0.5 else member; loser=member if winner.id==interaction.user.id else interaction.user
    if amount:
        money(interaction.guild_id,loser.id,-amount); money(interaction.guild_id,winner.id,amount)
    add_xp(interaction.guild_id,winner.id,30); add_xp(interaction.guild_id,loser.id,10)
    stat_inc(interaction.guild_id,winner.id,'duels_won'); stat_inc(interaction.guild_id,loser.id,'duels_lost')
    await interaction.response.send_message(f'⚔️ **DUEL!** {interaction.user.mention} vs {member.mention}\n🏆 Winner: **{winner.mention}**\n🖤🪙 Wager: **🖤🪙 {amount:,} Soul Coins**')


@bot.tree.command(name='pet_battle', description='Battle another member using your equipped pets')
@app_commands.describe(member='Friend to battle', amount='Optional Soul Coin wager')
async def pet_battle(interaction, member:discord.Member, amount:app_commands.Range[int,0,10000]=0):
    if member.bot or member.id==interaction.user.id:
        return await interaction.response.send_message('❌ Choose another real member.',ephemeral=True)
    con=db()
    a=con.execute('''SELECT p.* FROM pets p JOIN equipped e ON p.guild_id=e.guild_id AND p.user_id=e.user_id AND p.pet_id=e.pet_id WHERE p.guild_id=? AND p.user_id=?''',(interaction.guild_id,interaction.user.id)).fetchone()
    b=con.execute('''SELECT p.* FROM pets p JOIN equipped e ON p.guild_id=e.guild_id AND p.user_id=e.user_id AND p.pet_id=e.pet_id WHERE p.guild_id=? AND p.user_id=?''',(interaction.guild_id,member.id)).fetchone()
    con.close()
    if not a or not b:
        return await interaction.response.send_message('❌ Both players need an equipped pet.',ephemeral=True)
    u=get_user(interaction.guild_id,interaction.user.id); v=get_user(interaction.guild_id,member.id)
    if amount>u['cash'] or amount>v['cash']:
        return await interaction.response.send_message('❌ Both players need enough Soul Coins for this wager.',ephemeral=True)
    item_atk_a,_=equipped_bonuses(interaction.guild_id,interaction.user.id); ap=a['damage'] + (a['pet_level']-1)*5 + (u['attack']+item_atk_a)//2 + random.randint(0,max(1,u['luck']))
    item_atk_b,_=equipped_bonuses(interaction.guild_id,member.id); bp=b['damage'] + (b['pet_level']-1)*5 + (v['attack']+item_atk_b)//2 + random.randint(0,max(1,v['luck']))
    if ap==bp: winner=None
    else: winner=interaction.user if ap>bp else member
    if winner and amount:
        loser=member if winner.id==interaction.user.id else interaction.user
        money(interaction.guild_id,loser.id,-amount); money(interaction.guild_id,winner.id,amount)
    add_xp(interaction.guild_id,interaction.user.id,20); add_xp(interaction.guild_id,member.id,20)
    emoji_a=PET_EMOJIS.get(a['name'],RARITIES[a['rarity']]['emoji']); emoji_b=PET_EMOJIS.get(b['name'],RARITIES[b['rarity']]['emoji'])
    if winner:
        stat_inc(interaction.guild_id,winner.id,'battles_won'); mission_inc(interaction.guild_id,winner.id,2)

        stat_inc(interaction.guild_id,(member.id if winner.id==interaction.user.id else interaction.user.id),'battles_lost')
    result='🤝 **DRAW!**' if not winner else f'🏆 **Winner: {winner.mention}**'
    await interaction.response.send_message(f'⚔️ **PET BATTLE**\n{interaction.user.mention}: {emoji_a} **{a["name"]} Lv.{a["pet_level"]}/50** → Power **{ap}**\n{member.mention}: {emoji_b} **{b["name"]} Lv.{b["pet_level"]}/50** → Power **{bp}**\n{result}\n🖤🪙 Soul Coin wager: **{amount:,}**')


@bot.tree.command(name='quests', description='View your daily quests')
async def quests(interaction):
    qdate=today_key(); con=db(); lines=[]
    for qid,(name,event,target,reward,xpr) in QUESTS.items():
        row=con.execute('SELECT progress,claimed FROM quest_progress WHERE guild_id=? AND user_id=? AND quest_id=? AND quest_date=?',(interaction.guild_id,interaction.user.id,qid,qdate)).fetchone()
        p=min(row['progress'],target) if row else 0; claimed=bool(row['claimed']) if row else False
        status='✅ CLAIMED' if claimed else f'**{p}/{target}**'
        lines.append(f'`{qid}` **{name}** — {status} • 🖤🪙 {reward:,} Soul Coins • ✨ {xpr} XP')
    con.close(); await interaction.response.send_message('📜 **DAILY QUESTS**\n'+'\n'.join(lines)+'\nUse `/quest_claim quest_id:<number>` when complete.')


@bot.tree.command(name='quest_claim', description='Claim a completed daily quest')
@app_commands.describe(quest_id='Quest ID shown by /quests')
async def quest_claim(interaction, quest_id:int):
    if quest_id not in QUESTS: return await interaction.response.send_message('❌ Invalid quest ID.',ephemeral=True)
    qdate=today_key(); name,event,target,reward,xpr=QUESTS[quest_id]; con=db(); row=con.execute('SELECT progress,claimed FROM quest_progress WHERE guild_id=? AND user_id=? AND quest_id=? AND quest_date=?',(interaction.guild_id,interaction.user.id,quest_id,qdate)).fetchone()
    if not row or row['progress']<target: con.close(); return await interaction.response.send_message(f'❌ Quest not complete yet. Need **{target} {event}**.',ephemeral=True)
    if row['claimed']: con.close(); return await interaction.response.send_message('❌ Quest already claimed.',ephemeral=True)
    con.execute('UPDATE quest_progress SET claimed=1 WHERE guild_id=? AND user_id=? AND quest_id=? AND quest_date=?',(interaction.guild_id,interaction.user.id,quest_id,qdate)); con.commit(); con.close(); money(interaction.guild_id,interaction.user.id,reward); add_xp(interaction.guild_id,interaction.user.id,xpr)
    await interaction.response.send_message(f'🎉 Quest **{name}** claimed! 🖤🪙 +🖤🪙 {reward:,} Soul Coins • ✨ +{xpr} XP')


@bot.tree.command(name='leaderboard', description='Server cash leaderboard')
async def leaderboard(interaction):
    con=db(); rows=con.execute('SELECT user_id,cash,level FROM users WHERE guild_id=? ORDER BY cash DESC LIMIT 10',(interaction.guild_id,)).fetchall(); con.close()
    lines=[f'**{i}.** <@{r["user_id"]}> — 🖤🪙 {r["cash"]:,} Soul Coins • Lv.{r["level"]}' for i,r in enumerate(rows,1)]
    await interaction.response.send_message('🏆 **SERVER LEADERBOARD**\n'+'\n'.join(lines))





@bot.tree.command(name='leaderboards', description='View leaderboards for all major game systems')
async def leaderboards(interaction):
    con=db()
    gid=interaction.guild_id
    rows=con.execute('''SELECT u.user_id,u.cash,u.level,s.hunts,s.boss_kills,s.battles_won,s.gambles_won,s.duels_won,s.dungeon_clears, u.daily_streak
                        FROM users u LEFT JOIN stats s ON s.guild_id=u.guild_id AND s.user_id=u.user_id
                        WHERE u.guild_id=?''',(gid,)).fetchall()
    con.close()
    def top(key, label, fmt=lambda r: str(r[key] or 0)):
        ordered=sorted(rows,key=lambda r:(r[key] or 0),reverse=True)[:5]
        if not ordered or (ordered[0][key] or 0)==0: return f'**{label}**\n— No scores yet'
        return f'**{label}**\n'+'\n'.join(f'**{i}.** <@{r["user_id"]}> — {fmt(r)}' for i,r in enumerate(ordered,1))
    emb=discord.Embed(title='🏆 ALL GAME LEADERBOARDS',description='Top 5 players in each category')
    emb.add_field(name='🖤🪙 Soul Coins',value=top('cash','',lambda r:f'{r["cash"]:,}'),inline=True)
    emb.add_field(name='📈 Level',value=top('level','',lambda r:f'Lv.{r["level"]}'),inline=True)
    emb.add_field(name='🐾 Hunts',value=top('hunts','',lambda r:f'{r["hunts"]:,}'),inline=True)
    emb.add_field(name='👹 Boss Kills',value=top('boss_kills','',lambda r:f'{r["boss_kills"]:,}'),inline=True)
    emb.add_field(name='⚔️ Pet Battles',value=top('battles_won','',lambda r:f'{r["battles_won"]:,} wins'),inline=True)
    emb.add_field(name='🎰 Gambling',value=top('gambles_won','',lambda r:f'{r["gambles_won"]:,} wins'),inline=True)
    emb.add_field(name='⚔️ Duels',value=top('duels_won','',lambda r:f'{r["duels_won"]:,} wins'),inline=True)
    emb.add_field(name='🏰 Dungeon',value=top('dungeon_clears','',lambda r:f'{r["dungeon_clears"]:,} clears'),inline=True)
    emb.add_field(name='🔥 Daily Streak',value=top('daily_streak','',lambda r:f'{r["daily_streak"]:,} days'),inline=True)
    await interaction.response.send_message(embed=emb)

# ===== V4 EXPANSION =====
AREAS = {
    'dark_forest': {'name':'🌲 Dark Forest','rarities':['Common','Uncommon','Rare'],'coins':(80,220),'xp':(25,60),'enemy':(20,60)},
    'frozen_lands': {'name':'❄️ Frozen Lands','rarities':['Uncommon','Rare','Epic'],'coins':(120,320),'xp':(40,90),'enemy':(35,85)},
    'inferno': {'name':'🌋 Inferno','rarities':['Rare','Epic','Legendary'],'coins':(180,450),'xp':(60,130),'enemy':(55,120)},
    'void': {'name':'🌌 Void','rarities':['Epic','Legendary','Mythical'],'coins':(260,700),'xp':(90,190),'enemy':(80,170)},
    'cursed_realm': {'name':'☠️ Cursed Realm','rarities':['Legendary','Mythical','Special'],'coins':(400,1200),'xp':(140,300),'enemy':(120,240)},
}

ITEMS = {
    'rusty_sword': ('⚔️ Rusty Sword','weapon',3,120),
    'iron_blade': ('⚔️ Iron Blade','weapon',7,350),
    'void_blade': ('🗡️ Void Blade','weapon',14,1000),
    'leather_armor': ('🛡️ Leather Armor','armor',3,120),
    'iron_armor': ('🛡️ Iron Armor','armor',8,400),
    'void_armor': ('🛡️ Void Armor','armor',16,1200),
    'small_potion': ('🧪 Small Potion','potion',20,80),
    'large_potion': ('🧪 Large Potion','potion',60,250),
    'pet_core': ('🔮 Pet Core','material',1,500),
    'evolution_shard': ('💎 Evolution Shard','material',1,1200),
}
CHESTS = {'basic':('🟤 Basic Chest',0.02),'rare':('🔵 Rare Chest',0.008),'epic':('🟣 Epic Chest',0.003),'legendary':('🟡 Legendary Chest',0.0008),'mythical':('🌈 Mythical Chest',0.0002)}
ACHIEVEMENTS = {
    'hunter10':('🐾 First Pack','Catch 10 pets',10,'hunt',500),
    'legendary':('👑 Legendary Hunter','Find a Legendary pet',1,'legendary',2500),
    'mythical':('🌟 Myth Hunter','Find a Mythical pet',1,'mythical',10000),
    'boss10':('👹 Boss Slayer','Defeat 10 bosses',10,'boss_kill',5000),
    'coins100k':('💰 Treasure Hoarder','Earn 100,000 Soul Coins',100000,'earned',7500),
    'streak30':('🔥 Unbreakable','Reach a 30-day streak',30,'streak',10000),
}

def init_v4():
    con=db(); c=con.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS inventory (guild_id INTEGER,user_id INTEGER,item TEXT,qty INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id,item))')
    c.execute('CREATE TABLE IF NOT EXISTS equipped_items (guild_id INTEGER,user_id INTEGER,slot TEXT,item TEXT,PRIMARY KEY(guild_id,user_id,slot))')
    c.execute('CREATE TABLE IF NOT EXISTS achievements (guild_id INTEGER,user_id INTEGER,aid TEXT,claimed INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id,aid))')
    c.execute('CREATE TABLE IF NOT EXISTS stats (guild_id INTEGER,user_id INTEGER,hunts INTEGER DEFAULT 0,boss_kills INTEGER DEFAULT 0,battles_won INTEGER DEFAULT 0,battles_lost INTEGER DEFAULT 0,gambles_won INTEGER DEFAULT 0,gambles_lost INTEGER DEFAULT 0,duels_won INTEGER DEFAULT 0,duels_lost INTEGER DEFAULT 0,dungeon_clears INTEGER DEFAULT 0,soul_earned INTEGER DEFAULT 0,started TEXT,PRIMARY KEY(guild_id,user_id))')
    for col, definition in [('started','TEXT'),('duels_won','INTEGER DEFAULT 0'),('duels_lost','INTEGER DEFAULT 0'),('dungeon_clears','INTEGER DEFAULT 0')]:
        try: c.execute(f'ALTER TABLE stats ADD COLUMN {col} {definition}')
        except sqlite3.OperationalError: pass
    for col, definition in [('duels_won','INTEGER DEFAULT 0'),('duels_lost','INTEGER DEFAULT 0'),('dungeon_clears','INTEGER DEFAULT 0')]:
        try: c.execute(f'ALTER TABLE stats ADD COLUMN {col} {definition}')
        except sqlite3.OperationalError: pass
    c.execute('CREATE TABLE IF NOT EXISTS areas (guild_id INTEGER,user_id INTEGER,area TEXT DEFAULT "dark_forest",PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS prestige (guild_id INTEGER,user_id INTEGER,prestige INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS clans (guild_id INTEGER,clan_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,owner_id INTEGER,level INTEGER DEFAULT 1,bank INTEGER DEFAULT 0,xp INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS clan_members (guild_id INTEGER,clan_id INTEGER,user_id INTEGER,PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS market (listing_id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER,seller_id INTEGER,kind TEXT,item TEXT,qty INTEGER,price INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS world_events (guild_id INTEGER PRIMARY KEY,event TEXT,ends TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admin_users (guild_id INTEGER,user_id INTEGER,PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS pet_slot_upgrades (guild_id INTEGER,user_id INTEGER,slots INTEGER DEFAULT 1,PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS command_cooldowns (guild_id INTEGER,user_id INTEGER,command TEXT,used_at TEXT,PRIMARY KEY(guild_id,user_id,command))')
    c.execute('CREATE TABLE IF NOT EXISTS dungeon_progress (guild_id INTEGER,user_id INTEGER,floor INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id))')
    c.execute('CREATE TABLE IF NOT EXISTS daily_missions (guild_id INTEGER,user_id INTEGER,mid INTEGER,day TEXT,progress INTEGER DEFAULT 0,claimed INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id,mid,day))')
    c.execute('CREATE TABLE IF NOT EXISTS clan_bosses (guild_id INTEGER,clan_id INTEGER,hp INTEGER,max_hp INTEGER,week_key TEXT,defeated INTEGER DEFAULT 0,PRIMARY KEY(guild_id,clan_id))')
    c.execute('CREATE TABLE IF NOT EXISTS clan_boss_attacks (guild_id INTEGER,clan_id INTEGER,user_id INTEGER,last_attack TEXT,PRIMARY KEY(guild_id,clan_id,user_id))')
    con.commit(); con.close()

# Call V4 DB setup before the bot starts.
init_db(); init_v4()

def ensure_stats(gid,uid):
    con=db(); con.execute('INSERT OR IGNORE INTO stats(guild_id,user_id,started) VALUES(?,?,?)',(gid,uid,datetime.now(timezone.utc).isoformat())); con.commit(); con.close()

def stat_inc(gid,uid,field,amount=1):
    ensure_stats(gid,uid); con=db(); con.execute(f'UPDATE stats SET {field}={field}+? WHERE guild_id=? AND user_id=?',(amount,gid,uid)); con.commit(); con.close()

def inv_add(gid,uid,item,qty=1):
    con=db(); con.execute('INSERT INTO inventory(guild_id,user_id,item,qty) VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id,item) DO UPDATE SET qty=qty+excluded.qty',(gid,uid,item,qty)); con.commit(); con.close()

def equipped_bonuses(gid,uid):
    con=db(); rows=con.execute('SELECT item FROM equipped_items WHERE guild_id=? AND user_id=?',(gid,uid)).fetchall(); con.close()
    attack=defense=0
    for r in rows:
        item=r['item']
        if item in ITEMS:
            _,kind,bonus,_=ITEMS[item]
            if kind=='weapon': attack += bonus
            elif kind=='armor': defense += bonus
    # Crafted weapon is the user's currently equipped weapon.
    con=db(); crafted=con.execute('SELECT attack_bonus FROM crafted_weapons WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); con.close()
    if crafted: attack += crafted['attack_bonus']
    return attack, defense

def weapon_proc(gid, uid, base_damage):
    """Apply the currently crafted weapon's special proc in boss combat."""
    con=db(); row=con.execute('SELECT weapon,ability,attack_bonus FROM crafted_weapons WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); con.close()
    if not row: return base_damage, ''
    weapon=row['weapon']; proc_bonus=0; note=''
    chances={'Iron Reaper':(.15, 'Reaper’s Mark'), 'Venom Fang':(.20, 'Poison Bite'), 'Frostmourne Edge':(.15, 'Frozen Strike'), 'Stormbreaker Axe':(.20, 'Thunderclap'), 'Voidbreaker':(.15, 'Void Surge'), 'Sunpiercer':(.15, 'Solar Burst'), 'Bloodmoon Greatsword':(.20, 'Blood Frenzy'), 'Astral Devourer':(.12, 'Starfall'), 'Soulforge Obliterator':(.10, 'Soul Annihilation')}
    bonuses={'Iron Reaper':row['attack_bonus'], 'Frostmourne Edge':40, 'Stormbreaker Axe':60, 'Voidbreaker':100, 'Sunpiercer':120, 'Bloodmoon Greatsword':50, 'Astral Devourer':180, 'Soulforge Obliterator':250}
    if weapon=='Emberblade':
        con=db(); con.execute('CREATE TABLE IF NOT EXISTS weapon_counters(guild_id INTEGER,user_id INTEGER,count INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id))')
        con.execute('INSERT OR IGNORE INTO weapon_counters VALUES(?,?,0)',(gid,uid)); con.execute('UPDATE weapon_counters SET count=count+1 WHERE guild_id=? AND user_id=?',(gid,uid)); count=con.execute('SELECT count FROM weapon_counters WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()['count']; con.commit(); con.close()
        if count%3==0: return base_damage+50, '🔥 Inferno triggered: +50 damage!'
    if weapon=='Venom Fang':
        con=db()
        con.execute('CREATE TABLE IF NOT EXISTS weapon_poison(guild_id INTEGER,user_id INTEGER,attacks_left INTEGER DEFAULT 0,PRIMARY KEY(guild_id,user_id))')
        con.execute('INSERT OR IGNORE INTO weapon_poison VALUES(?,?,0)',(gid,uid))
        pending=con.execute('SELECT attacks_left FROM weapon_poison WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()['attacks_left']
        if pending>0:
            con.execute('UPDATE weapon_poison SET attacks_left=attacks_left-1 WHERE guild_id=? AND user_id=?',(gid,uid))
            con.commit(); con.close()
            return base_damage+15, f'☠️ Venom poison dealt +15 damage! ({pending-1} poisoned attack(s) remain after this one).'
        if random.random()<.20:
            con.execute('UPDATE weapon_poison SET attacks_left=2 WHERE guild_id=? AND user_id=?',(gid,uid))
            con.commit(); con.close()
            return base_damage, '☠️ Poison Bite triggered: your next 2 attacks will deal +15 poison damage each!'
        con.close()
    if weapon in chances and random.random()<chances[weapon][0]:
        proc_bonus=bonuses.get(weapon,0); note=f'✨ {chances[weapon][1]} triggered: +{proc_bonus} damage!'
        return base_damage+proc_bonus, note
    return base_damage, ''

def inv_take(gid,uid,item,qty=1):
    con=db(); r=con.execute('SELECT qty FROM inventory WHERE guild_id=? AND user_id=? AND item=?',(gid,uid,item)).fetchone()
    if not r or r['qty']<qty: con.close(); return False
    con.execute('UPDATE inventory SET qty=qty-? WHERE guild_id=? AND user_id=? AND item=?',(qty,gid,uid,item)); con.commit(); con.close(); return True

def mission_inc(gid,uid,mid,amount=1):
    day=today_key(); con=db(); con.execute('INSERT INTO daily_missions(guild_id,user_id,mid,day,progress,claimed) VALUES(?,?,?,?,?,0) ON CONFLICT(guild_id,user_id,mid,day) DO UPDATE SET progress=progress+excluded.progress',(gid,uid,mid,day,amount)); con.commit(); con.close()

def rarity_pick(allowed):
    """Pick a pet rarity while keeping Mythical/Special genuinely rare."""
    allowed=list(allowed)
    if 'Special' in allowed and random.random() < 0.0001:
        return 'Special'
    if 'Mythical' in allowed and random.random() < 0.002:
        return 'Mythical'
    weights={'Common':6000,'Uncommon':2400,'Rare':900,'Epic':400,'Legendary':120,'Mythical':15,'Special':1}
    normal=[r for r in allowed if r not in ('Mythical','Special')]
    pool=normal or [r for r in allowed if r != 'Special'] or allowed
    total=sum(weights[r] for r in pool); roll=random.randint(1,total); acc=0
    for r in pool:
        acc += weights[r]
        if roll<=acc: return r
    return pool[0]

def current_event(gid):
    con=db(); r=con.execute('SELECT * FROM world_events WHERE guild_id=?',(gid,)).fetchone(); con.close()
    if not r: return None
    if datetime.fromisoformat(r['ends']) <= datetime.now(timezone.utc): return None
    return r

def admin_ok(interaction):
    # Only the bot creator's Discord User ID can use admin commands.
    return bool(OWNER_ID and interaction.user.id == OWNER_ID)

@bot.tree.command(name='dungeon', description='Enter a 1-20 floor dungeon')
async def dungeon(interaction):
    if not await command_cooldown(interaction,'dungeon',5): return
    gid,uid=interaction.guild_id,interaction.user.id; get_user(gid,uid)
    con=db(); r=con.execute('SELECT floor FROM dungeon_progress WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); floor=(r['floor'] if r else 0)+1
    if floor>20: floor=1
    enemy=random.choice(['Cursed Goblin','Frost Wraith','Inferno Hound','Void Knight','Abyss Beast'])
    hp=30+floor*22
    if floor == 20:
        enemy = random.choice(['👑 Dungeon Overlord','☠️ Cursed Colossus','🌌 Void Warden'])
        hp += 300
    u=get_user(gid,uid); item_atk,item_def=equipped_bonuses(gid,uid); power=u['attack']+item_atk+pet_power(gid,uid)+random.randint(0,max(1,u['luck']))+item_def//2
    if power+random.randint(0,40) < hp:
        await interaction.response.send_message(f'🏰 **Floor {floor}/20** — {enemy}\n💀 You were defeated. Train up and try again!')
        return
    coins=random.randint(60+floor*20,120+floor*60); xp=random.randint(30+floor*8,70+floor*15)
    money(gid,uid,coins); add_xp(gid,uid,xp)
    if random.random()<0.18: inv_add(gid,uid,random.choice(['pet_core','evolution_shard','small_potion','large_potion']))
    if floor==20: inv_add(gid,uid,'legendary_chest'); floor=0
    stat_inc(gid,uid,'dungeon_clears')
    con=db(); con.execute('INSERT INTO dungeon_progress(guild_id,user_id,floor) VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET floor=excluded.floor',(gid,uid,floor)); con.commit(); con.close()
    await interaction.response.send_message(f'🏰 **Floor {20 if floor==0 else floor}/20 CLEARED!** 👹 {enemy}\n🖤🪙 +{coins:,} Soul Coins • ✨ +{xp} XP\n🔮 You may have found loot!')

@bot.tree.command(name='areas', description='View hunting areas')
async def areas(interaction):
    await interaction.response.send_message('🗺️ **AREAS**\n' + '\n'.join(f'`{k}` — {v["name"]}' for k,v in AREAS.items()) + '\nUse `/travel area:<name>` then `/explore`.')

@bot.tree.command(name='travel', description='Travel to a hunting area')
@app_commands.describe(area='dark_forest, frozen_lands, inferno, void, cursed_realm')
async def travel(interaction, area:str):
    area=area.lower().strip()
    if area not in AREAS: return await interaction.response.send_message('❌ Invalid area. Use `/areas`.',ephemeral=True)
    con=db(); con.execute('INSERT INTO areas(guild_id,user_id,area) VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET area=excluded.area',(interaction.guild_id,interaction.user.id,area)); con.commit(); con.close()
    await interaction.response.send_message(f'🗺️ You travelled to **{AREAS[area]["name"]}**. Use `/explore` to search it.')

@bot.tree.command(name='explore', description='Explore your current area for loot, enemies and pets')
async def explore(interaction):
    if not await command_cooldown(interaction,'explore',5): return
    gid,uid=interaction.guild_id,interaction.user.id; u=get_user(gid,uid); con=db(); r=con.execute('SELECT area FROM areas WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); con.close(); area=r['area'] if r else 'dark_forest'; a=AREAS[area]
    ev=current_event(gid); mult=2 if ev and ev['event']=='blood_moon' else 1
    coins=random.randint(*a['coins'])*mult; xp=random.randint(*a['xp'])*mult; mission_inc(gid,uid,1); money(gid,uid,coins); add_xp(gid,uid,xp)
    if random.random()<0.22:
        rarity=rarity_pick(a['rarities']); name=random.choice(PET_NAMES[rarity]); pid=db().execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()['n']+1
        con=db(); con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)',(gid,uid,pid,name,rarity,PET_DAMAGE[name],1)); con.commit(); con.close()
        await interaction.response.send_message(f'{a["name"]} → 🐾 Found {RARITIES[rarity]["emoji"]} **{rarity} {name}**!\n🖤🪙 +{coins:,} Soul Coins • ✨ +{xp} XP')
    else:
        await interaction.response.send_message(f'{a["name"]} → ⚔️ You survived the wild.\n🖤🪙 +{coins:,} Soul Coins • ✨ +{xp} XP')

@bot.tree.command(name='inventory', description='View your items')
async def inventory(interaction):
    con=db(); rows=con.execute('SELECT item,qty FROM inventory WHERE guild_id=? AND user_id=? AND qty>0 ORDER BY item',(interaction.guild_id,interaction.user.id)).fetchall(); con.close()
    if not rows: return await interaction.response.send_message('🎒 Your inventory is empty.')
    await interaction.response.send_message('🎒 **INVENTORY**\n'+'\n'.join(f'{ITEMS.get(r["item"],(r["item"],))[0]} × **{r["qty"]}**' for r in rows))

@bot.tree.command(name='equip_item', description='Equip a weapon or armor')
@app_commands.describe(item='Item key from /inventory')
async def equip_item(interaction,item:str):
    if item not in ITEMS or ITEMS[item][1] not in ('weapon','armor'): return await interaction.response.send_message('❌ That item cannot be equipped.',ephemeral=True)
    con=db(); owned=con.execute('SELECT qty FROM inventory WHERE guild_id=? AND user_id=? AND item=?',(interaction.guild_id,interaction.user.id,item)).fetchone(); con.close()
    if not owned or owned['qty'] < 1: return await interaction.response.send_message('❌ You do not have that item.',ephemeral=True)
    slot=ITEMS[item][1]; con=db(); con.execute('INSERT OR REPLACE INTO equipped_items VALUES(?,?,?,?)',(interaction.guild_id,interaction.user.id,slot,item)); con.commit(); con.close()
    await interaction.response.send_message(f'⚔️ Equipped **{ITEMS[item][0]}**.')

@bot.tree.command(name='achievements', description='View achievements')
async def achievements(interaction):
    con=db(); claimed={r['aid'] for r in con.execute('SELECT aid FROM achievements WHERE guild_id=? AND user_id=? AND claimed=1',(interaction.guild_id,interaction.user.id)).fetchall()}; con.close()
    await interaction.response.send_message('🏆 **ACHIEVEMENTS**\n'+'\n'.join(f'{"✅" if k in claimed else "⬜"} **{v[0]}** — {v[1]} • 🖤🪙 {v[4]:,}' for k,v in ACHIEVEMENTS.items()))

@bot.tree.command(name='stats', description='View lifetime statistics')
async def stats(interaction):
    ensure_stats(interaction.guild_id,interaction.user.id); con=db(); r=con.execute('SELECT * FROM stats WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone(); p=con.execute('SELECT COUNT(*) n FROM pets WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()['n']; con.close()
    await interaction.response.send_message(f'📊 **{interaction.user.display_name} STATS**\n🐾 Pets collected: **{p}**\n🌲 Hunts: **{r["hunts"]}**\n👹 Boss kills: **{r["boss_kills"]}**\n⚔️ Pet battles W/L: **{r["battles_won"]}/{r["battles_lost"]}**\n🎰 Gambling W/L: **{r["gambles_won"]}/{r["gambles_lost"]}**\n⚔️ Duels W/L: **{r["duels_won"]}/{r["duels_lost"]}**\n🏰 Dungeon clears: **{r["dungeon_clears"]}**\n🔥 Highest/current streak: **{get_user(interaction.guild_id,interaction.user.id)["daily_streak"]}**\n🖤🪙 Soul Coins earned: **{r["soul_earned"]:,}**\n⏱️ Playing since: **<t:{int(datetime.fromisoformat(r["started"] or datetime.now(timezone.utc).isoformat()).timestamp())}:R>**')

@bot.tree.command(name='open_chest', description='Open a chest')
@app_commands.describe(chest='basic, rare, epic, legendary or mythical')
async def open_chest(interaction,chest:str):
    chest=chest.lower().strip()
    if chest not in CHESTS: return await interaction.response.send_message('❌ Invalid chest type.',ephemeral=True)
    if not inv_take(interaction.guild_id,interaction.user.id,chest+'_chest',1): return await interaction.response.send_message('❌ You do not have that chest.',ephemeral=True)
    roll=random.random(); name=None
    if roll < 0.0002: rarity='Special'
    elif roll < 0.001: rarity='Mythical'
    elif roll < 0.008: rarity='Legendary'
    elif roll < 0.05: rarity='Epic'
    else: rarity='Rare'
    if rarity=='Special' and random.random()<0.1: name='Wither Storm'
    else: name=random.choice(PET_NAMES[rarity])
    if random.random()<0.65: inv_add(interaction.guild_id,interaction.user.id,'pet_core',random.randint(1,3))
    con=db(); pid=con.execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()['n']+1; con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)',(interaction.guild_id,interaction.user.id,pid,name,rarity,PET_DAMAGE.get(name,random.randint(*RARITIES[rarity]['base'])),1)); con.commit(); con.close()
    await interaction.response.send_message(f'🎁 **{CHESTS[chest][0]} OPENED!**\nYou found {RARITIES[rarity]["emoji"]} **{rarity} {name}**!')

@bot.tree.command(name='missions', description='View daily missions')
async def missions(interaction):
    day=today_key(); con=db();
    data=[(1,'Explore 3 times','explore',3,800,150),(2,'Win 2 pet battles','battle',2,1200,250),(3,'Earn 3000 Soul Coins','coins',3000,1500,300)]
    lines=[]
    for mid,name,ev,target,reward,xp in data:
        row=con.execute('SELECT progress,claimed FROM daily_missions WHERE guild_id=? AND user_id=? AND mid=? AND day=?',(interaction.guild_id,interaction.user.id,mid,day)).fetchone(); p=row['progress'] if row else 0; cl=row['claimed'] if row else 0
        lines.append(f'`{mid}` {name} — **{min(p,target)}/{target}** {"✅" if cl else ""} • 🖤🪙 {reward:,}')
    con.close(); await interaction.response.send_message('🎁 **DAILY MISSIONS**\n'+'\n'.join(lines)+'\nUse `/mission_claim mission_id:<id>`.')

@bot.tree.command(name='mission_claim', description='Claim a completed daily mission')
async def mission_claim(interaction,mission_id:int):
    data={1:('Explore 3 times',3,800,150),2:('Win 2 pet battles',2,1200,250),3:('Earn 3000 Soul Coins',3000,1500,300)}
    if mission_id not in data: return await interaction.response.send_message('❌ Invalid mission.',ephemeral=True)
    name,target,reward,xp=data[mission_id]; day=today_key(); con=db(); r=con.execute('SELECT progress,claimed FROM daily_missions WHERE guild_id=? AND user_id=? AND mid=? AND day=?',(interaction.guild_id,interaction.user.id,mission_id,day)).fetchone()
    if not r or r['progress']<target or r['claimed']: con.close(); return await interaction.response.send_message('❌ Mission is not complete or already claimed.',ephemeral=True)
    con.execute('UPDATE daily_missions SET claimed=1 WHERE guild_id=? AND user_id=? AND mid=? AND day=?',(interaction.guild_id,interaction.user.id,mission_id,day)); con.commit(); con.close(); money(interaction.guild_id,interaction.user.id,reward); add_xp(interaction.guild_id,interaction.user.id,xp); await interaction.response.send_message(f'🎉 **{name}** claimed! 🖤🪙 +{reward:,} • ✨ +{xp} XP')

@bot.tree.command(name='daily_shop', description='View rotating shop')
async def daily_shop(interaction):
    seed=int(today_key().replace('-','')); rng=random.Random(seed+interaction.guild_id); keys=rng.sample(list(ITEMS.keys()),4)
    await interaction.response.send_message('🏪 **ROTATING SHOP — 24H**\n'+'\n'.join(f'`{k}` {ITEMS[k][0]} — 🖤🪙 {ITEMS[k][3]:,}' for k in keys)+'\nUse `/buy_shop item:<key>`.')

@bot.tree.command(name='buy_shop', description='Buy an item from the rotating shop')
async def buy_shop(interaction,item:str):
    seed=int(today_key().replace('-','')); rng=random.Random(seed+interaction.guild_id); keys=rng.sample(list(ITEMS.keys()),4)
    if item not in keys: return await interaction.response.send_message('❌ That item is not in today’s shop.',ephemeral=True)
    price=ITEMS[item][3]; u=get_user(interaction.guild_id,interaction.user.id)
    if u['cash']<price: return await interaction.response.send_message('❌ Not enough Soul Coins.',ephemeral=True)
    money(interaction.guild_id,interaction.user.id,-price); inv_add(interaction.guild_id,interaction.user.id,item,1); await interaction.response.send_message(f'🛒 Bought **{ITEMS[item][0]}** for 🖤🪙 {price:,}.')

@bot.tree.command(name='world_event', description='View the current world event')
async def world_event(interaction):
    ev=current_event(interaction.guild_id)
    if not ev: return await interaction.response.send_message('🌙 No world event is active right now.')
    await interaction.response.send_message(f'🌑 **BLOOD MOON!** Hunt/explore rewards are boosted until <t:{int(datetime.fromisoformat(ev["ends"]).timestamp())}:R>.')

@bot.tree.command(name='clan_create', description='Create a clan')
async def clan_create(interaction,name:str):
    if len(name)>24: return await interaction.response.send_message('❌ Name too long.',ephemeral=True)
    con=db(); own=con.execute('SELECT clan_id FROM clan_members WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()
    if own: con.close(); return await interaction.response.send_message('❌ You are already in a clan.',ephemeral=True)
    try:
        cur=con.execute('INSERT INTO clans(guild_id,name,owner_id) VALUES(?,?,?)',(interaction.guild_id,name,interaction.user.id)); cid=cur.lastrowid; con.execute('INSERT INTO clan_members VALUES(?,?,?)',(interaction.guild_id,cid,interaction.user.id)); con.commit()
    except sqlite3.IntegrityError: con.close(); return await interaction.response.send_message('❌ Clan name already exists.',ephemeral=True)
    con.close(); await interaction.response.send_message(f'👑 Clan **{name}** created!')

@bot.tree.command(name='clan_join', description='Join a clan')
async def clan_join(interaction,clan_name:str):
    con=db(); c=con.execute('SELECT * FROM clans WHERE guild_id=? AND lower(name)=lower(?)',(interaction.guild_id,clan_name)).fetchone(); own=con.execute('SELECT clan_id FROM clan_members WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()
    if not c or own: con.close(); return await interaction.response.send_message('❌ Clan not found or you are already in a clan.',ephemeral=True)
    con.execute('INSERT INTO clan_members VALUES(?,?,?)',(interaction.guild_id,c['clan_id'],interaction.user.id)); con.commit(); con.close(); await interaction.response.send_message(f'🤝 Joined **{c["name"]}**!')

@bot.tree.command(name='clan_info', description='View your clan')
async def clan_info(interaction):
    con=db(); m=con.execute('SELECT clan_id FROM clan_members WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone()
    if not m: con.close(); return await interaction.response.send_message('❌ You are not in a clan.',ephemeral=True)
    c=con.execute('SELECT * FROM clans WHERE clan_id=?',(m['clan_id'],)).fetchone(); n=con.execute('SELECT COUNT(*) n FROM clan_members WHERE clan_id=?',(m['clan_id'],)).fetchone()['n']; con.close(); await interaction.response.send_message(f'👑 **{c["name"]}**\nLevel: **{c["level"]}** • Members: **{n}**\n🏦 Bank: 🖤🪙 {c["bank"]:,}')

@bot.tree.command(name='clan_contribute', description='Contribute Soul Coins to your clan')
async def clan_contribute(interaction,amount:app_commands.Range[int,100,100000]):
    con=db(); m=con.execute('SELECT clan_id FROM clan_members WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone(); con.close()
    if not m: return await interaction.response.send_message('❌ Join a clan first.',ephemeral=True)
    u=get_user(interaction.guild_id,interaction.user.id)
    if u['cash']<amount: return await interaction.response.send_message('❌ Not enough Soul Coins.',ephemeral=True)
    money(interaction.guild_id,interaction.user.id,-amount); con=db(); con.execute('UPDATE clans SET bank=bank+?,xp=xp+? WHERE clan_id=?',(amount,amount,m['clan_id'])); con.commit(); con.close(); await interaction.response.send_message(f'🏦 Contributed 🖤🪙 {amount:,} Soul Coins to your clan.')

@bot.tree.command(name='market', description='View player market listings')
async def market(interaction):
    con=db(); rows=con.execute('SELECT * FROM market WHERE guild_id=? ORDER BY listing_id DESC LIMIT 15',(interaction.guild_id,)).fetchall(); con.close()
    if not rows: return await interaction.response.send_message('🎟️ Market is empty.')
    await interaction.response.send_message('🎟️ **PLAYER MARKET**\n'+'\n'.join(f'`{r["listing_id"]}` {r["item"]} ×{r["qty"]} — 🖤🪙 {r["price"]:,} — Seller <@{r["seller_id"]}>' for r in rows))

@bot.tree.command(name='market_list', description='List an inventory item on the market')
async def market_list(interaction,item:str,qty:app_commands.Range[int,1,100],price:app_commands.Range[int,1,1000000]):
    con=db(); equipped=con.execute('SELECT 1 FROM equipped_items WHERE guild_id=? AND user_id=? AND item=? LIMIT 1',(interaction.guild_id,interaction.user.id,item)).fetchone(); con.close()
    if equipped: return await interaction.response.send_message('❌ Unequip this item before listing it on the market.',ephemeral=True)
    if not inv_take(interaction.guild_id,interaction.user.id,item,qty): return await interaction.response.send_message('❌ You do not have enough of that item.',ephemeral=True)
    con=db(); con.execute('INSERT INTO market(guild_id,seller_id,kind,item,qty,price) VALUES(?,?,?,?,?,?)',(interaction.guild_id,interaction.user.id,'item',item,qty,price)); con.commit(); lid=con.execute('SELECT last_insert_rowid() id').fetchone()['id']; con.close(); await interaction.response.send_message(f'🎟️ Listed `{item}` ×{qty} for 🖤🪙 {price:,}. Listing ID: **{lid}**')

@bot.tree.command(name='market_buy', description='Buy a market listing')
async def market_buy(interaction,listing_id:int):
    con=db(); r=con.execute('SELECT * FROM market WHERE listing_id=? AND guild_id=?',(listing_id,interaction.guild_id)).fetchone()
    if not r: con.close(); return await interaction.response.send_message('❌ Listing not found.',ephemeral=True)
    if r['seller_id']==interaction.user.id: con.close(); return await interaction.response.send_message('❌ You cannot buy your own listing.',ephemeral=True)
    u=get_user(interaction.guild_id,interaction.user.id)
    if u['cash']<r['price']: con.close(); return await interaction.response.send_message('❌ Not enough Soul Coins.',ephemeral=True)
    money(interaction.guild_id,interaction.user.id,-r['price']); money(interaction.guild_id,r['seller_id'],r['price']); inv_add(interaction.guild_id,interaction.user.id,r['item'],r['qty']); con.execute('DELETE FROM market WHERE listing_id=?',(listing_id,)); con.commit(); con.close(); await interaction.response.send_message(f'🛍️ Bought `{r["item"]}` ×{r["qty"]} for 🖤🪙 {r["price"]:,}.')

@bot.tree.command(name='prestige', description='Prestige at level 100 for a permanent XP bonus')
async def prestige_cmd(interaction):
    u=get_user(interaction.guild_id,interaction.user.id)
    if u['level']<100: return await interaction.response.send_message(f'❌ You need Level 100. You are Level {u["level"]}.',ephemeral=True)
    con=db(); r=con.execute('SELECT prestige FROM prestige WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone(); p=(r['prestige'] if r else 0)+1; con.execute('INSERT INTO prestige(guild_id,user_id,prestige) VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET prestige=excluded.prestige',(interaction.guild_id,interaction.user.id,p)); con.execute('UPDATE users SET level=1,xp=0 WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)); con.commit(); con.close(); await interaction.response.send_message(f'🔥 **PRESTIGE {p}!** Level reset to 1. Permanent XP bonus: **+{p*5}%**.')

@bot.tree.command(name='tip', description='Get a random gameplay progression tip')
async def tip(interaction):
    tips=["⛏️ Mine often: Crystal Shards, Ember Cores and Void Fragments unlock stronger weapon recipes.","🐾 Hunt for pets, then upgrade duplicate pets to improve their damage.","⚔️ Check `/weapon_list` and `/weapon_recipe` before spending crafting materials.","👹 Coordinate with the server to defeat the daily and weekly bosses for rewards.","🏰 Try dungeons as your level and gear improve; higher floors are tougher.","🎁 Claim `/daily` rewards regularly and keep your streak alive.","🛡️ Use `/shop` to improve your combat stats before harder fights.","📜 Check `/quests`, `/missions` and `/achievements` for extra progression rewards."]
    await interaction.response.send_message(random.choice(tips))

@bot.tree.command(name='weapon_list', description='List all craftable weapons')
async def weapon_list(interaction):
    lines=[]
    for name,w in WEAPONS.items():
        lines.append(f"⚔️ **{name}** — +{w['bonus']} damage\n   {w['ability']}")
    await interaction.response.send_message('**⚒️ SoulForge Weapon Codex**\n'+'\n'.join(lines),ephemeral=True)

@bot.tree.command(name='weapon_recipe', description='View a weapon recipe, damage and ability')
@app_commands.choices(weapon=[app_commands.Choice(name=n,value=n) for n in WEAPONS])
async def weapon_recipe(interaction, weapon:app_commands.Choice[str]):
    w=WEAPONS[weapon.value]
    costs='\n'.join(f'{mat} ×{qty}' for mat,qty in w['cost'].items())
    await interaction.response.send_message(f"**⚔️ {weapon.value}**\nDamage bonus: **+{w['bonus']}**\nAbility: {w['ability']}\n\n**Crafting recipe**\n{costs}",ephemeral=True)

@bot.tree.command(name='pet_info', description='View detailed information about one of your pets')
@app_commands.describe(pet_id='Pet ID shown by /pets')
async def pet_info(interaction, pet_id:int):
    con=db(); pet=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(interaction.guild_id,interaction.user.id,pet_id)).fetchone(); con.close()
    if not pet: return await interaction.response.send_message('❌ Pet not found. Use `/pets` to check IDs.',ephemeral=True)
    icon=PET_EMOJIS.get(pet['name'],RARITIES[pet['rarity']]['emoji'])
    await interaction.response.send_message(f"{icon} **{pet['name']}**\nRarity: **{pet['rarity']}** • Level **{pet['pet_level']}/50**\n❤️ HP: **{100+pet['pet_level']*10}**\n⚔️ Damage: **{pet['damage']+(pet['pet_level']-1)*5}**\n✨ Level up or evolve pets to improve their power.",ephemeral=True)

PET_SLOT_COSTS=[(5,2000,{'🪨 Iron Ore':10}),(10,7500,{'🪨 Iron Ore':20,'💎 Crystal Shard':5}),(20,20000,{'💎 Crystal Shard':10,'🔥 Ember Core':5}),(35,50000,{'💎 Crystal Shard':15,'🔥 Ember Core':10,'🌑 Void Fragment':3})]
@bot.tree.command(name='pet_upgrade_info', description='View requirements for the next pet slot')
async def pet_upgrade_info(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); con=db(); r=con.execute('SELECT slots FROM pet_slot_upgrades WHERE guild_id=? AND user_id=?',(interaction.guild_id,interaction.user.id)).fetchone(); con.close(); slots=r['slots'] if r else 1
    if slots>=5: return await interaction.response.send_message('🐾 You already have all 5 pet slots unlocked!',ephemeral=True)
    lvl,cost,mats=PET_SLOT_COSTS[slots-1]; req=', '.join(f'{k} ×{v}' for k,v in mats.items())
    await interaction.response.send_message(f'🔓 **Pet Slot Upgrade {slots} → {slots+1}**\nRequired level: **{lvl}** (you: {u["level"]})\nCost: **{cost:,} Soul Coins**\nMaterials: {req}\nUse `/pet_upgrade_slots` to purchase.',ephemeral=True)

@bot.tree.command(name='pet_upgrade_slots', description='Unlock one additional pet equip slot')
async def pet_upgrade_slots(interaction):
    u=get_user(interaction.guild_id,interaction.user.id); gid,uid=interaction.guild_id,interaction.user.id; con=db(); r=con.execute('SELECT slots FROM pet_slot_upgrades WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); slots=r['slots'] if r else 1
    if slots>=5: con.close(); return await interaction.response.send_message('🐾 You already have all 5 pet slots unlocked!',ephemeral=True)
    lvl,cost,mats=PET_SLOT_COSTS[slots-1]
    if u['level']<lvl: con.close(); return await interaction.response.send_message(f'❌ You need player level {lvl}. Current level: {u["level"]}.',ephemeral=True)
    if u['cash']<cost: con.close(); return await interaction.response.send_message(f'❌ You need {cost:,} Soul Coins.',ephemeral=True)
    inv={x['ore']:x['amount'] for x in con.execute('SELECT ore,amount FROM mining WHERE guild_id=? AND user_id=?',(gid,uid)).fetchall()}
    missing=[f'{k} ×{v}' for k,v in mats.items() if inv.get(k,0)<v]
    if missing: con.close(); return await interaction.response.send_message('❌ Missing materials: '+', '.join(missing),ephemeral=True)
    con.execute('UPDATE users SET cash=cash-? WHERE guild_id=? AND user_id=?',(cost,gid,uid))
    for k,v in mats.items(): con.execute('UPDATE mining SET amount=amount-? WHERE guild_id=? AND user_id=? AND ore=?',(v,gid,uid,k))
    con.execute('INSERT INTO pet_slot_upgrades VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET slots=excluded.slots',(gid,uid,slots+1)); con.commit(); con.close()
    await interaction.response.send_message(f'🔓 **Pet slot unlocked!** You can now equip **{slots+1} pets**.\nPaid {cost:,} Soul Coins and required crafting materials.')

@bot.tree.command(name='admin_setup', description='Server owner: make yourself a bot admin')
async def admin_setup(interaction):
    if interaction.guild_id is None or not OWNER_ID or interaction.user.id != OWNER_ID: return await interaction.response.send_message('❌ You are not authorized to use the bot admin system.',ephemeral=True)
    con=db(); con.execute('INSERT OR IGNORE INTO admin_users VALUES(?,?)',(interaction.guild_id,interaction.user.id)); con.commit(); con.close(); await interaction.response.send_message('👑 **Admin access enabled for you.** Use `/admin` to see admin tools.',ephemeral=True)

@bot.tree.command(name='admin', description='Open bot admin tools')
async def admin(interaction):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin access required. Server owner can use `/admin_setup` first.',ephemeral=True)
    cmds=sorted((c for c in bot.tree.get_commands() if c.name.startswith('admin')), key=lambda c:c.name)
    lines=[f"`/{c.name}` — {c.description or 'Admin command'}" for c in cmds]
    pages=[lines[i:i+15] for i in range(0,len(lines),15)] or [["No admin commands registered."]]
    await interaction.response.send_message("🛠️ **ADMIN PANEL**\\n"+ "\\n".join(pages[0]),ephemeral=True)

@bot.tree.command(name='admin_event', description='Admin: start a Blood Moon event')
async def admin_event(interaction):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    ends=datetime.now(timezone.utc)+timedelta(hours=1); con=db(); con.execute('INSERT OR REPLACE INTO world_events VALUES(?,?,?)',(interaction.guild_id,'blood_moon',ends.isoformat())); con.commit(); con.close(); await interaction.response.send_message('🌑 **BLOOD MOON STARTED!** 1 hour of boosted exploration rewards.')

@bot.tree.command(name='admin_give', description='Admin: give Soul Coins')
async def admin_give(interaction,member:discord.Member,amount:app_commands.Range[int,1,1000000]):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    money(interaction.guild_id,member.id,amount); await interaction.response.send_message(f'👑 Gave {member.mention} 🖤🪙 {amount:,} Soul Coins.')

@bot.tree.command(name='admin_give_item', description='Admin: give an inventory item')
async def admin_give_item(interaction,member:discord.Member,item:str,qty:app_commands.Range[int,1,100]):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    if item not in ITEMS and item not in [k+'_chest' for k in CHESTS]: return await interaction.response.send_message('❌ Unknown item.',ephemeral=True)
    inv_add(interaction.guild_id,member.id,item,qty); await interaction.response.send_message(f'👑 Gave {member.mention} `{item}` ×{qty}.')

@bot.tree.command(name='admin_boss_reset', description='Admin: reset the weekly boss')
async def admin_boss_reset(interaction):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    con=db(); con.execute('DELETE FROM bosses WHERE guild_id=?',(interaction.guild_id,)); con.commit(); con.close(); await boss_row(interaction.guild_id); await interaction.response.send_message('👹 Weekly boss reset.')


@bot.tree.command(name='admin_give_pet', description='Admin: grant a pet to a member')
@app_commands.describe(member='Recipient', rarity='Pet rarity')
@app_commands.choices(rarity=[app_commands.Choice(name=r,value=r) for r in PET_NAMES])
async def admin_give_pet(interaction, member:discord.Member, rarity:app_commands.Choice[str]):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    name=random.choice(PET_NAMES[rarity.value]); damage=PET_DAMAGE[name]; gid=interaction.guild_id
    con=db(); row=con.execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(gid,member.id)).fetchone(); pid=row['n']+1
    con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,1)',(gid,member.id,pid,name,rarity.value,damage)); con.commit(); con.close()
    await interaction.response.send_message(f'👑 Granted **{rarity.value} {name}** (+{damage} damage) to {member.mention}. Pet ID: `{pid}`.')

@bot.tree.command(name='admin_set_level', description='Admin: set a member level')
@app_commands.describe(member='Target member', level='Level to set (1-100)')
async def admin_set_level(interaction, member:discord.Member, level:app_commands.Range[int,1,100]):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    ensure_user(interaction.guild_id,member.id); con=db(); con.execute('UPDATE users SET level=?,xp=0 WHERE guild_id=? AND user_id=?',(level,interaction.guild_id,member.id)); con.commit(); con.close()
    await interaction.response.send_message(f'👑 Set {member.mention} to level **{level}** (XP reset to 0).')

@bot.tree.command(name='admin_reset_player', description='Admin: reset a member game profile')
@app_commands.describe(member='Target member')
async def admin_reset_player(interaction, member:discord.Member):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    gid,uid=interaction.guild_id,member.id; con=db()
    for table in ['users','pets','equipped','mining','crafted_weapons','inventory','equipped_items','stats','achievements','prestige','dungeon_progress','daily_missions','quest_progress','pet_slot_upgrades','command_cooldowns']:
        try: con.execute(f'DELETE FROM {table} WHERE guild_id=? AND user_id=?',(gid,uid))
        except sqlite3.OperationalError: pass
    con.commit(); con.close(); await interaction.response.send_message(f'⚠️ Reset {member.mention} game data for this server.')

@bot.tree.command(name='admin_daily_boss_reset', description='Admin: reset today’s daily boss')
async def admin_daily_boss_reset(interaction):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    con=db(); con.execute('DELETE FROM daily_bosses WHERE guild_id=?',(interaction.guild_id,)); con.commit(); con.close(); r=await daily_boss_row(interaction.guild_id)
    await interaction.response.send_message(f'👑 Daily boss reset: **{r["name"]}** ({r["hp"]:,} HP).')

@bot.tree.command(name='pet_evolve', description='Evolve a level 50 pet using duplicates and shards')
async def pet_evolve(interaction, pet_id:int):
    gid,uid=interaction.guild_id,interaction.user.id; con=db(); target=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(gid,uid,pet_id)).fetchone()
    if not target: con.close(); return await interaction.response.send_message('❌ Pet not found.',ephemeral=True)
    if target['pet_level'] < 50: con.close(); return await interaction.response.send_message('❌ This pet must be **Level 50** first.',ephemeral=True)
    dup=con.execute('SELECT * FROM pets WHERE guild_id=? AND user_id=? AND name=? AND pet_id!=? LIMIT 2',(gid,uid,target['name'],pet_id)).fetchall()
    if len(dup)<2: con.close(); return await interaction.response.send_message('❌ You need **2 duplicate copies** of this pet.',ephemeral=True)
    shards=con.execute('SELECT qty FROM inventory WHERE guild_id=? AND user_id=? AND item="evolution_shard"',(gid,uid)).fetchone()
    if not shards or shards['qty']<3: con.close(); return await interaction.response.send_message('❌ You need **3 Evolution Shards**.',ephemeral=True)
    new_name=target['name']+' Ascended'; new_damage=int(target['damage']*1.75)+25
    con.execute('UPDATE pets SET name=?,damage=? WHERE guild_id=? AND user_id=? AND pet_id=?',(new_name,new_damage,gid,uid,pet_id))
    for d in dup: con.execute('DELETE FROM pets WHERE guild_id=? AND user_id=? AND pet_id=?',(gid,uid,d['pet_id']))
    con.execute('UPDATE inventory SET qty=qty-3 WHERE guild_id=? AND user_id=? AND item="evolution_shard"',(gid,uid)); con.commit(); con.close()
    await interaction.response.send_message(f'🧬 **EVOLUTION COMPLETE!** {PET_EMOJIS.get(target["name"],RARITIES[target["rarity"]]["emoji"])} **{new_name}**\n⚔️ Damage: **{new_damage}** • Lv.50 MAX • Ascended Tier I')

@bot.tree.command(name='achievement_claim', description='Claim a completed achievement')
async def achievement_claim(interaction,achievement_id:str):
    if achievement_id not in ACHIEVEMENTS: return await interaction.response.send_message('❌ Invalid achievement ID.',ephemeral=True)
    gid,uid=interaction.guild_id,interaction.user.id; ensure_stats(gid,uid); name,desc,target,kind,reward=ACHIEVEMENTS[achievement_id]; con=db(); already=con.execute('SELECT claimed FROM achievements WHERE guild_id=? AND user_id=? AND aid=?',(gid,uid,achievement_id)).fetchone();
    if already and already['claimed']: con.close(); return await interaction.response.send_message('❌ Already claimed.',ephemeral=True)
    u=get_user(gid,uid); st=con.execute('SELECT * FROM stats WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone(); pets_count=con.execute('SELECT COUNT(*) n FROM pets WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()['n'];
    progress={'hunt':st['hunts'],'legendary':con.execute('SELECT COUNT(*) n FROM pets WHERE guild_id=? AND user_id=? AND rarity="Legendary"',(gid,uid)).fetchone()['n'],'mythical':con.execute('SELECT COUNT(*) n FROM pets WHERE guild_id=? AND user_id=? AND rarity="Mythical"',(gid,uid)).fetchone()['n'],'boss_kill':st['boss_kills'],'earned':st['soul_earned'],'streak':u['daily_streak']}[kind]
    if progress<target: con.close(); return await interaction.response.send_message(f'❌ Not complete yet: **{progress}/{target}**.',ephemeral=True)
    con.execute('INSERT INTO achievements VALUES(?,?,?,1) ON CONFLICT(guild_id,user_id,aid) DO UPDATE SET claimed=1',(gid,uid,achievement_id)); con.commit(); con.close(); money(gid,uid,reward); await interaction.response.send_message(f'🏆 **{name}** claimed! 🖤🪙 +{reward:,} Soul Coins.')

@bot.tree.command(name='clan_leaderboard', description='Clan leaderboard')
async def clan_leaderboard(interaction):
    con=db(); rows=con.execute('SELECT name,level,bank,xp FROM clans WHERE guild_id=? ORDER BY level DESC,xp DESC LIMIT 10',(interaction.guild_id,)).fetchall(); con.close();
    await interaction.response.send_message('👑 **CLAN LEADERBOARD**\n'+('\n'.join(f'**{i}.** {r["name"]} — Lv.{r["level"]} • 🖤🪙 {r["bank"]:,}' for i,r in enumerate(rows,1)) if rows else 'No clans yet.'))

@bot.tree.command(name='clan_boss', description='Fight your clan boss for clan XP and rewards')
async def clan_boss(interaction):
    gid,uid=interaction.guild_id,interaction.user.id
    con=db(); m=con.execute('SELECT clan_id FROM clan_members WHERE guild_id=? AND user_id=?',(gid,uid)).fetchone()
    if not m:
        con.close(); return await interaction.response.send_message('❌ Join a clan first.',ephemeral=True)
    cid=m['clan_id']; wk=week_key()
    r=con.execute('SELECT * FROM clan_bosses WHERE guild_id=? AND clan_id=?',(gid,cid)).fetchone()
    if not r or r['week_key'] != wk:
        con.execute('INSERT OR REPLACE INTO clan_bosses(guild_id,clan_id,hp,max_hp,week_key,defeated) VALUES(?,?,?,?,?,0)',(gid,cid,15000,15000,wk))
        r=con.execute('SELECT * FROM clan_bosses WHERE guild_id=? AND clan_id=?',(gid,cid)).fetchone()
    if r['defeated']:
        con.close(); return await interaction.response.send_message('🏆 Your clan already defeated this week\'s boss. Come back next week!',ephemeral=True)
    last=con.execute('SELECT last_attack FROM clan_boss_attacks WHERE guild_id=? AND clan_id=? AND user_id=?',(gid,cid,uid)).fetchone()
    con.close()
    if last and last['last_attack']:
        ok,left=cooldown_ok(last,'last_attack',30)
        if not ok: return await interaction.response.send_message(f'⏳ Clan boss attack cooldown: **{fmt_time(left)}**.',ephemeral=True)
    u=get_user(gid,uid); item_atk,_=equipped_bonuses(gid,uid)
    dmg=u['attack']+item_atk+pet_power(gid,uid)+random.randint(10,40)
    con=db(); con.execute('BEGIN IMMEDIATE')
    r=con.execute('SELECT * FROM clan_bosses WHERE guild_id=? AND clan_id=?',(gid,cid)).fetchone()
    if not r or r['defeated']:
        con.rollback(); con.close(); return await interaction.response.send_message('🏆 The clan boss is already defeated.',ephemeral=True)
    newhp=max(0,r['hp']-dmg); defeated=int(newhp==0)
    con.execute('UPDATE clan_bosses SET hp=?,defeated=? WHERE guild_id=? AND clan_id=? AND hp=? AND defeated=0',(newhp,defeated,gid,cid,r['hp']))
    con.execute('INSERT OR REPLACE INTO clan_boss_attacks VALUES(?,?,?,?)',(gid,cid,uid,datetime.now(timezone.utc).isoformat()))
    clan_reward=max(50,dmg//2); final_reward=10000 if defeated else 0
    con.execute('UPDATE clans SET bank=bank+?,xp=xp+? WHERE clan_id=?',(clan_reward+final_reward,dmg,cid))
    con.commit(); con.close()
    money(gid,uid,clan_reward + (1000 if defeated else 0)); add_xp(gid,uid,25 + (500 if defeated else 0))
    msg=f'👑 **CLAN BOSS ATTACK!**\n⚔️ Damage: **{dmg:,}**\n❤️ Boss HP: **{newhp:,}/{r["max_hp"]:,}**\n🏦 Clan bank: +🖤🪙 {clan_reward:,}'
    if defeated: msg += f'\n\n🏆 **CLAN BOSS DEFEATED!**\n🏦 Clan bonus: +🖤🪙 {final_reward:,}\n🎁 Your clear bonus: +🖤🪙 1,000 + 500 XP'
    await interaction.response.send_message(msg)

@bot.tree.command(name='admin_limited_pet', description='Admin: award a limited event pet')
async def admin_limited_pet(interaction,member:discord.Member,event:str):
    if not admin_ok(interaction): return await interaction.response.send_message('❌ Admin only.',ephemeral=True)
    key=event.title()
    if key not in LIMITED_PETS: return await interaction.response.send_message('❌ Event: Halloween, Christmas, Blood Moon, Anniversary.',ephemeral=True)
    name=LIMITED_PETS[key]; con=db(); pid=con.execute('SELECT COALESCE(MAX(pet_id),0) n FROM pets WHERE guild_id=? AND user_id=?',(interaction.guild_id,member.id)).fetchone()['n']+1; con.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)',(interaction.guild_id,member.id,pid,name,'Special',400,1)); con.commit(); con.close(); await interaction.response.send_message(f'👑 Awarded limited **{name}** to {member.mention}.')

# Limited event pets are intentionally not in normal hunt pools. They can be awarded by future events/admins.
LIMITED_PETS = {'Halloween':'🎃 Pumpkin Wraith','Christmas':'🎄 Frost Santa','Blood Moon':'🌑 Blood Moon Reaper','Anniversary':'🎂 Anniversary Dragon'}

# Re-sync after registering the V4 commands.
@bot.event
async def on_ready_v4_sync():
    pass

if not TOKEN: print('WARNING: DISCORD_TOKEN is missing')
else: bot.run(TOKEN)
