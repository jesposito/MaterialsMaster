import discord
from discord.ext import commands, tasks
from cerberus import Validator
import asyncio
import logging
import os
from datetime import datetime, timedelta
from dateparser import parse

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
    def __init__(self, bot):
        self.bot = bot
        self.channel_ids = {}
        self.active_requisitions = {}
        self.reminder_tasks = {}
        logger.info("RequisitionFlow cog initialized.")

    def validate_request(self, data):
        logger.debug(f"Validating request data: {data}")
        is_valid = v.validate(data)
        if not is_valid:
            logger.warning(f"Validation failed: {v.errors}")
        return is_valid

    async def send_reminder(self, user, message, message_id):  # Ensure this is declared correctly
        logger.info(f"Scheduling reminder for user {user} with message: {message}")
        # Example: Remind after 1 hour
        task = asyncio.create_task(self.remind_later(user, message, 3600))
        self.reminder_tasks[message_id] = task  # Here message_id is used

    async def remind_later(self, user, message, delay):
        await asyncio.sleep(delay)
        await user.send(message)
        logger.info(f"Reminder sent to user {user}")

    @commands.command(name='mm_set_channels')
    async def mm_set_channels(self, ctx, requisitions_channel_id: int, archive_channel_id: int):
        """Set the channel IDs for requisitions and archive per guild/server"""
        guild_id = ctx.guild.id  # Get the guild ID from the context

        # Store channel IDs in a dictionary with the guild ID as the key
        if guild_id not in self.channel_ids:
            self.channel_ids[guild_id] = {}

        self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID'] = requisitions_channel_id
        self.channel_ids[guild_id]['ARCHIVE_CHANNEL_ID'] = archive_channel_id

        await ctx.send(f"Requisition channel set to <#{requisitions_channel_id}> and archive channel set to <#{archive_channel_id}> for {ctx.guild.name}")

    @commands.command(name='mm_request')
    async def mm_request(self, ctx, *, user_input: str = None):
        """Start the requisition flow or handle full request"""
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
        # Try to parse the deadline from natural language to a datetime object
        parsed_deadline = parse(deadline)
        if not parsed_deadline:
            await ctx.send("Could not understand the deadline. Please enter a specific date.")
            return
        
        # Format the deadline as a string, or use it as a datetime object as needed
        formatted_deadline = parsed_deadline.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare the data dictionary
        data = {
            'material': material,
            'quantity': quantity,
            'payment': payment,
            'deadline': formatted_deadline  # Use the formatted deadline
        }
        
        # Validate the requisition data
        if self.validate_request(data):
            guild_id = ctx.guild.id
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
                    self.active_requisitions[message.id] = {
                        'requester': ctx.author.id,
                        'material': material,
                        'quantity': quantity,
                        'payment': payment,
                        'deadline': formatted_deadline,
                        'accepted_by': [],
                        'completed_by': []
                    }
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

        if user.id == requisition['requester'] and len(requisition['completed_by']) == len(requisition['accepted_by']):
            if requester:
                await requester.send(f"The requisition for {requisition['material']} has been completed and confirmed.")
            archive_channel_id = self.channel_ids[guild_id]['ARCHIVE_CHANNEL_ID']
            requisitions_channel_id = self.channel_ids[guild_id]['REQUISITIONS_CHANNEL_ID']
            archive_channel = self.bot.get_channel(archive_channel_id)
            requisitions_channel = self.bot.get_channel(requisitions_channel_id)

            try:
                message = await requisitions_channel.fetch_message(message_id)
                await archive_channel.send(
                    f"**Archived Request from {requester.mention}:**\n"
                    f"**Material:** {requisition['material']}\n"
                    f"**Quantity:** {requisition['quantity']}\n"
                    f"**Payment:** {requisition['payment']}\n"
                    f"**Deadline:** {requisition['deadline']}"
                )
                await message.delete()
                del self.active_requisitions[message_id]
            except discord.NotFound:
                logger.error("Message or channel not found")
            except discord.Forbidden:
                logger.error("Bot lacks permissions to fetch/delete messages or send messages in the archive channel")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")

    @commands.command(name='mm_update_request')
    async def mm_update_request(self, ctx, message_id: int, new_quantity: int = None, new_payment: str = None, new_deadline: str = None):
        """Update an existing requisition"""
        req = self.active_requisitions.get(message_id)
        if req:
            updates = {'quantity': new_quantity, 'payment': new_payment, 'deadline': new_deadline}
            req.update({k: v for k, v in updates.items() if v is not None})
            channel = self.bot.get_channel(self.channel_ids['REQUISITIONS_CHANNEL_ID'])
            if channel:
                message = await channel.fetch_message(message_id)
                await message.edit(content=f"**Request from {ctx.author.mention}:**\n**Material:** {req['material']}\n**Quantity:** {req['quantity']}\n**Payment:** {req['payment']}\n**Deadline:** {req['deadline']}\nReact with ✋ to accept this job.")
                await ctx.send("Requisition updated successfully.")
            else:
                await ctx.send("Invalid requisitions channel ID.")
        else:
            await ctx.send("Invalid message ID.")
    
    def cancel_reminder(self, message_id):
        task = self.reminder_tasks.get(message_id)
        if task:
            try:
                task.cancel()
                logger.info(f"Cancelled reminder for message ID: {message_id}")
            except asyncio.CancelledError:
                logger.error(f"Attempted to cancel an already cancelled task for message ID: {message_id}")
            finally:
                del self.reminder_tasks[message_id]  # Always ensure to clean up

    @commands.command(name='mm_progress')
    async def mm_progress(self, ctx, message_id: int, percentage: int):
        """Update the progress of gathering materials for a requisition"""
        if message_id in self.active_requisitions:
            self.active_requisitions[message_id]['progress'] = percentage
            await ctx.send(f"Requisition progress updated to {percentage}%.")
        else:
            await ctx.send("Invalid message ID.")

    @commands.command(name='mm_feedback')
    async def mm_feedback(self, ctx, message_id: int, *, feedback: str):
        """Collect feedback from requesters after a requisition is completed"""
        if message_id in self.active_requisitions:
            self.active_requisitions[message_id]['feedback'] = feedback
            await ctx.send("Thank you for your feedback!")
        else:
            await ctx.send("Invalid message ID.")

async def setup(bot):
    await bot.add_cog(RequisitionFlow(bot))