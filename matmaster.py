import discord
from discord.ext import commands, tasks
import logging
import os
import asyncio
from datetime import datetime, timedelta
from dateparser import parse

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('discord')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables.")
    exit()

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Create the bot instance with a simple '!' prefix
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}! Bot is in the following guilds: {[guild.name for guild in bot.guilds]}")
    all_commands = ', '.join([command.name for command in bot.commands])
    logger.info(f"Available commands: {all_commands}")

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"An error occurred: {str(error)}")
    await ctx.send(f"An error occurred: {str(error)}")

@bot.command(name='mm_help')
async def mm_help(ctx):
    help_text = (
        "**Crafting Requisition Bot Commands:**\n\n"
        "__**Commands Overview:**__\n\n"
        "**!mm_help**\nDisplays this help message.\n\n"
        "**!mm_set_channels <requisitions_channel_id> <archive_channel_id>**\n"
        "Set the channel IDs for requisitions and archive. Use in the format:\n"
        "`!mm_set_channels 123456789012345678 987654321098765432`\n\n"
        "**!mm_request [material, quantity, payment, deadline]**\n"
        "Start a new requisition with the specified parameters. Use in the format:\n"
        "`!mm_request Iron, 50, 10 Gold Bars, 2024-06-30`\n\n"
        "**!mm_update_request <message_id> [new_quantity] [new_payment] [new_deadline]**\n"
        "Update an existing requisition. Use in the format:\n"
        "`!mm_update_request 123456789012345678 60 20 Gold Bars 2024-07-31`\n\n"
        "**!mm_progress <message_id> <percentage>**\n"
        "Update the progress of gathering materials for a requisition. Use in the format:\n"
        "`!mm_progress 123456789012345678 50`\n\n"
        "**!mm_feedback <message_id> <feedback>**\n"
        "Collect feedback from requesters after a requisition is completed. Use in the format:\n"
        "`!mm_feedback 123456789012345678 The materials were delivered on time and in good condition.`\n"
    )
    await ctx.send(help_text)

async def load_extensions():
    await bot.load_extension('cogs.requisition_flow')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
