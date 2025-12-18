"""Security Module - Bans, Timeouts, Trusted Users"""
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from typing import Optional
import bot as bot_module
from format import (
    create_module_help_embed,
    create_info_embed,
    create_success_embed,
    create_error_embed
)

class Security(commands.Cog):
    """Network security, bans, timeouts, and system control"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(name='sec', aliases=['security'])
    async def security(self, ctx):
        """🔒 Security Module - Network security and control"""
        if ctx.invoked_subcommand is None:
            commands_list = [
                {
                    "name": "sec ban <user_id>",
                    "description": "Ban user from all networks"
                },
                {
                    "name": "sec timeout <user_id> <time>",
                    "description": "Timeout user (5min-60min)"
                },
                {
                    "name": "sec stop",
                    "description": "Stop the loyalty system"
                },
                {
                    "name": "sec start",
                    "description": "Start the loyalty system"
                },
                {
                    "name": "sec trusted add <@user>",
                    "description": "Add trusted admin"
                }
            ]
            
            embed = create_module_help_embed(
                "Security",
                "🔒",
                "Network security, bans, timeouts, and system control",
                commands_list,
                ctx.guild
            )
            await ctx.send(embed=embed)
    
    @security.command(name='ban')
    @commands.has_permissions(administrator=True)
    async def ban_user(self, ctx, user_id: int):
        """Ban user from all network servers"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Add to global blacklist
            if user_id not in bot_module.DATA["global_blacklist"]:
                bot_module.DATA["global_blacklist"].append(user_id)
            
            # Mark user as blacklisted
            user_data = bot_module.get_user_data(user_id)
            user_data["is_loyal"] = False
            user_data["is_muted"] = False
            
            # Ban from all servers
            for guild_id_str, guild_config in bot_module.DATA.get("guilds", {}).items():
                guild = self.bot.get_guild(int(guild_id_str))
                if guild:
                    try:
                        user_obj = await self.bot.fetch_user(user_id)
                        await guild.ban(user_obj, reason="Network ban")
                    except:
                        pass
            
            bot_module.save_data()
            
            embed = create_success_embed(
                title="User Banned",
                description=f"<@{user_id}> has been banned from the network",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to ban user: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @security.command(name='timeout')
    @commands.has_permissions(administrator=True)
    async def timeout_user(self, ctx, user_id: int, duration: str):
        """Timeout user on all servers"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Parse duration (e.g., "10m", "1h")
            minutes = 0
            if duration.endswith("m"):
                minutes = int(duration[:-1])
            elif duration.endswith("h"):
                minutes = int(duration[:-1]) * 60
            else:
                minutes = int(duration)
            
            # Clamp between 5 and 60 minutes
            minutes = min(max(minutes, 5), 60)
            
            timeout_duration = timedelta(minutes=minutes)
            
            # Timeout on all servers
            for guild_id_str, guild_config in bot_module.DATA.get("guilds", {}).items():
                guild = self.bot.get_guild(int(guild_id_str))
                if guild:
                    try:
                        member = guild.get_member(user_id)
                        if member:
                            await member.timeout(timeout_duration, reason="Network timeout")
                    except:
                        pass
            
            embed = create_success_embed(
                title="User Timed Out",
                description=f"<@{user_id}> timed out for {minutes} minutes across all servers",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to timeout user: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @security.command(name='stop')
    @commands.has_permissions(administrator=True)
    async def stop_system(self, ctx):
        """Stop the loyalty system"""
        if not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Trusted admin only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        bot_module.DATA["network_config"]["system_active"] = False
        bot_module.save_data()
        
        embed = create_success_embed(
            title="System Stopped",
            description="Loyalty system has been disabled",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @security.command(name='start')
    @commands.has_permissions(administrator=True)
    async def start_system(self, ctx):
        """Start the loyalty system"""
        if not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Trusted admin only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        bot_module.DATA["network_config"]["system_active"] = True
        bot_module.save_data()
        
        embed = create_success_embed(
            title="System Started",
            description="Loyalty system has been enabled",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @security.group(name='trusted')
    async def trusted_group(self, ctx):
        """Manage trusted admins"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ sec trusted add <@user>` or remove")
    
    @trusted_group.command(name='add')
    @commands.has_permissions(administrator=True)
    async def add_trusted(self, ctx, user: discord.User):
        """Add user to trusted list"""
        if not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Trusted admin only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if user.id not in bot_module.DATA["network_config"]["trusted_users"]:
            bot_module.DATA["network_config"]["trusted_users"].append(user.id)
            bot_module.save_data()
            
            embed = create_success_embed(
                title="User Trusted",
                description=f"{user.mention} added to trusted list",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        else:
            embed = create_info_embed(
                title="Already Trusted",
                description=f"{user.mention} is already trusted",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot: commands.Bot):
    """Load the Security cog"""
    await bot.add_cog(Security(bot))
