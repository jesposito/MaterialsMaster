import discord
from discord.ext import commands
from cerberus import Validator
import asyncio
import logging
from datetime import datetime, timedelta
from dateparser import parse
from psycopg2.extras import RealDictCursor
import random

logger = logging.getLogger('discord')

# Validation schema
schema = {
    'material': {'type': 'string', 'required': True},
    'quantity': {'type': 'integer', 'min': 1, 'required': True},
    'payment': {'type': 'string', 'required': True},
    'deadline': {'type': 'string', 'required': True},
    'region': {'type': 'string', 'required': True}
}
v = Validator(schema)

class RequisitionFlow(commands.Cog):
    def __init__(self, bot, conn):
        self.bot = bot
        self.conn = conn
        self.channel_ids = {}
        self.active_requisitions = {}
        self.reminder_tasks = {}
        logger.info("RequisitionFlow cog initialized.")
        self.create_tables()
        self.load_channel_ids()
        self.load_active_requisitions()

    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS requisitions (
                    id SERIAL PRIMARY KEY,
                    requester BIGINT,
                    material TEXT,
                    quantity INTEGER,
                    payment TEXT,
                    deadline TIMESTAMP,
                    accepted_by BIGINT[],
                    completed_by BIGINT[],
                    message_id BIGINT,
                    region TEXT,
                    completion_details TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    guild_id BIGINT PRIMARY KEY,
                    requisitions_channel_id BIGINT,
                    archive_channel_id BIGINT,
                    server_name TEXT
                );
            """)
            self.conn.commit()

    def load_channel_ids(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM channels")
            rows = cur.fetchall()
            for row in rows:
                self.channel_ids[row['guild_id']] = {
                    'REQUISITIONS_CHANNEL_ID': row['requisitions_channel_id'],
                    'ARCHIVE_CHANNEL_ID': row['archive_channel_id'],
                    'SERVER_NAME': row['server_name']
                }
        logger.info(f"Loaded channel IDs for {len(self.channel_ids)} guilds.")

    def load_active_requisitions(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM requisitions WHERE message_id IS NOT NULL")
            rows = cur.fetchall()
            for row in rows:
                self.active_requisitions[row['message_id']] = {
                    'requester': row['requester'],
                    'material': row['material'],
                    'quantity': row['quantity'],
                    'payment': row['payment'],
                    'deadline': row['deadline'].strftime('%Y-%m-%d %H:%M:%S'),
                    'accepted_by': row['accepted_by'],
                    'completed_by': row['completed_by'],
                    'region': row['region'],
                    'completion_details': row.get('completion_details', "")
                }
        logger.info(f"Loaded active requisitions for {len(self.active_requisitions)} messages.")

    def validate_request(self, data):
        logger.debug(f"Validating request data: {data}")
        is_valid = v.validate(data)
        if not is_valid:
            logger.warning(f"Validation failed: {v.errors}")
        return is_valid

    async def send_reminder(self, user, message, message_id):
        logger.info(f"Scheduling reminder for user {user} with message: {message}")
        task = asyncio.create_task(self.remind_later(user, message, 3600))
        self.reminder_tasks[message_id] = task

    async def remind_later(self, user, message, delay):
        await asyncio.sleep(delay)
        await user.send(message)
        logger.info(f"Reminder sent to user {user}")

    @commands.command(name='mm_config')
    @commands.has_permissions(administrator=True)
    async def mm_config(self, ctx, requisitions_channel_id: int, archive_channel_id: int, *, server_name: str):
        guild_id = ctx.guild.id
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO channels (guild_id, requisitions_channel_id, archive_channel_id, server_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE
                SET requisitions_channel_id = EXCLUDED.requisitions_channel_id,
                    archive_channel_id = EXCLUDED.archive_channel_id,
                    server_name = EXCLUDED.server_name;
            """, (guild_id, requisitions_channel_id, archive_channel_id, server_name))
            self.conn.commit()

        self.channel_ids[guild_id] = {
            'REQUISITIONS_CHANNEL_ID': requisitions_channel_id,
            'ARCHIVE_CHANNEL_ID': archive_channel_id,
            'SERVER_NAME': server_name
        }

        await ctx.send(f"Requisition channel set to <#{requisitions_channel_id}>, archive channel set to <#{archive_channel_id}>, and server name set to `{server_name}` for {ctx.guild.name}")

    @mm_config.error
    async def mm_config_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have the necessary permissions to use this command.")
        else:
            await ctx.send("An error occurred while processing the command.")

    @commands.command(name='mm_request')
    async def mm_request(self, ctx, *, user_input: str = None):
        if user_input:
            parts = user_input.split(',')
            if len(parts) == 5 and all(part.strip() for part in parts):
                material, quantity, payment, deadline, region = (part.strip() for part in parts)
                if quantity.isdigit():
                    await self.create_requisition(ctx, material, int(quantity), payment, deadline, region)
                    return
            await ctx.send("Invalid format. Use: `!mm_request [material, quantity, payment, deadline, region]` or follow the interactive prompts.")
        else:
            await ctx.send("What material do you need?")
            try:
                material = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
                await ctx.send("How many do you need?")
                quantity_msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
                if not quantity_msg.content.isdigit():
                    await ctx.send("Quantity must be a number.")
                    return
                await ctx.send("What is the payment method?")
                payment = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
                await ctx.send("What is the deadline?")
                deadline = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
                await ctx.send("What is the region?")
                region = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)

                data = {
                    'material': material.content,
                    'quantity': int(quantity_msg.content),
                    'payment': payment.content,
                    'deadline': deadline.content,
                    'region': region.content
                }

                if self.validate_request(data):
                    await self.create_requisition(ctx, data['material'], data['quantity'], data['payment'], data['deadline'], data['region'])
                else:
                    await ctx.send(f"Validation failed: {v.errors}")

            except asyncio.TimeoutError:
                await ctx.send("Request timed out. Please try again.")

    async def create_requisition(self, ctx, material, quantity, payment, deadline, region):
        parsed_deadline = parse(deadline)
        if not parsed_deadline:
            await ctx.send("Could not understand the deadline. Please enter a specific date.")
            return
        
        formatted_deadline = parsed_deadline.strftime('%Y-%m-%d %H:%M:%S')
        
        data = {
            'material': material,
            'quantity': quantity,
            'payment': payment,
            'deadline': formatted_deadline,
            'region': region
        }
        
        if self.validate_request(data):
            guild_id = ctx.guild.id
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO requisitions (requester, material, quantity, payment, deadline, accepted_by, completed_by, message_id, region)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (ctx.author.id, material, quantity, payment, formatted_deadline, [], [], None, region))
                requisition_id = cur.fetchone()['id']
                self.conn.commit()

            if guild_id in self.channel_ids and 'REQUISITIONS_CHANNEL_ID' in self.channel_ids[guild_id]:
                channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
                server_name = self.channel_ids[guild_id]['SERVER_NAME']
                channel = self.bot.get_channel(channel_id)
                if channel:
                    message_content = (
                        f"**{server_name} - {region}**\n"
                        f"**Request from {ctx.author.mention}:**\n"
                        f"**Material:** {material}\n"
                        f"**Quantity:** {quantity}\n"
                        f"**Payment:** {payment}\n"
                        f"**Deadline:** {formatted_deadline}\n"
                        "React with ✋ to accept this job. React with ✅ when completed.\n"
                    )
                    message = await channel.send(message_content)
                    with self.conn.cursor() as cur:
                        cur.execute("""
                            UPDATE requisitions
                            SET message_id = %s
                            WHERE id = %s;
                        """, (message.id, requisition_id))
                        self.conn.commit()
                    self.active_requisitions[message.id] = {
                        'requester': ctx.author.id,
                        'material': material,
                        'quantity': quantity,
                        'payment': payment,
                        'deadline': formatted_deadline,
                        'region': region,
                        'accepted_by': [],
                        'completed_by': []
                    }
                    await message.add_reaction('✋')
                    await message.add_reaction('✅')
                    await self.send_reminder(ctx.author, f"Reminder: Your requisition for {material} is still open.", message.id)
                else:
                    await ctx.send("Invalid requisitions channel ID.")
            else:
                await ctx.send("Requisitions channel ID has not been set. Use the `!mm_config` command to set it.")
        else:
            await ctx.send(f"Validation failed: {v.errors}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message_id = reaction.message.id
        guild_id = reaction.message.guild.id

        if message_id not in self.active_requisitions:
            return

        requisition = self.active_requisitions[message_id]
        requester = self.bot.get_user(requisition['requester'])

        if reaction.emoji == '✋':
            if user.id not in requisition['accepted_by']:
                requisition['accepted_by'].append(user.id)
                await user.send(f"You have accepted the requisition for {requisition['material']}.")
                if requester:
                    await requester.send(f"{user.mention} has accepted your requisition for {requisition['material']}.")

        elif reaction.emoji == '✅' and user.id in requisition['accepted_by']:
            if user.id not in requisition['completed_by']:
                requisition['completed_by'].append(user.id)
                if len(requisition['completed_by']) == len(requisition['accepted_by']):
                    if requester:
                        await requester.send(f"All parties have completed the requisition for {requisition['material']}. Please confirm by reacting with ✅.")
                    await self.get_completion_details(requisition, user, requester, message_id, guild_id)

    async def get_completion_details(self, requisition, user, requester, message_id, guild_id):
        try:
            await user.send(f"Please provide completion details for the requisition `{requisition['material']}` (e.g., where the resources are left, meeting arrangements, etc.). You have 5 minutes to respond.")
            completion_details = await self.bot.wait_for(
                'message',
                check=lambda message: message.author == user and isinstance(message.channel, discord.DMChannel),
                timeout=300
            )
            completion_details_text = completion_details.content
        except asyncio.TimeoutError:
            completion_details_text = "No details provided."

        requisition['completion_details'] = completion_details_text

        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE requisitions
                SET completion_details = %s
                WHERE message_id = %s;
            """, (completion_details_text, message_id))
            self.conn.commit()

        await requester.send(f"Completion details for your requisition `{requisition['material']}`: {completion_details_text}")

        await self.archive_requisition(requisition, message_id, guild_id)

    async def archive_requisition(self, requisition, message_id, guild_id):
        archive_channel_id = self.channel_ids[guild_id]['ARCHIVE_CHANNEL_ID']
        archive_channel = self.bot.get_channel(archive_channel_id)
        requisitions_channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
        requisitions_channel = self.bot.get_channel(requisitions_channel_id)

        try:
            message = await requisitions_channel.fetch_message(message_id)
            server_name = self.channel_ids[guild_id]['SERVER_NAME']
            archived_message_content = (
                f"**{server_name} - {requisition['region']}**\n"
                f"**Archived Request from {self.bot.get_user(requisition['requester']).mention}:**\n"
                f"**Material:** {requisition['material']}\n"
                f"**Quantity:** {requisition['quantity']}\n"
                f"**Payment:** {requisition['payment']}\n"
                f"**Deadline:** {requisition['deadline']}\n"
                f"**Completed by:** {', '.join([self.bot.get_user(uid).mention for uid in requisition['completed_by']])}\n"
                f"**Completion Details:** {requisition['completion_details']}\n"
            )
            if random.random() < 0.1:  # 10% chance to include the donation link
                donate_message = "\n\nIf you find this bot helpful, please consider donating to support its development: https://ko-fi.com/jedespo"
                archived_message_content += donate_message

            archived_message = await archive_channel.send(archived_message_content)
            await message.delete()
            del self.active_requisitions[message_id]

            requester = self.bot.get_user(requisition['requester'])
            dm_channel = await requester.create_dm()
            await dm_channel.send(
                f"Your requisition has been completed and archived!\n"
                f"\n"
                f"**Please provide feedback** on your experience in a few sentences.\n"
                f"I'll add it onto the archived post. Provide feedback here:"
            )

            def check(m):
                return m.author == requester and isinstance(m.channel, discord.DMChannel)

            feedback_message = await self.bot.wait_for('message', check=check, timeout=300)
            if feedback_message:
                await archived_message.edit(content=f"{archived_message.content}\n**Feedback:** {feedback_message.content}")
                await dm_channel.send("Thank you for your feedback!")
        except discord.NotFound:
            logger.error("Message or channel not found")
        except discord.Forbidden:
            logger.error("Bot lacks permissions to fetch/delete messages or send messages in the archive channel")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")

    @commands.command(name='mm_update_request')
    async def mm_update_request(self, ctx, *, user_input: str = None):
        if user_input:
            parts = user_input.split(',')
            if len(parts) == 4 and all(part.strip() for part in parts):
                message_id, new_quantity, new_payment, new_deadline = (part.strip() for part in parts)
                if new_quantity.isdigit() and message_id.isdigit():
                    await self.update_requisition(ctx, message_id, int(new_quantity), new_payment, new_deadline)
                    return
                else:
                    await ctx.send("Please ensure the message ID and quantity are numbers.")
                    return
            else:
                await ctx.send("Invalid format. Use: `!mm_update_request <message_id>, <new_quantity>, <new_payment>, <new_deadline>`")
        else:
            await ctx.send("Please enter the message ID of the requisition you want to update:")
            message_id = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
            await ctx.send("Enter the new quantity:")
            quantity_msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
            if not quantity_msg.content.isdigit():
                await ctx.send("Quantity must be a number. Try again.")
                return
            await ctx.send("Enter the new payment method:")
            payment = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
            await ctx.send("Enter the new deadline:")
            deadline = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel, timeout=60)
            
            await self.update_requisition(ctx, message_id.content, int(quantity_msg.content), payment.content, deadline.content)

    async def update_requisition(self, ctx, message_id, new_quantity, new_payment, new_deadline):
        if not message_id.isdigit():
            await ctx.send("Invalid message ID format.")
            return
        
        message_id = int(message_id)
        
        if message_id not in self.active_requisitions:
            await ctx.send("Requisition not found.")
            return

        requisition = self.active_requisitions[message_id]

        parsed_deadline = parse(new_deadline)
        if not parsed_deadline:
            await ctx.send("Could not understand the deadline. Please enter a specific date.")
            return
        
        formatted_deadline = parsed_deadline.strftime('%Y-%m-%d %H:%M:%S')
        
        data = {
            'material': requisition['material'],
            'quantity': new_quantity,
            'payment': new_payment,
            'deadline': formatted_deadline
        }
        
        if not self.validate_request(data):
            await ctx.send(f"Validation failed: {v.errors}")
            return
        
        requisition.update({
            'quantity': new_quantity,
            'payment': new_payment,
            'deadline': formatted_deadline
        })
        
        guild_id = ctx.guild.id
        requisitions_channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
        requisitions_channel = self.bot.get_channel(requisitions_channel_id)

        if not requisitions_channel:
            await ctx.send("Requisitions channel not found or not set.")
            return
        
        try:
            message = await requisitions_channel.fetch_message(message_id)
            
            await message.edit(
                content=(
                    f"**Request from {ctx.author.mention}:**\n"
                    f"**Material:** {requisition['material']}\n"
                    f"**Quantity:** {new_quantity}\n"
                    f"**Payment:** {new_payment}\n"
                    f"**Deadline:** {formatted_deadline}\n"
                    "React with ✋ to accept this job. React with ✅ when completed.\n"
                )
            )
            
            await ctx.send(f"Requisition {message_id} updated successfully.")
        
        except discord.NotFound:
            await ctx.send("Original requisition message not found.")
            logger.error("Requisition message not found")
        
        except discord.Forbidden:
            await ctx.send("Bot lacks permissions to edit the requisition message.")
            logger.error("Bot lacks permissions to edit messages in the requisitions channel")
        
        except Exception as e:
            await ctx.send("An unexpected error occurred while updating the requisition message.")
            logger.error(f"Unexpected error: {str(e)}")
    
    def cancel_reminder(self, message_id):
        task = self.reminder_tasks.get(message_id)
        if task:
            task.cancel()
            logger.info(f"Cancelled reminder for message ID: {message_id}")
            del self.reminder_tasks[message_id]
        else:
            logger.warning(f"No active reminder task found for message ID: {message_id}")

async def setup(bot):
    await bot.add_cog(RequisitionFlow(bot))
