import os
import json
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

if not TOKEN:
    raise ValueError("Missing DISCORD_TOKEN")
if not GUILD_ID:
    raise ValueError("Missing GUILD_ID")

with open("boss_data.json", "r", encoding="utf-8") as f:
    boss_data = json.load(f)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def find_boss(name: str):
    search = name.lower().strip()

    for key, value in boss_data.items():
        boss_name = str(value.get("name", "")).lower()
        if search == key.lower() or search in boss_name:
            return value

    return None


async def setup_hook():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)


bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.tree.command(
    name="bossinfo",
    description="Show boss information",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(name="Boss name")
async def bossinfo(interaction: discord.Interaction, name: str):
    boss = find_boss(name)

    if not boss:
        await interaction.response.send_message("Boss not found.", ephemeral=True)
        return

    boss_name = boss.get("name", "Unknown Boss")
    boss_id = boss.get("id", "N/A")
    level = boss.get("level", "N/A")
    hp = boss.get("health", boss.get("hp", "N/A"))
    attack = boss.get("attack", "N/A")
    defense = boss.get("defence", boss.get("defense", "N/A"))
    attack_speed = boss.get("attackSpeed", "N/A")
    xp = boss.get("xp", "N/A")
    gold = boss.get("gold", "N/A")

    embed = discord.Embed(
        title=f"{boss_name} (ID: {boss_id})",
        color=0xC0392B
    )

    general_lines = [
        f"**Level:** {level}",
        f"**HP:** {hp:,}" if isinstance(hp, int) else f"**HP:** {hp}",
        f"**Attack:** {attack:,}" if isinstance(attack, int) else f"**Attack:** {attack}",
        f"**Defense:** {defense:,}" if isinstance(defense, int) else f"**Defense:** {defense}",
        f"**Attack Spd:** {attack_speed}",
        f"**XP:** {xp:,}" if isinstance(xp, int) else f"**XP:** {xp}",
        f"**Gold:** {gold:,}" if isinstance(gold, int) else f"**Gold:** {gold}",
    ]

    embed.add_field(
        name="General Stats",
        value="\n".join(general_lines),
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
