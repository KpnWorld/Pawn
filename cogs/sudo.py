"""Sudo Module - Bot Owner Commands"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional
import bot as bot_module
from stats import (
    get_network_overview,
    get_activity_stats,
    get_network_trends,
    validate_schema,
    record_activity_snapshot
)
from format import (
    create_module_help_embed,
    create_info_embed,
    create_success_embed,
    create_error_embed,
    create_stats_overview_embed,
    create_activity_stats_embed,
    create_trend_embed
)

BOT_OWNER_ID = 895767962722660372

class Sudo(commands.Cog):
    """Bot owner utilities and system diagnostics"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def _is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        return user_id == BOT_OWNER_ID
    
    @commands.group(name='su', aliases=['sudo'])
    async def sudo(self, ctx):
        """⚙️ Sudo Module - Bot owner controls"""
        if not self._is_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Bot owner only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if ctx.invoked_subcommand is None:
            commands_list = [
                {
                    "name": "su trusted remove <user_id>",
                    "description": "Remove trusted admin"
                },
                {
                    "name": "su schema view <table>",
                    "description": "View database table"
                },
                {
                    "name": "su schema health",
                    "description": "Check schema integrity"
                },
                {
                    "name": "su stats overview",
                    "description": "Network statistics"
                },
                {
                    "name": "su stats activity",
                    "description": "Activity statistics"
                },
                {
                    "name": "su stats network",
                    "description": "Join/leave trends"
                },
                {
                    "name": "su bot presence switch <type> <msg>",
                    "description": "Change bot status"
                },
                {
                    "name": "su bot presence default",
                    "description": "Reset to default presence"
                },
                {
                    "name": "su bot cog <load|reload|unload> <cog>",
                    "description": "Manage cogs"
                },
                {
                    "name": "su bot cmds",
                    "description": "Command count"
                }
            ]
            
            embed = create_module_help_embed(
                "Sudo",
                "⚙️",
                "Bot owner utilities and system diagnostics",
                commands_list,
                ctx.guild
            )
            await ctx.send(embed=embed)
    
    @sudo.group(name='trusted')
    async def trusted_mgmt(self, ctx):
        """Manage trusted users"""
        if not self._is_owner(ctx.author.id):
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ su trusted remove <user_id>` or `remove all`")
    
    @trusted_mgmt.command(name='remove')
    async def remove_trusted(self, ctx, target: str):
        """Remove trusted user"""
        if not self._is_owner(ctx.author.id):
            return
        
        try:
            if target.lower() == "all":
                bot_module.DATA["network_config"]["trusted_users"] = [BOT_OWNER_ID]
                bot_module.save_data()
                embed = create_success_embed(
                    title="All Trusted Removed",
                    description="Only bot owner remains trusted",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            else:
                user_id = int(target)
                if user_id != BOT_OWNER_ID and user_id in bot_module.DATA["network_config"]["trusted_users"]:
                    bot_module.DATA["network_config"]["trusted_users"].remove(user_id)
                    bot_module.save_data()
                    embed = create_success_embed(
                        title="Trusted Removed",
                        description=f"<@{user_id}> removed from trusted",
                        guild=ctx.guild
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = create_error_embed(
                        title="Cannot Remove",
                        description="User not trusted or is bot owner",
                        guild=ctx.guild
                    )
                    await ctx.send(embed=embed, delete_after=5)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=str(e),
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @sudo.group(name='schema')
    async def schema(self, ctx):
        """Database schema management"""
        if not self._is_owner(ctx.author.id):
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ su schema view <table>`, `health`, or `reload`")
    
    @schema.command(name='view')
    async def view_table(self, ctx, table: str):
        """View database table"""
        if not self._is_owner(ctx.author.id):
            return
        
        tables = {
            "network_config": bot_module.DATA.get("network_config", {}),
            "global_blacklist": bot_module.DATA.get("global_blacklist", []),
            "guilds": bot_module.DATA.get("guilds", {}),
            "stats": bot_module.DATA.get("stats", {}),
            "global_users": bot_module.DATA.get("global_users", {})
        }
        
        if table not in tables:
            embed = create_error_embed(
                title="Table Not Found",
                description=f"Available tables: {', '.join(tables.keys())}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        data_str = str(tables[table])[:1950]  # Truncate if too long
        embed = create_info_embed(
            title=f"Table: {table}",
            description=f"```json\n{data_str}\n```",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @schema.command(name='health')
    async def check_health(self, ctx):
        """Check schema integrity"""
        if not self._is_owner(ctx.author.id):
            return
        
        is_valid, errors = validate_schema()
        
        if is_valid:
            embed = create_success_embed(
                title="Schema Health ✅",
                description="All tables valid",
                guild=ctx.guild
            )
        else:
            error_list = "\n".join(f"• {e}" for e in errors[:10])
            embed = create_error_embed(
                title="Schema Issues ⚠️",
                description=f"```\n{error_list}\n```",
                guild=ctx.guild
            )
        
        await ctx.send(embed=embed)
    
    @sudo.group(name='stats')
    async def stats_group(self, ctx):
        """Network statistics"""
        if not self._is_owner(ctx.author.id):
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ su stats overview`, `activity`, or `network`")
    
    @stats_group.command(name='overview')
    async def stats_overview(self, ctx):
        """Network overview statistics"""
        if not self._is_owner(ctx.author.id):
            return
        
        stats = get_network_overview()
        embed = create_stats_overview_embed(stats, ctx.guild)
        await ctx.send(embed=embed)
    
    @stats_group.command(name='activity')
    async def stats_activity(self, ctx):
        """Activity statistics"""
        if not self._is_owner(ctx.author.id):
            return
        
        stats = get_activity_stats()
        embed = create_activity_stats_embed(stats, ctx.guild)
        await ctx.send(embed=embed)
    
    @stats_group.command(name='network')
    async def stats_network(self, ctx):
        """Network join/leave trends"""
        if not self._is_owner(ctx.author.id):
            return
        
        trends = get_network_trends(days=7)
        embed = create_trend_embed(trends["trends"], ctx.guild)
        await ctx.send(embed=embed)
    
    @sudo.group(name='bot')
    async def control(self, ctx):
        """Bot control commands"""
        if not self._is_owner(ctx.author.id):
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ su bot presence`, `cog`, or `cmds`")
    
    @control.group(name='presence')
    async def presence_control(self, ctx):
        """Bot presence control"""
        if not self._is_owner(ctx.author.id):
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ su bot presence switch` or `default`")
    
    @presence_control.command(name='switch')
    async def change_presence(self, ctx, activity_type: str, *, message: str):
        """Change bot presence"""
        if not self._is_owner(ctx.author.id):
            return
        
        try:
            activity_type = activity_type.lower()
            
            if activity_type == "streaming":
                activity = discord.Streaming(name=message, url="https://twitch.tv/pawnbot")
                status = discord.Status.online
            elif activity_type == "playing":
                activity = discord.Game(name=message)
                status = discord.Status.online
            elif activity_type == "listening":
                activity = discord.Activity(type=discord.ActivityType.listening, name=message)
                status = discord.Status.online
            elif activity_type == "watching":
                activity = discord.Activity(type=discord.ActivityType.watching, name=message)
                status = discord.Status.online
            else:
                embed = create_error_embed(
                    title="Invalid Type",
                    description="Use: streaming, playing, listening, or watching",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
                return
            
            await self.bot.change_presence(status=status, activity=activity)
            
            embed = create_success_embed(
                title="Presence Updated",
                description=f"Bot now {activity_type}: {message}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=str(e),
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @presence_control.command(name='default')
    async def default_presence(self, ctx):
        """Reset to default presence"""
        if not self._is_owner(ctx.author.id):
            return
        
        count = bot_module.get_loyal_count()
        activity = discord.Streaming(
            name=f"{count} loyal members",
            url="https://twitch.tv/pawnbot"
        )
        await self.bot.change_presence(activity=activity)
        
        embed = create_success_embed(
            title="Presence Reset",
            description="Bot presence set to default",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @control.command(name='cog')
    async def manage_cog(self, ctx, action: str, cog_name: str):
        """Load/unload/reload cogs"""
        if not self._is_owner(ctx.author.id):
            return
        
        action = action.lower()
        
        try:
            if action == "load":
                await self.bot.load_extension(f"cogs.{cog_name}")
                embed = create_success_embed(
                    title="Cog Loaded",
                    description=f"Loaded cogs.{cog_name}",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            
            elif action == "unload":
                await self.bot.unload_extension(f"cogs.{cog_name}")
                embed = create_success_embed(
                    title="Cog Unloaded",
                    description=f"Unloaded cogs.{cog_name}",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            
            elif action == "reload":
                await self.bot.reload_extension(f"cogs.{cog_name}")
                embed = create_success_embed(
                    title="Cog Reloaded",
                    description=f"Reloaded cogs.{cog_name}",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            
            else:
                embed = create_error_embed(
                    title="Invalid Action",
                    description="Use: load, unload, or reload",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=str(e),
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @control.command(name='cmds')
    async def command_count(self, ctx):
        """Show total command count"""
        if not self._is_owner(ctx.author.id):
            return
        
        commands_count = len(self.bot.commands)
        embed = create_info_embed(
            title="Command Count",
            description=f"Total commands: **{commands_count}**",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Load the Sudo cog"""
    await bot.add_cog(Sudo(bot))
