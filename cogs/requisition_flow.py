import discord
from discord.ext import commands, tasks
from cerberus import Validator
import asyncio
import logging
import os
from datetime import datetime, timedelta
from dateparser import parse
from psycopg2.extras import RealDictCursor

logger = logging.getLogger('discord')

# Validation schema
schema = {
    'material': {'type': 'string', 'required': True},
    'quantity': {'type': 'integer', 'min': 1, 'required': True},
    'payment': {'type': 'string', 'required': True},
    'deadline': {'type': 'string', 'required': True},
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
                    message_id BIGINT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    guild_id BIGINT PRIMARY KEY,
                    requisitions_channel_id BIGINT,
                    archive_channel_id BIGINT
                );
            """)
            self.conn.commit()

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

    @commands.command(name='mm_set_channels')
    async def mm_set_channels(self, ctx, requisitions_channel_id: int, archive_channel_id: int):
        guild_id = ctx.guild.id
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO channels (guild_id, requisitions_channel_id, archive_channel_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE
                SET requisitions_channel_id = EXCLUDED.requisitions_channel_id,
                    archive_channel_id = EXCLUDED.archive_channel_id;
            """, (guild_id, requisitions_channel_id, archive_channel_id))
            self.conn.commit()

        await ctx.send(f"Requisition channel set to <#{requisitions_channel_id}> and archive channel set to <#{archive_channel_id}> for {ctx.guild.name}")

    @commands.command(name='mm_request')
    async def mm_request(self, ctx, *, user_input: str = None):
        if user_input:
            parts = user_input.split(',')
            if len(parts) == 4 and all(part.strip() for part in parts):
                material, quantity, payment, deadline = (part.strip() for part in parts)
                if quantity.isdigit():
                    await self.create_requisition(ctx, material, int(quantity), payment, deadline)
                    return
            await ctx.send("Invalid format. Use: `!mm_request [material, quantity, payment, deadline]` or follow the interactive prompts.")
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

                data = {
                    'material': material.content,
                    'quantity': int(quantity_msg.content),
                    'payment': payment.content,
                    'deadline': deadline.content
                }

                if self.validate_request(data):
                    await self.create_requisition(ctx, data['material'], data['quantity'], data['payment'], data['deadline'])
                else:
                    await ctx.send(f"Validation failed: {v.errors}")

            except asyncio.TimeoutError:
                await ctx.send("Request timed out. Please try again.")

    async def create_requisition(self, ctx, material, quantity, payment, deadline):
        parsed_deadline = parse(deadline)
        if not parsed_deadline:
            await ctx.send("Could not understand the deadline. Please enter a specific date.")
            return
        
        formatted_deadline = parsed_deadline.strftime('%Y-%m-%d %H:%M:%S')
        
        data = {
            'material': material,
            'quantity': quantity,
            'payment': payment,
            'deadline': formatted_deadline
        }
        
        if self.validate_request(data):
            guild_id = ctx.guild.id
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO requisitions (requester, material, quantity, payment, deadline, accepted_by, completed_by, message_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (ctx.author.id, material, quantity, payment, formatted_deadline, [], [], None))
                requisition_id = cur.fetchone()['id']
                self.conn.commit()

            if guild_id in self.channel_ids and 'REQUISITIONS_CHANNEL_ID' in self.channel_ids[guild_id]:
                channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
                channel = self.bot.get_channel(channel_id)
                if channel:
                    message = await channel.send(
                        f"**Request from {ctx.author.mention}:**\n"
                        f"**Material:** {material}\n"
                        f"**Quantity:** {quantity}\n"
                        f"**Payment:** {payment}\n"
                        f"**Deadline:** {formatted_deadline}\n"
                        "React with ✋ to accept this job. React with ✅ when completed.\n"
                    )
                    with self.conn.cursor() as cur:
                        cur.execute("""
                            UPDATE requisitions
                            SET message_id = %s
                            WHERE id = %s;
                        """, (message.id, requisition_id))
                        self.conn.commit()
                    await message.add_reaction('✋')
                    await message.add_reaction('✅')
                    await self.send_reminder(ctx.author, f"Reminder: Your requisition for {material} is still open.", message.id)
                else:
                    await ctx.send("Invalid requisitions channel ID.")
            else:
                await ctx.send("Requisitions channel ID has not been set. Use the `!mm_set_channels` command to set it.")
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

        if user.id == requisition['requester'] and reaction.emoji == '✅' and len(requisition['completed_by']) == len(requisition['accepted_by']):
            self.cancel_reminder(message_id)

            archive_channel_id = self.channel_ids[guild_id]['ARCHIVE_CHANNEL_ID']
            requisitions_channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
            archive_channel = self.bot.get_channel(archive_channel_id)
            requisitions_channel = self.bot.get_channel(requisitions_channel_id)

            try:
                message = await requisitions_channel.fetch_message(message_id)
                archived_message = await archive_channel.send(
                    f"**Archived Request from {requester.mention}:**\n"
                    f"**Material:** {requisition['material']}\n"
                    f"**Quantity:** {requisition['quantity']}\n"
                    f"**Payment:** {requisition['payment']}\n"
                    f"**Deadline:** {requisition['deadline']}\n"
                    f"**Completed by:** {', '.join([self.bot.get_user(uid).mention for uid in requisition['completed_by']])}"
                )
                await message.delete()
                del self.active_requisitions[message_id]

                dm_channel = await requester.create_dm()
                await dm_channel.send(
                    f"Your requisition has been completed and archived.\n"
                    f"**Please provide feedback** on your experience in a few sentences.\n"
                    f"I'll add it to the archived post. Procide feedback here:"
                    )

                def check(m):
                    return m.author == requester and isinstance(m.channel, discord.DMChannel)

                feedback_message = await self.bot.wait_for('message', check=check, timeout=300)
                if feedback_message:
                    await archived_message.edit(content=f"{archived_message.content}\nFeedback: {feedback_message.content}")
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