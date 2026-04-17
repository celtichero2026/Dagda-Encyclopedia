import discord
from discord.ext import commands
import json

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load mob data
with open("mobs.json", "r") as f:
    mobs = json.load(f)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Command: !boss gelebron
@bot.command()
async def boss(ctx, *, name: str):
    name = name.lower()

    for mob in mobs:
        if name in mob["name"].lower() and mob.get("stars") == 6:
            embed = discord.Embed(
                title=mob["name"],
                color=discord.Color.red()
            )

            embed.add_field(name="Level", value=mob["level"])
            embed.add_field(name="HP", value=mob["health"])
            embed.add_field(name="Attack", value=mob["attack"])
            embed.add_field(name="Defense", value=mob["defence"])

            dmg = mob.get("damage", {})
            embed.add_field(
                name="Damage",
                value=f"Magic: {dmg.get('magic',0)} | Chaos: {dmg.get('chaos',0)}",
                inline=False
            )

            await ctx.send(embed=embed)
            return

    await ctx.send("Boss not found 😢")

bot.run("YOUR_TOKEN_HERE")
