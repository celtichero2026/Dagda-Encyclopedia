import os
import json
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("Missing DISCORD_TOKEN environment variable")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

with open("mobs.json", "r", encoding="utf-8") as f:
    mobs = json.load(f)


def fmt_num(value):
    if value is None:
        return "N/A"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return str(value)


def fmt_resist(value):
    if value == -1:
        return "Immune"
    return fmt_num(value)


def find_mob(name: str):
    search = name.lower().strip()

    exact = []
    partial = []

    for mob in mobs:
        mob_name = mob.get("name", "").lower()

        if mob_name == search:
            exact.append(mob)
        elif search in mob_name:
            partial.append(mob)

    # prefer exact, then partial, then higher stars/level
    pool = exact if exact else partial
    if not pool:
        return None

    pool.sort(key=lambda m: (m.get("stars", 0), m.get("level", 0), m.get("health", 0)), reverse=True)
    return pool[0]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def mob(ctx, *, name: str):
    mob = find_mob(name)

    if not mob:
        await ctx.send("Mob not found.")
        return

    damage = mob.get("damage", {})
    resist = mob.get("resist", {})

    title = f"{mob.get('name', 'Unknown')} (ID: {mob.get('id', 'N/A')})"

    embed = discord.Embed(
        title=title,
        color=discord.Color.red()
    )

    general_stats = (
        f"**Level:** {fmt_num(mob.get('level'))}\n"
        f"**HP:** {fmt_num(mob.get('health'))}\n"
        f"**Energy:** {fmt_num(mob.get('energy'))}"
    )

    general_stats_2 = (
        f"**Attack:** {fmt_num(mob.get('attack'))}\n"
        f"**Defence:** {fmt_num(mob.get('defence'))}\n"
        f"**Attack Spd:** {fmt_num(mob.get('attackSpeed'))}"
    )

    general_stats_3 = (
        f"**Radius:** {fmt_num(mob.get('range'))}\n"
        f"**Gold:** {fmt_num(mob.get('goldMax'))}\n"
        f"**Exp:** {fmt_num(mob.get('xp'))}"
    )

    combat_stats = (
        f"**Atk Range:** {fmt_num(mob.get('AttackRange'))}\n"
        f"**Missile Spd:** {fmt_num(mob.get('missileSpeed'))}\n"
        f"**Follow Range:** {fmt_num(mob.get('followRange'))}"
    )

    misc_stats = f"**Opinion:** {str(mob.get('opinion', 'N/A')).title()}"

    damage_resist = (
        f"**Pierce:** {fmt_num(damage.get('pierce'))} / {fmt_resist(resist.get('pierce'))}\n"
        f"**Slash:** {fmt_num(damage.get('slash'))} / {fmt_resist(resist.get('slash'))}\n"
        f"**Crush:** {fmt_num(damage.get('crush'))} / {fmt_resist(resist.get('crush'))}\n"
        f"**Heat:** {fmt_num(damage.get('heat'))} / {fmt_resist(resist.get('heat'))}\n"
        f"**Cold:** {fmt_num(damage.get('cold'))} / {fmt_resist(resist.get('cold'))}\n"
        f"**Magic:** {fmt_num(damage.get('magic'))} / {fmt_resist(resist.get('magic'))}\n"
        f"**Poison:** {fmt_num(damage.get('poison'))} / {fmt_resist(resist.get('poison'))}\n"
        f"**Divine:** {fmt_num(damage.get('divine'))} / {fmt_resist(resist.get('divine'))}\n"
        f"**Chaos:** {fmt_num(damage.get('chaos'))} / {fmt_resist(resist.get('chaos'))}"
    )

    evasions = (
        f"**Physical:** {fmt_num(mob.get('physicalEvade'))}\n"
        f"**Spell:** {fmt_num(mob.get('spellEvade'))}\n"
        f"**Movement:** {fmt_num(mob.get('moveEvade'))}\n"
        f"**Wounding:** {fmt_num(mob.get('woundEvade'))}\n"
        f"**Weakening:** {fmt_num(mob.get('weakEvade'))}\n"
        f"**Mental:** {fmt_num(mob.get('mentalEvade'))}"
    )

    embed.add_field(name="General Stats", value=general_stats, inline=True)
    embed.add_field(name="\u200b", value=general_stats_2, inline=True)
    embed.add_field(name="\u200b", value=general_stats_3, inline=True)

    embed.add_field(name="\u200b", value=combat_stats, inline=True)
    embed.add_field(name="\u200b", value=misc_stats, inline=True)
    embed.add_field(name="Damage / Resist", value=damage_resist, inline=True)

    embed.add_field(name="Evasions", value=evasions, inline=False)

    await ctx.send(embed=embed)


bot.run(TOKEN)
