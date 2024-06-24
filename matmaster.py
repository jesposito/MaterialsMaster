import discord
from discord.ext import commands, tasks
import logging
import os
import asyncio
from datetime import datetime, timedelta
from dateparser import parse
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('discord')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables.")
    exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables.")
    exit(1)

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
    "**🛠️ Materials Master (MatMaster) Requisition Bot Commands:**\n\n"
    "**Overview of Commands:**\n\n"
    "**!mm_help**\n"
    "Displays this help message. Use this command if you need a quick reminder of how to interact with me.\n\n"
    
    "**!mm_set_channels <requisitions_channel_id> <archive_channel_id>**\n"
    "Sets up the channels for managing requisitions and archiving them once completed. Here’s how to set it up:\n"
    "`!mm_set_channels 123456789012345678 987654321098765432`\n"
    "> Make sure you replace the IDs with your actual channel IDs!\n\n"
    
    "**!mm_request [material, quantity, payment, deadline]**\n"
    "Starts a new requisition. You can enter all details at once like this:\n"
    "`!mm_request Iron, 50, 10 Gold Bars, 2024-06-30`\n"
    "Or, simply type `!mm_request` and I'll guide you through the process interactively, asking for each detail one step at a time. This way, you can take your time providing the necessary information.\n\n"
    
    "**!mm_update_request <message_id>, <new_quantity>, <new_payment>, <new_deadline>**\n"
    "Need to make changes to an existing requisition? Just let me know what needs updating. Here’s the format:\n"
    "`!mm_update_request 123456789012345678, 60, 20 Gold Bars, 2024-07-31`\n"
    "> Remember to include the message ID of the requisition you’re updating.\n"
    "Or, simply type `!mm_update_request` and I'll guide you through the update process interactively, asking for each detail one step at a time.\n\n"
    
    "**Feedback on Requisitions**\n"
    "Once your requisition is completed and archived, I’ll send you a direct message to collect your feedback. It’s a great way to let us know how the process went and how we can improve!\n"
)

    await ctx.send(help_text)

async def load_extensions():
    await bot.load_extension('cogs.requisition_flow')

async def main():
    async with bot:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)
        await bot.add_cog(RequisitionFlow(bot, conn))
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
