import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

async def main():
    async with bot:
        await bot.load_extension('link_monitor')        # loads "link_monitor.py"
        await bot.start('token')                        # Insert Bot-Token here

if __name__ == "__main__":
    asyncio.run(main())