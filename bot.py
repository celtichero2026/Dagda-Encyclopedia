import os
import sqlite3
import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = os.getenv('GRIMOIRE_DB', 'grimoire.db')

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
    with get_db() as conn:
        # Exact match first, then partial. Sort like your JSON version did.
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


bot.run(TOKEN)
