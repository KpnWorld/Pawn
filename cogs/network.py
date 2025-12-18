"""Network Module - Broadcasting, Invites, Guild Management"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional
import random
import asyncio
import bot as bot_module
from format import (
    create_module_help_embed,
    create_command_reference_embed,
    create_info_embed,
    create_success_embed,
    create_error_embed
)

class Network(commands.Cog):
    """Control global network broadcasting, invites, and guild management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(name='net', aliases=['network'])
    async def network(self, ctx):
        """🌐 Network Module - Control global network"""
        if ctx.invoked_subcommand is None:
            commands_list = [
                {
                    "name": "net guild",
                    "description": "View guild settings"
                },
                {
                    "name": "net guild prefix <prefix>",
                    "description": "Change bot prefix for this guild"
                },
                {
                    "name": "net guild ann <#channel>",
                    "description": "Set announcement channel"
                },
                {
                    "name": "net broadcast dm <msg>",
                    "description": "DM loyal members in this gateway"
                },
                {
                    "name": "net broadcast global dm <msg>",
                    "description": "DM all loyal members network-wide"
                },
                {
                    "name": "net invite",
                    "description": "Send hub invite to loyal members"
                },
                {
                    "name": "net pick <amount>",
                    "description": "Pick random members (1-10)"
                },
                {
                    "name": "net dm <user_id/username> <msg>",
                    "description": "Send DM to specific user"
                }
            ]
            
            embed = create_module_help_embed(
                "Network",
                "🌐",
                "Control global network broadcasting and invites",
                commands_list,
                ctx.guild
            )
            await ctx.send(embed=embed)
    
    @network.group(name='guild')
    @commands.has_permissions(administrator=True)
    async def guild_group(self, ctx):
        """Guild management commands"""
        if ctx.invoked_subcommand is None:
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            embed = create_info_embed(
                title=f"{ctx.guild.name} Settings",
                description=f"Prefix: `{guild_data.get('prefix', '$')}`\n"
                           f"Announcement Channel: {guild_data.get('announcement_channel') or 'Not Set'}\n"
                           f"Broadcast Channel: {guild_data.get('broadcast_channel') or 'Not Set'}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    @guild_group.command(name='prefix')
    async def set_prefix(self, ctx, prefix: str):
        """Change bot prefix for this guild"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if len(prefix) > 3:
            embed = create_error_embed(
                title="Invalid Prefix",
                description="Prefix must be 3 characters or less",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        guild_data = bot_module.get_guild_data(ctx.guild.id)
        guild_data["prefix"] = prefix
        bot_module.save_data()
        
        embed = create_success_embed(
            title="Prefix Updated",
            description=f"New prefix: `{prefix}`",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @guild_group.command(name='ann', aliases=['announcement'])
    async def set_announcement(self, ctx, channel: discord.TextChannel):
        """Set announcement channel"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        guild_data = bot_module.get_guild_data(ctx.guild.id)
        guild_data["announcement_channel"] = channel.id
        bot_module.save_data()
        
        embed = create_success_embed(
            title="Announcement Channel Set",
            description=f"Announcements will go to {channel.mention}",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @commands.group(name='broadcast', aliases=['bc'])
    @commands.has_permissions(administrator=True)
    async def broadcast(self, ctx):
        """Broadcast messages to loyal members"""
        if ctx.invoked_subcommand is None:
            embed = create_info_embed(
                title="Broadcast Help",
                description="Use:\n`$ broadcast dm <msg>` - Local gateway\n`$ broadcast global dm <msg>` - All servers",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    @broadcast.command(name='dm')
    async def broadcast_local(self, ctx, *, message: str):
        """Broadcast DM to loyal members in this gateway"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Get loyal members in this gateway
            loyal_in_gateway = [
                int(uid) for uid, u in bot_module.DATA["global_users"].items()
                if u.get("is_loyal", False) and u.get("active_location_id") == ctx.guild.id
            ]
            
            sent = 0
            failed = 0
            
            for user_id in loyal_in_gateway:
                try:
                    user = await self.bot.fetch_user(user_id)
                    embed = discord.Embed(
                        title=f"Message from {ctx.guild.name}",
                        description=message,
                        color=0x2B2D31,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await user.send(embed=embed)
                    sent += 1
                    await asyncio.sleep(1)  # Rate limit
                except:
                    failed += 1
            
            embed = create_success_embed(
                title="Broadcast Complete",
                description=f"✅ Sent: {sent}\n❌ Failed: {failed}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Broadcast failed: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @broadcast.group(name='global')
    async def broadcast_global_group(self, ctx):
        """Global broadcast commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ broadcast global dm <msg>`")
    
    @broadcast_global_group.command(name='dm')
    async def broadcast_global_dm(self, ctx, *, message: str):
        """Broadcast DM to ALL loyal members"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Get all loyal members
            loyal_users = [
                int(uid) for uid, u in bot_module.DATA["global_users"].items()
                if u.get("is_loyal", False)
            ]
            
            sent = 0
            failed = 0
            
            for user_id in loyal_users:
                try:
                    user = await self.bot.fetch_user(user_id)
                    embed = discord.Embed(
                        title="🌐 Network-Wide Message",
                        description=message,
                        color=0x2B2D31,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await user.send(embed=embed)
                    sent += 1
                    await asyncio.sleep(1)  # Rate limit
                except:
                    failed += 1
            
            embed = create_success_embed(
                title="Global Broadcast Complete",
                description=f"✅ Sent: {sent}\n❌ Failed: {failed}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Global broadcast failed: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='invite', aliases=['inv'])
    @commands.has_permissions(administrator=True)
    async def send_invite(self, ctx):
        """Send hub invite to loyal members in this gateway"""
        if ctx.guild.id == bot_module.MAIN_HUB_ID:
            embed = create_error_embed(
                title="Cannot Use in Hub",
                description="This command is for gateway servers only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            loyal_in_gateway = [
                int(uid) for uid, u in bot_module.DATA["global_users"].items()
                if u.get("is_loyal", False) and u.get("active_location_id") == ctx.guild.id
            ]
            
            sent = 0
            failed = 0
            
            for user_id in loyal_in_gateway:
                try:
                    user = await self.bot.fetch_user(user_id)
                    embed = discord.Embed(
                        title="🏢 Join the Main Hub",
                        description=f"You're invited to the Prime Network Main Hub!\n\n{bot_module.MAIN_HUB_INVITE}",
                        color=0x2B2D31,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await user.send(embed=embed)
                    sent += 1
                    await asyncio.sleep(1)
                except:
                    failed += 1
            
            embed = create_success_embed(
                title="Invites Sent",
                description=f"✅ Sent: {sent}\n❌ Failed: {failed}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to send invites: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='pick')
    @commands.has_permissions(administrator=True)
    async def pick_random(self, ctx, amount: int = 1):
        """Pick random loyal members"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        amount = min(max(amount, 1), 10)  # Clamp between 1-10
        
        loyal_users = [
            int(uid) for uid, u in bot_module.DATA["global_users"].items()
            if u.get("is_loyal", False)
        ]
        
        if len(loyal_users) < amount:
            embed = create_error_embed(
                title="Not Enough Members",
                description=f"Only {len(loyal_users)} loyal members available",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        picked = random.sample(loyal_users, amount)
        
        picked_text = "\n".join(f"• <@{uid}>" for uid in picked)
        embed = create_info_embed(
            title=f"🎲 Random Pick ({amount})",
            description=picked_text,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='dm', aliases=['message'])
    @commands.has_permissions(administrator=True)
    async def send_dm(self, ctx, user_input: str, *, message: str):
        """Send DM to a specific user via bot"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Try to parse as user ID
            try:
                user_id = int(user_input)
                user = await self.bot.fetch_user(user_id)
            except:
                # Try to find by name
                user = None
                for member in ctx.guild.members:
                    if user_input.lower() in member.name.lower():
                        user = member
                        break
            
            if not user:
                embed = create_error_embed(
                    title="User Not Found",
                    description="Could not find user",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
                return
            
            embed = discord.Embed(
                title=f"Message from {ctx.guild.name}",
                description=message,
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            await user.send(embed=embed)
            
            embed = create_success_embed(
                title="DM Sent",
                description=f"Message sent to {user.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to send DM: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot: commands.Bot):
    """Load the Network cog"""
    await bot.add_cog(Network(bot))
