import discord
from discord.ext import commands
from typing import Optional, Union
import random
import asyncio
import sys
import os

# Add parent directory to path to import from bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import (
    DATA,
    save_data,
    get_guild_data,
    get_user_data,
    check_user_in_hub,
    BRAND_COLOR,
    MAIN_HUB_ID,
    MAIN_HUB_NAME,
    HUB_INVITE,
    HUB_ANN_CHANNEL_ID
)

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed,
    create_guild_config_embed
)

class Network(commands.Cog):
    """Network module - Manage network-wide communications, guild settings, and invites"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== NETWORK GROUP ====================
    
    @commands.group(name='network', aliases=['net'], invoke_without_command=True)
    async def network(self, ctx):
        """Network system commands"""
        if not ctx.guild:
            return
        
        # Create module help embed - Page 1
        commands_page1 = [
            {
                "name": "View Guild Config",
                "syntax": f"{ctx.prefix}net guild"
            },
            {
                "name": "Change Prefix",
                "syntax": f"{ctx.prefix}net guild prefix <prefix>"
            },
            {
                "name": "Setup Announcements",
                "syntax": f"{ctx.prefix}net guild ann <#channel>"
            },
            {
                "name": "Local Broadcast DM",
                "syntax": f"{ctx.prefix}net broadcast dm <message>"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Network",
            module_icon="🌐",
            description="Manage network-wide communications, guild settings, and invites.\n\n"
                       "**Features:**\n"
                       "• Guild configuration & prefix management\n"
                       "• Hub announcement channel following\n"
                       "• Mass DM broadcasts (local & global)\n"
                       "• Hub invites & random member selection",
            commands=commands_page1,
            guild=ctx.guild,
            page=1,
            total_pages=2
        )
        
        await ctx.send(embed=embed)
    
    # ==================== GUILD SUBGROUP ====================
    
    @network.group(name='guild', aliases=['g'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def guild(self, ctx):
        """Guild configuration commands"""
        if not ctx.guild:
            return
        
        # Show current guild configuration
        guild_data = get_guild_data(ctx.guild.id)
        embed = create_guild_config_embed(
            guild=ctx.guild,
            guild_data=guild_data
        )
        await ctx.send(embed=embed)
    
    # ==================== PREFIX COMMAND ====================
    
    @guild.command(name='prefix', aliases=['p'])
    @commands.has_permissions(administrator=True)
    async def guild_prefix(self, ctx, prefix: str):
        """
        Change bot prefix for this guild
        
        Usage: $ net guild prefix !
        """
        if not ctx.guild:
            return
        
        if len(prefix) > 3:
            embed = create_error_embed(
                title="Prefix Too Long",
                description="Prefix must be 3 characters or less.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        old_prefix = guild_data.get("prefix", "$")
        guild_data["prefix"] = prefix
        save_data()
        
        embed = create_success_embed(
            title="Prefix Updated",
            description=f"Bot prefix changed from `{old_prefix}` to `{prefix}`\n\n"
                       f"Example: `{prefix}net guild`",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== ANNOUNCEMENT CHANNEL COMMAND ====================
    
    @guild.command(name='ann', aliases=['announcement', 'announcements'])
    @commands.has_permissions(administrator=True)
    async def guild_announcement(self, ctx, channel: discord.TextChannel):
        """
        Setup channel to receive Prime Network announcements
        
        Usage: $ net guild ann #announcements
        """
        if not ctx.guild:
            return
        
        # Get hub announcement channel
        hub = self.bot.get_guild(MAIN_HUB_ID)
        if not hub:
            embed = create_error_embed(
                title="Hub Not Found",
                description="Cannot locate main hub server.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        hub_channel = hub.get_channel(HUB_ANN_CHANNEL_ID)
        if not hub_channel:
            embed = create_error_embed(
                title="Announcement Channel Not Found",
                description="Cannot locate hub announcement channel.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Check bot permissions
        permissions = channel.permissions_for(ctx.guild.me)
        if not permissions.manage_channels or not permissions.manage_webhooks:
            embed = create_error_embed(
                title="Missing Permissions",
                description="I need **Manage Channels** and **Manage Webhooks** permissions in that channel.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Make channel read-only for @everyone
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                reason="Prime Network announcement channel - read-only"
            )
            
            # Follow the hub announcement channel
            webhook = await hub_channel.follow(destination=channel)
            
            # Save configuration
            guild_data = get_guild_data(ctx.guild.id)
            guild_data["announcement_channel"] = channel.id
            guild_data["hub_ann_channel_id"] = HUB_ANN_CHANNEL_ID
            save_data()
            
            embed = create_success_embed(
                title="Announcement Channel Setup",
                description=f"✅ {channel.mention} is now following Prime Network announcements\n"
                           f"✅ Channel set to read-only\n"
                           f"✅ Webhook created: {webhook.name}\n\n"
                           f"All announcements from the hub will appear here automatically!",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = create_error_embed(
                title="Permission Error",
                description="Failed to set up announcement channel. Check bot permissions.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed(
                title="Setup Failed",
                description=f"Error: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    # ==================== BROADCAST SUBGROUP ====================
    
    @network.group(name='broadcast', aliases=['bc'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def broadcast(self, ctx):
        """Broadcast commands"""
        commands_list = [
            {
                "name": "Local Broadcast",
                "syntax": f"{ctx.prefix}net broadcast dm <message>"
            },
            {
                "name": "Global Broadcast",
                "syntax": f"{ctx.prefix}net broadcast global dm <message>"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Network - Broadcast",
            module_icon="📢",
            description="Send DMs to loyal members (1 second delay between messages)",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== LOCAL BROADCAST DM ====================
    
    @broadcast.command(name='dm')
    @commands.has_permissions(administrator=True)
    async def broadcast_dm(self, ctx, *, message: str):
        """
        DM all loyal members in current guild
        
        Usage: $ net broadcast dm Hello everyone!
        """
        if not ctx.guild:
            return
        
        # Get loyal members in this guild (by main server)
        loyal_members = []
        for user_id_str, user_data in DATA.get("global_users", {}).items():
            if user_data.get("is_loyal") and user_data.get("main_server_id") == ctx.guild.id:
                member = ctx.guild.get_member(int(user_id_str))
                if member:
                    loyal_members.append(member)
        
        if not loyal_members:
            embed = create_error_embed(
                title="No Loyal Members",
                description="No loyal members found in this guild.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm broadcast
        confirm_embed = create_info_embed(
            title="Confirm Broadcast",
            description=f"Send DM to **{len(loyal_members)}** loyal members in this server?\n\n"
                       f"Preview:\n```{message[:100]}{'...' if len(message) > 100 else ''}```",
            guild=ctx.guild
        )
        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = create_error_embed(
                    title="Broadcast Cancelled",
                    description="Broadcast has been cancelled.",
                    guild=ctx.guild
                )
                await confirm_msg.edit(embed=embed)
                return
            
            # Send broadcast
            sent = 0
            failed = 0
            
            status_embed = create_info_embed(
                title="Sending Broadcast",
                description=f"Sending to {len(loyal_members)} members...",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=status_embed)
            
            for member in loyal_members:
                try:
                    dm_embed = discord.Embed(
                        title=f"📢 Message from {ctx.guild.name}",
                        description=message,
                        color=BRAND_COLOR
                    )
                    if ctx.guild.icon:
                        dm_embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
                    else:
                        dm_embed.set_footer(text="Prime Network")
                    
                    await member.send(embed=dm_embed)
                    sent += 1
                except:
                    failed += 1
                
                await asyncio.sleep(1)  # 1 second delay
            
            # Final result
            result_embed = create_success_embed(
                title="Broadcast Complete",
                description=f"✅ Sent to {sent} members\n❌ Failed to send to {failed} members",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            embed = create_error_embed(
                title="Broadcast Timeout",
                description="Confirmation timed out. Broadcast cancelled.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== GLOBAL BROADCAST ====================
    
    @broadcast.group(name='global', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def broadcast_global(self, ctx):
        """Global broadcast commands"""
        pass
    
    @broadcast_global.command(name='dm')
    @commands.has_permissions(administrator=True)
    async def broadcast_global_dm(self, ctx, *, message: str):
        """
        DM all loyal members network-wide
        
        Usage: $ net broadcast global dm Network announcement!
        """
        if not ctx.guild:
            return
        
        # Get ALL loyal members
        loyal_user_ids = [int(uid) for uid, data in DATA.get("global_users", {}).items() 
                         if data.get("is_loyal") and not data.get("is_inactive")]
        
        if not loyal_user_ids:
            embed = create_error_embed(
                title="No Loyal Members",
                description="No loyal members found in the network.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm broadcast
        confirm_embed = create_info_embed(
            title="⚠️ Confirm Global Broadcast",
            description=f"Send DM to **{len(loyal_user_ids)}** loyal members **NETWORK-WIDE**?\n\n"
                       f"Preview:\n```{message[:100]}{'...' if len(message) > 100 else ''}```\n\n"
                       f"This will take approximately {len(loyal_user_ids)} seconds.",
            guild=ctx.guild
        )
        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = create_error_embed(
                    title="Broadcast Cancelled",
                    description="Global broadcast has been cancelled.",
                    guild=ctx.guild
                )
                await confirm_msg.edit(embed=embed)
                return
            
            # Send global broadcast
            sent = 0
            failed = 0
            
            status_embed = create_info_embed(
                title="Sending Global Broadcast",
                description=f"Sending to {len(loyal_user_ids)} network members...",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=status_embed)
            
            for user_id in loyal_user_ids:
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        dm_embed = discord.Embed(
                            title="📢 Prime Network Announcement",
                            description=message,
                            color=BRAND_COLOR
                        )
                        dm_embed.set_footer(text="Prime Network")
                        
                        await user.send(embed=dm_embed)
                        sent += 1
                except:
                    failed += 1
                
                await asyncio.sleep(1)  # 1 second delay
            
            # Final result
            result_embed = create_success_embed(
                title="Global Broadcast Complete",
                description=f"✅ Sent to {sent} members\n❌ Failed to send to {failed} members",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            embed = create_error_embed(
                title="Broadcast Timeout",
                description="Confirmation timed out. Broadcast cancelled.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== INVITE COMMAND ====================
    
    @network.command(name='invite', aliases=['inv'])
    @commands.has_permissions(administrator=True)
    async def invite(self, ctx):
        """
        Send hub invite to loyal members in this gateway
        
        Usage: $ net invite
        """
        if not ctx.guild:
            return
        
        # Check if this is the hub
        if ctx.guild.id == MAIN_HUB_ID:
            embed = create_error_embed(
                title="Cannot Use in Hub",
                description=f"This command cannot be used in {MAIN_HUB_NAME} (main hub).",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Get loyal members NOT in hub
        loyal_members = []
        for user_id_str, user_data in DATA.get("global_users", {}).items():
            if user_data.get("is_loyal") and user_data.get("main_server_id") == ctx.guild.id:
                user_id = int(user_id_str)
                if not check_user_in_hub(user_id):
                    member = ctx.guild.get_member(user_id)
                    if member:
                        loyal_members.append(member)
        
        if not loyal_members:
            embed = create_info_embed(
                title="No Members to Invite",
                description=f"All loyal members are already in {MAIN_HUB_NAME}!",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Send invites
        sent = 0
        failed = 0
        
        for member in loyal_members:
            try:
                invite_embed = discord.Embed(
                    title=f"🏢 Invitation to {MAIN_HUB_NAME}",
                    description=f"Hello from **{ctx.guild.name}**!\n\n"
                               f"As a loyal member, you're invited to join **{MAIN_HUB_NAME}**, "
                               f"the main hub of Prime Network.\n\n"
                               f"**Invite Link:**\n{HUB_INVITE}",
                    color=BRAND_COLOR
                )
                if ctx.guild.icon:
                    invite_embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
                else:
                    invite_embed.set_footer(text="Prime Network")
                
                await member.send(embed=invite_embed)
                sent += 1
            except:
                failed += 1
            
            await asyncio.sleep(1)
        
        result_embed = create_success_embed(
            title="Hub Invites Sent",
            description=f"✅ Sent to {sent} loyal members\n❌ Failed to send to {failed} members",
            guild=ctx.guild
        )
        await ctx.send(embed=result_embed)
    
    # ==================== PICK RANDOM COMMAND ====================
    
    @network.command(name='pick', aliases=['random'])
    @commands.has_permissions(administrator=True)
    async def pick(self, ctx, count: int = 1):
        """
        Pick random loyal members from network
        
        Usage: $ net pick 5
        """
        if not ctx.guild:
            return
        
        if count < 1 or count > 10:
            embed = create_error_embed(
                title="Invalid Count",
                description="Please pick between 1 and 10 members.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Get all active loyal members
        loyal_user_ids = [int(uid) for uid, data in DATA.get("global_users", {}).items() 
                         if data.get("is_loyal") and not data.get("is_inactive")]
        
        if not loyal_user_ids:
            embed = create_error_embed(
                title="No Loyal Members",
                description="No loyal members found in the network.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        if count > len(loyal_user_ids):
            count = len(loyal_user_ids)
        
        # Pick random members
        selected = random.sample(loyal_user_ids, count)
        
        members_text = ""
        for user_id in selected:
            try:
                user = await self.bot.fetch_user(user_id)
                members_text += f"• {user.mention} (`{user.id}`)\n"
            except:
                members_text += f"• User ID: `{user_id}`\n"
        
        embed = create_info_embed(
            title=f"🎲 Random Pick - {count} Member{'s' if count != 1 else ''}",
            description=members_text,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== DM USER COMMAND ====================
    
    @network.command(name='dm')
    @commands.has_permissions(administrator=True)
    async def dm_user(self, ctx, user: Union[discord.Member, discord.User, str], *, message: str):
        """
        Send DM to specific user
        
        Usage: $ net dm @user Hello!
        Usage: $ net dm 123456789 Hello!
        Usage: $ net dm username Hello!
        """
        if not ctx.guild:
            return
        
        target_user = None
        
        # If user is a string, try to find by ID or name
        if isinstance(user, str):
            # Try as ID
            if user.isdigit():
                try:
                    target_user = await self.bot.fetch_user(int(user))
                except:
                    pass
            
            # Try as name if ID failed
            if not target_user:
                for member in ctx.guild.members:
                    if user.lower() in member.name.lower() or user.lower() in member.display_name.lower():
                        target_user = member
                        break
        else:
            target_user = user
        
        if not target_user:
            embed = create_error_embed(
                title="User Not Found",
                description="Could not find that user.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Send DM
        try:
            dm_embed = discord.Embed(
                title=f"📨 Message from {ctx.author.display_name}",
                description=message,
                color=BRAND_COLOR
            )
            if ctx.guild.icon:
                dm_embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                dm_embed.set_footer(text="Prime Network")
            
            await target_user.send(embed=dm_embed)
            
            confirm_embed = create_success_embed(
                title="DM Sent",
                description=f"Message sent to {target_user.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            embed = create_error_embed(
                title="DM Failed",
                description=f"Cannot send DM to {target_user.mention}. They may have DMs disabled.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)

# ==================== COG SETUP ====================

async def setup(bot):
    await bot.add_cog(Network(bot))