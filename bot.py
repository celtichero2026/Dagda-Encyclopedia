import os
import sqlite3
import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = os.getenv('GRIMOIRE_DB', 'grimoire.db')

ALIASES = {
    "smol": "smolach",
    "bt": "bloodthorn",
    "dhio": "dhiothu",
    "dino": "dhiothu",
    "gele": "gelebron",
    "prot": "proteus",
    "prime": "proteus prime",
    "base": "proteus base",
    "necro": "efnisien",
    "mord": "mordris",
    "hrung": "hrungnir",
    "crom": "crom",
}

BOSSES = {
    "mordris": {"id": 73000, "name": "Mordris", "aliases": ["mord"], "window": "20h - 36h"},
    "hrungnir": {"id": 73708, "name": "Hrungnir", "aliases": ["hrung"], "window": "22h - 38h"},
    "efnisien": {"id": 100002, "name": "Efnisien The Necromancer", "aliases": ["necro", "necromancer"], "window": "22h - 38h"},
    "gelebron": {"id": 102982, "name": "Gelebron", "aliases": ["gele"], "window": "32h - 60h"},
    "proteus base": {"id": 103027, "name": "Proteus Base", "aliases": ["prot base", "base"], "window": "18h - 18h 15m"},
    "proteus prime": {"id": 103028, "name": "Proteus Prime", "aliases": ["prot prime", "prime"], "window": "18h - 18h 15m"},
    "bloodthorn": {"id": 141966, "name": "Bloodthorn The Ravenous", "aliases": ["bt"], "window": "34h - 62h"},
    "dhiothu": {"id": 142027, "name": "Dhiothu", "aliases": ["dhio", "dino"], "window": "34h - 62h"},
    "crom": {"id": 200490, "name": "Crom's Hellborne Manikin", "aliases": ["manikin", "hellborne"], "window": "96h - 104h"},
}


def find_boss(query: str):
    search = query.lower().strip()
    search = ALIASES.get(search, search)

    for key, boss in BOSSES.items():
        if search == key or search == str(boss["id"]):
            return boss

        if search == boss["name"].lower():
            return boss

        if search in boss.get("aliases", []):
            return boss

    for key, boss in BOSSES.items():
        if search in key or search in boss["name"].lower():
            return boss

    return None

if not TOKEN:
    raise ValueError('Missing DISCORD_TOKEN environment variable')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fmt_num(value):
    if value is None:
        return 'N/A'
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, (int, float)):
        return f'{value:,}'
    return str(value)


def fmt_resist(value):
    if value == -1:
        return 'Immune'
    return fmt_num(value)


def row_to_mob(row: sqlite3.Row) -> dict:
    return dict(row)


def find_mob(name: str):
    search = name.lower().strip()
    search = ALIASES.get(search, search)

    with get_db() as conn:
        row = conn.execute(
            '''
            SELECT * FROM mobs
            WHERE search_name = ?
            ORDER BY COALESCE(stars, 0) DESC, COALESCE(level, 0) DESC, COALESCE(health, 0) DESC
            LIMIT 1
            ''',
            (search,),
        ).fetchone()

        if row is None:
            row = conn.execute(
                '''
                SELECT * FROM mobs
                WHERE search_name LIKE ?
                ORDER BY COALESCE(stars, 0) DESC, COALESCE(level, 0) DESC, COALESCE(health, 0) DESC
                LIMIT 1
                ''',
                (f'%{search}%',),
            ).fetchone()

    return row_to_mob(row) if row else None


def make_mob_embed(mob: dict) -> discord.Embed:
    title = f"{mob.get('name', 'Unknown')} (ID: {mob.get('id', 'N/A')})"
    embed = discord.Embed(title=title, color=discord.Color.red())

    general_stats = (
        f"📈 **Level:** {fmt_num(mob.get('level'))}\n"
        f"❤️ **HP:** {fmt_num(mob.get('health'))}\n"
        f"🔋 **Energy:** {fmt_num(mob.get('energy'))}"
    )

    general_stats_2 = (
        f"⚔️ **Attack:** {fmt_num(mob.get('attack'))}\n"
        f"🛡️ **Defence:** {fmt_num(mob.get('defence'))}\n"
        f"⏱️ **Attack Spd:** {fmt_num(mob.get('attack_speed'))}"
    )

    general_stats_3 = (
        f"📏 **Radius:** {fmt_num(mob.get('range'))}\n"
        f"🪙 **Gold:** {fmt_num(mob.get('gold_min'))} - {fmt_num(mob.get('gold_max'))}\n"
        f"⭐ **Exp:** {fmt_num(mob.get('xp'))}"
    )

    combat_stats = (
        f"🏹 **Atk Range:** {fmt_num(mob.get('attack_range'))}\n"
        f"🚀 **Missile Spd:** {fmt_num(mob.get('missile_speed'))}\n"
        f"👣 **Follow Range:** {fmt_num(mob.get('follow_range'))}"
    )

    misc_stats = f"😠 **Opinion:** {str(mob.get('opinion') or 'N/A').title()}"

    damage_resist = (
        f"🗡️ **Pierce:** {fmt_num(mob.get('damage_pierce'))} / {fmt_resist(mob.get('resist_pierce'))}\n"
        f"⚔️ **Slash:** {fmt_num(mob.get('damage_slash'))} / {fmt_resist(mob.get('resist_slash'))}\n"
        f"🔨 **Crush:** {fmt_num(mob.get('damage_crush'))} / {fmt_resist(mob.get('resist_crush'))}\n"
        f"🔥 **Heat:** {fmt_num(mob.get('damage_heat'))} / {fmt_resist(mob.get('resist_heat'))}\n"
        f"❄️ **Cold:** {fmt_num(mob.get('damage_cold'))} / {fmt_resist(mob.get('resist_cold'))}\n"
        f"✨ **Magic:** {fmt_num(mob.get('damage_magic'))} / {fmt_resist(mob.get('resist_magic'))}\n"
        f"☠️ **Poison:** {fmt_num(mob.get('damage_poison'))} / {fmt_resist(mob.get('resist_poison'))}\n"
        f"🌟 **Divine:** {fmt_num(mob.get('damage_divine'))} / {fmt_resist(mob.get('resist_divine'))}\n"
        f"🌑 **Chaos:** {fmt_num(mob.get('damage_chaos'))} / {fmt_resist(mob.get('resist_chaos'))}"
    )

    evasions = (
        f"🛡️ **Physical:** {fmt_num(mob.get('physical_evade'))}\n"
        f"🔮 **Spell:** {fmt_num(mob.get('spell_evade'))}\n"
        f"💨 **Movement:** {fmt_num(mob.get('move_evade'))}\n"
        f"🩸 **Wounding:** {fmt_num(mob.get('wound_evade'))}\n"
        f"🪶 **Weakening:** {fmt_num(mob.get('weak_evade'))}\n"
        f"🧠 **Mental:** {fmt_num(mob.get('mental_evade'))}"
    )

    embed.add_field(name='General Stats', value=general_stats, inline=True)
    embed.add_field(name='\u200b', value=general_stats_2, inline=True)
    embed.add_field(name='\u200b', value=general_stats_3, inline=True)
    embed.add_field(name='\u200b', value=combat_stats, inline=True)
    embed.add_field(name='\u200b', value=misc_stats, inline=True)
    embed.add_field(name='Damage / Resist', value=damage_resist, inline=True)
    embed.add_field(name='Evasions', value=evasions, inline=False)
    return embed


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def mob(ctx, *, name: str):
    mob_data = find_mob(name)
    if not mob_data:
        await ctx.send('Mob not found.')
        return

    await ctx.send(embed=make_mob_embed(mob_data))


@bot.command()
async def dbstats(ctx):
    with get_db() as conn:
        mobs = conn.execute('SELECT COUNT(*) FROM mobs').fetchone()[0]
        spawns = conn.execute('SELECT COUNT(*) FROM mob_spawns').fetchone()[0]
        drops = conn.execute('SELECT COUNT(*) FROM mob_drops').fetchone()[0]
    await ctx.send(f'📚 Grimoire DB: **{mobs:,} mobs**, **{spawns:,} spawns**, **{drops:,} drop rows**')

@bot.command()
async def drops(ctx, *, name: str):
    mob_data = find_mob(name)

    if not mob_data:
        await ctx.send("Mob not found.")
        return

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT item_name, item_id
            FROM mob_drops
            WHERE mob_id = ?
            ORDER BY item_name
            """,
            (mob_data["id"],),
        ).fetchall()

    if not rows:
        await ctx.send(f"No drops found for **{mob_data['name']}**.")
        return

    # Remove duplicate drops
    seen = set()
    drops = []
    for row in rows:
        key = (row["item_name"], row["item_id"])
        if key not in seen:
            seen.add(key)
            drops.append(f"• **{row['item_name']}** `{row['item_id']}`")

    # Discord embed fields max around 1024 chars, so chunk it
    chunks = []
    current = ""

    for drop in drops:
        if len(current) + len(drop) + 1 > 1000:
            chunks.append(current)
            current = drop
        else:
            current += "\n" + drop if current else drop

    if current:
        chunks.append(current)

    embed = discord.Embed(
        title=f"Drops: {mob_data['name']}",
        description=f"Mob ID: `{mob_data['id']}`\nUnique drops: **{len(drops):,}**",
        color=discord.Color.gold()
    )

    for i, chunk in enumerate(chunks[:5], start=1):
        embed.add_field(name=f"Drop List {i}", value=chunk, inline=False)

    if len(chunks) > 5:
        embed.set_footer(text=f"Showing first 5 pages. {len(drops):,} total unique drops.")

    await ctx.send(embed=embed)

@bot.command(name="item")
async def item_lookup(ctx, *, query: str):
    search = query.lower().strip()

    with get_db() as conn:
        if search.isdigit():
            rows = conn.execute(
                """
                SELECT DISTINCT item_id, item_name
                FROM mob_drops
                WHERE item_id = ?
                ORDER BY item_name
                """,
                (int(search),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT DISTINCT item_id, item_name
                FROM mob_drops
                WHERE LOWER(item_name) LIKE ?
                ORDER BY item_name
                LIMIT 10
                """,
                (f"%{search}%",),
            ).fetchall()

    if not rows:
        await ctx.send("Item not found.")
        return

    if len(rows) > 1:
        msg = "\n".join(f"• **{r['item_name']}** `{r['item_id']}`" for r in rows)
        await ctx.send(f"Multiple matches:\n{msg}")
        return

    item_id = rows[0]["item_id"]
    item_name = rows[0]["item_name"]

    with get_db() as conn:
        mobs = conn.execute(
            """
            SELECT DISTINCT m.name, m.id
            FROM mob_drops d
            JOIN mobs m ON m.id = d.mob_id
            WHERE d.item_id = ?
            ORDER BY m.name
            """,
            (item_id,),
        ).fetchall()

    dropped_by = "\n".join(f"• **{m['name']}** `{m['id']}`" for m in mobs) or "No mob drops found."

    embed = discord.Embed(
        title=item_name,
        description=f"Item ID: `{item_id}`",
        color=discord.Color.blue()
    )
    embed.add_field(name="Dropped By", value=dropped_by[:1024], inline=False)

    await ctx.send(embed=embed)


@bot.command(name="who_drops", aliases=["whodrops", "source", "sources"])
async def who_drops(ctx, *, query: str):
    await item_lookup(ctx, query=query)

@bot.command()
async def boss(ctx, *, query: str):
    boss_info = find_boss(query)

    if not boss_info:
        await ctx.send("Boss not found.")
        return

    mob_data = find_mob(boss_info["name"])

    with get_db() as conn:
        drop_count = conn.execute(
            """
            SELECT COUNT(DISTINCT item_id)
            FROM mob_drops
            WHERE mob_id = ?
            """,
            (boss_info["id"],),
        ).fetchone()[0]

    embed = discord.Embed(
        title=boss_info["name"],
        color=discord.Color.dark_gold()
    )

    embed.add_field(name="Boss ID", value=f"`{boss_info['id']}`", inline=True)
    embed.add_field(name="Respawn Window", value=boss_info["window"], inline=True)
    embed.add_field(name="Known Unique Drops", value=f"{drop_count:,}", inline=True)

    if mob_data:
        embed.add_field(
            name="Stats",
            value=(
                f"Level: **{fmt_num(mob_data.get('level'))}**\n"
                f"HP: **{fmt_num(mob_data.get('health'))}**\n"
                f"Attack: **{fmt_num(mob_data.get('attack'))}**\n"
                f"Defence: **{fmt_num(mob_data.get('defence'))}**"
            ),
            inline=True
        )

        user_alias = query.lower().strip()
        
        embed.add_field(
            name="Useful Commands",
            value=(
                f"• `!mob {user_alias}`\n"
                f"• `!drops {user_alias}`\n"
                f"• `!boss {user_alias}`\n"
                f"• `!item <item name or id>`"
            ),
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, query: str):
    search_text = query.lower().strip()
    alias_text = ALIASES.get(search_text, search_text)

    boss_matches = []
    for key, boss in BOSSES.items():
        names = [key, boss["name"].lower()] + boss.get("aliases", [])
        if any(alias_text in n for n in names):
            boss_matches.append(f"• **{boss['name']}** `{boss['id']}`")

    with get_db() as conn:
        mob_rows = conn.execute(
            """
            SELECT DISTINCT id, name, level, stars
            FROM mobs
            WHERE search_name LIKE ?
            ORDER BY COALESCE(stars, 0) DESC, COALESCE(level, 0) DESC
            LIMIT 10
            """,
            (f"%{alias_text}%",),
        ).fetchall()

        item_rows = conn.execute(
            """
            SELECT DISTINCT item_id, item_name
            FROM mob_drops
            WHERE LOWER(item_name) LIKE ?
            ORDER BY item_name
            LIMIT 10
            """,
            (f"%{search_text}%",),
        ).fetchall()

    mob_matches = [
        f"• **{m['name']}** `{m['id']}` — Lv {fmt_num(m['level'])}, {fmt_num(m['stars'])}★"
        for m in mob_rows
    ]

    item_matches = [
        f"• **{i['item_name']}** `{i['item_id']}`"
        for i in item_rows
    ]

    if not boss_matches and not mob_matches and not item_matches:
        await ctx.send("No results found.")
        return

    embed = discord.Embed(
        title=f"Search Results: {query}",
        color=discord.Color.purple()
    )

    if boss_matches:
        embed.add_field(
            name="Bosses",
            value="\n".join(boss_matches[:10]),
            inline=False
        )

    if mob_matches:
        embed.add_field(
            name="Mobs",
            value="\n".join(mob_matches[:10]),
            inline=False
        )

    if item_matches:
        embed.add_field(
            name="Items",
            value="\n".join(item_matches[:10]),
            inline=False
        )

    await ctx.send(embed=embed)

bot.run(TOKEN)
