import discord
from discord.ext import commands
from typing import Optional, Literal
import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import from bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import (
    DATA,
    save_data,
    get_loyal_member_count,
    get_active_loyal_count,
    is_owner,
    BRAND_COLOR,
    BOT_OWNER_ID
)

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed,
    create_network_stats_embed
)

def is_owner_check():
    """Decorator to check if user is owner"""
    async def predicate(ctx):
        if not is_owner(ctx.author.id):
            embed = discord.Embed(
                title="❌ Owner Only",
                description="This command can only be used by the bot owner.",
                color=BRAND_COLOR
            )
            if ctx.guild and ctx.guild.icon:
                embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            await ctx.send(embed=embed)
            return False
        return True
    return commands.check(predicate)

class Sudo(commands.Cog):
    """Sudo module - Owner-only administration and diagnostics"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== SUDO GROUP ====================
    
    @commands.group(name='sudo', aliases=['su'], invoke_without_command=True)
    @is_owner_check()
    async def sudo(self, ctx):
        """Sudo system commands (owner only)"""
        commands_page1 = [
            {
                "name": "Remove Trusted User",
                "syntax": f"{ctx.prefix}su trusted remove <user_id>"
            },
            {
                "name": "Remove All Trusted",
                "syntax": f"{ctx.prefix}su trusted remove all"
            },
            {
                "name": "View Database Table",
                "syntax": f"{ctx.prefix}su schema view <table>"
            },
            {
                "name": "Check Schema Health",
                "syntax": f"{ctx.prefix}su schema health"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Sudo",
            module_icon="⚙️",
            description=f"Owner-only administration and diagnostics\n**Owner:** <@{BOT_OWNER_ID}>\n\n"
                       "**Features:**\n"
                       "• Trusted user management\n"
                       "• Database inspection\n"
                       "• Network statistics\n"
                       "• Bot control",
            commands=commands_page1,
            guild=ctx.guild,
            page=1,
            total_pages=2
        )
        
        await ctx.send(embed=embed)
    
    # ==================== TRUSTED SUBGROUP ====================
    
    @sudo.group(name='trusted', invoke_without_command=True)
    @is_owner_check()
    async def trusted(self, ctx):
        """Trusted user management"""
        # Show trusted users
        trusted_users = DATA.get("network_config", {}).get("trusted_users", [])
        
        users_text = ""
        for user_id in trusted_users:
            try:
                user = await self.bot.fetch_user(user_id)
                owner_tag = " **(Owner)**" if user_id == BOT_OWNER_ID else ""
                users_text += f"• {user.mention} - `{user.id}`{owner_tag}\n"
            except:
                users_text += f"• User ID: `{user_id}`\n"
        
        if not users_text:
            users_text = "No trusted users configured."
        
        embed = create_info_embed(
            title="🔐 Trusted Admins",
            description=f"**Total:** {len(trusted_users)}\n\n{users_text}",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @trusted.command(name='remove', aliases=['rm'])
    @is_owner_check()
    async def trusted_remove(self, ctx, user_id: str):
        """
        Remove user from global trusted list
        
        Usage: $ su trusted remove 123456789
        Usage: $ su trusted remove all
        """
        trusted_users = DATA.get("network_config", {}).get("trusted_users", [])
        
        if user_id.lower() == "all":
            # Remove all except owner
            removed = [uid for uid in trusted_users if uid != BOT_OWNER_ID]
            DATA["network_config"]["trusted_users"] = [BOT_OWNER_ID]
            save_data()
            
            embed = create_success_embed(
                title="All Trusted Removed",
                description=f"Removed {len(removed)} trusted users.\nOwner cannot be removed.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Validate user ID
        if not user_id.isdigit():
            embed = create_error_embed(
                title="Invalid User ID",
                description="Please provide a valid numeric user ID or 'all'.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        user_id_int = int(user_id)
        
        # Cannot remove owner
        if user_id_int == BOT_OWNER_ID:
            embed = create_error_embed(
                title="Cannot Remove Owner",
                description="The bot owner cannot be removed from trusted list.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user is trusted
        if user_id_int not in trusted_users:
            embed = create_error_embed(
                title="Not Trusted",
                description=f"User `{user_id}` is not in the trusted list.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Remove from list
        trusted_users.remove(user_id_int)
        DATA["network_config"]["trusted_users"] = trusted_users
        save_data()
        
        # Fetch user info
        try:
            user = await self.bot.fetch_user(user_id_int)
            user_name = f"{user.name} ({user.id})"
        except:
            user_name = f"User ID: {user_id}"
        
        embed = create_success_embed(
            title="Trusted Removed",
            description=f"**{user_name}** has been removed from trusted admins.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== SCHEMA SUBGROUP ====================
    
    @sudo.group(name='schema', invoke_without_command=True)
    @is_owner_check()
    async def schema(self, ctx):
        """Database schema commands"""
        commands_list = [
            {
                "name": "View Table",
                "syntax": f"{ctx.prefix}su schema view <table>"
            },
            {
                "name": "Check Health",
                "syntax": f"{ctx.prefix}su schema health"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Sudo - Schema",
            module_icon="💾",
            description="Database inspection tools\n\n**Available tables:**\n"
                       "`network_config`, `global_blacklist`, `global_users`, `guilds`, `stats`",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @schema.command(name='view')
    @is_owner_check()
    async def schema_view(self, ctx, table: str):
        """
        Inspect raw JSON table (truncated to 1950 chars)
        
        Usage: $ su schema view network_config
        """
        valid_tables = ["network_config", "global_blacklist", "global_users", "guilds", "stats"]
        
        if table not in valid_tables:
            embed = create_error_embed(
                title="Invalid Table",
                description=f"Valid tables: {', '.join(valid_tables)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Get table data
        table_data = DATA.get(table, {})
        json_str = json.dumps(table_data, indent=2)
        
        # Truncate if too long
        if len(json_str) > 1950:
            json_str = json_str[:1950] + "\n... (truncated)"
        
        embed = create_info_embed(
            title=f"📊 Database Table: {table}",
            description=f"```json\n{json_str}\n```",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @schema.command(name='health')
    @is_owner_check()
    async def schema_health(self, ctx):
        """
        Validate database structure
        
        Usage: $ su schema health
        """
        issues = []
        
        # Check for required tables
        required_tables = ["network_config", "global_blacklist", "global_users", "guilds", "stats"]
        for table in required_tables:
            if table not in DATA:
                issues.append(f"❌ Missing table: `{table}`")
        
        # Check network_config structure
        if "network_config" in DATA:
            required_fields = ["main_hub_id", "main_hub_invite", "system_active", "trusted_users"]
            for field in required_fields:
                if field not in DATA["network_config"]:
                    issues.append(f"❌ Missing field in network_config: `{field}`")
        
        # Check stats structure
        if "stats" in DATA:
            required_fields = ["daily_joins", "daily_leaves", "activity_snapshots"]
            for field in required_fields:
                if field not in DATA["stats"]:
                    issues.append(f"❌ Missing field in stats: `{field}`")
        
        if issues:
            embed = create_error_embed(
                title="Schema Issues Found",
                description="\n".join(issues),
                guild=ctx.guild
            )
        else:
            embed = create_success_embed(
                title="Schema Healthy",
                description="✅ All tables and fields present\n✅ Database structure valid",
                guild=ctx.guild
            )
        
        await ctx.send(embed=embed)
    
    # ==================== STATS SUBGROUP ====================
    
    @sudo.group(name='stats', invoke_without_command=True)
    @is_owner_check()
    async def stats(self, ctx):
        """Network statistics commands"""
        commands_list = [
            {
                "name": "Network Overview",
                "syntax": f"{ctx.prefix}su stats overview"
            },
            {
                "name": "Activity Stats",
                "syntax": f"{ctx.prefix}su stats activity"
            },
            {
                "name": "Network Trends",
                "syntax": f"{ctx.prefix}su stats network"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Sudo - Statistics",
            module_icon="📈",
            description="View network-wide statistics and trends",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @stats.command(name='overview')
    @is_owner_check()
    async def stats_overview(self, ctx):
        """
        Total gateways, users, loyal count, blacklisted, trusted admins
        
        Usage: $ su stats overview
        """
        total_guilds = len(DATA.get("guilds", {}))
        total_users = len(DATA.get("global_users", {}))
        loyal_count = get_loyal_member_count()
        active_loyal = get_active_loyal_count()
        blacklisted = len(DATA.get("global_blacklist", []))
        trusted_count = len(DATA.get("network_config", {}).get("trusted_users", []))
        
        embed = create_network_stats_embed(
            total_guilds=total_guilds,
            total_users=total_users,
            loyal_count=loyal_count,
            active_loyal=active_loyal,
            blacklisted=blacklisted,
            trusted_count=trusted_count,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @stats.command(name='activity')
    @is_owner_check()
    async def stats_activity(self, ctx):
        """
        Active members today, activity percentage, avg messages, avg streak
        
        Usage: $ su stats activity
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Count active today
        active_today = 0
        total_messages = 0
        total_streak = 0
        loyal_count = 0
        
        for user_data in DATA.get("global_users", {}).values():
            if user_data.get("is_loyal"):
                loyal_count += 1
                total_messages += user_data.get("total_messages", 0)
                total_streak += user_data.get("streak", 0)
                
                if user_data.get("last_activity") == today:
                    active_today += 1
        
        activity_percentage = (active_today / loyal_count * 100) if loyal_count > 0 else 0
        avg_messages = (total_messages / loyal_count) if loyal_count > 0 else 0
        avg_streak = (total_streak / loyal_count) if loyal_count > 0 else 0
        
        embed = discord.Embed(
            title="📊 Activity Statistics",
            description=f"**Active Today:** {active_today} members\n"
                       f"**Activity Rate:** {activity_percentage:.1f}%\n"
                       f"**Avg Messages:** {avg_messages:.1f} per member\n"
                       f"**Avg Streak:** {avg_streak:.1f} days",
            color=BRAND_COLOR
        )
        
        if ctx.guild and ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        
        await ctx.send(embed=embed)
    
    @stats.command(name='network')
    @is_owner_check()
    async def stats_network(self, ctx):
        """
        7-day join/leave trends with ASCII visualization
        
        Usage: $ su stats network
        """
        daily_joins = DATA.get("stats", {}).get("daily_joins", {})
        daily_leaves = DATA.get("stats", {}).get("daily_leaves", {})
        
        # Get last 7 days
        trends_text = "**Last 7 Days:**\n```"
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            joins = daily_joins.get(date, 0)
            leaves = daily_leaves.get(date, 0)
            net = joins - leaves
            
            # Simple ASCII bar
            bar_joins = "+" * min(joins, 20)
            bar_leaves = "-" * min(leaves, 20)
            
            trends_text += f"{date}: +{joins:2d} -{leaves:2d} (net: {net:+3d})\n"
        
        trends_text += "```"
        
        embed = discord.Embed(
            title="📈 Network Trends",
            description=trends_text,
            color=BRAND_COLOR
        )
        
        if ctx.guild and ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        
        await ctx.send(embed=embed)
    
    # ==================== BOT SUBGROUP ====================
    
    @sudo.group(name='bot', invoke_without_command=True)
    @is_owner_check()
    async def bot_control(self, ctx):
        """Bot control commands"""
        commands_list = [
            {
                "name": "Change Presence",
                "syntax": f"{ctx.prefix}su bot presence switch <type> <msg>"
            },
            {
                "name": "Reset Presence",
                "syntax": f"{ctx.prefix}su bot presence default"
            },
            {
                "name": "Manage Cogs",
                "syntax": f"{ctx.prefix}su bot cog <load|reload|unload> <cog>"
            },
            {
                "name": "Command Count",
                "syntax": f"{ctx.prefix}su bot cmds"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Sudo - Bot Control",
            module_icon="🤖",
            description="Control bot behavior and modules",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @bot_control.group(name='presence', invoke_without_command=True)
    @is_owner_check()
    async def presence(self, ctx):
        """Presence commands"""
        pass
    
    @presence.command(name='switch')
    @is_owner_check()
    async def presence_switch(self, ctx, activity_type: Literal['streaming', 'playing', 'listening', 'watching'], *, message: str):
        """
        Change bot status
        
        Usage: $ su bot presence switch playing Prime Network
        """
        activity_map = {
            'streaming': discord.Streaming(name=message, url="https://twitch.tv/pawnbot"),
            'playing': discord.Game(name=message),
            'listening': discord.Activity(type=discord.ActivityType.listening, name=message),
            'watching': discord.Activity(type=discord.ActivityType.watching, name=message)
        }
        
        activity = activity_map.get(activity_type)
        if not activity:
            embed = create_error_embed(
                title="Invalid Type",
                description="Valid types: streaming, playing, listening, watching",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        await self.bot.change_presence(activity=activity)
        
        embed = create_success_embed(
            title="Presence Updated",
            description=f"Bot is now **{activity_type}** `{message}`",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @presence.command(name='default')
    @is_owner_check()
    async def presence_default(self, ctx):
        """
        Reset status to display loyal member count
        
        Usage: $ su bot presence default
        """
        count = get_loyal_member_count()
        activity = discord.Streaming(
            name=f"{count} loyal members",
            url="https://twitch.tv/pawnbot"
        )
        await self.bot.change_presence(activity=activity)
        
        embed = create_success_embed(
            title="Presence Reset",
            description=f"Bot presence reset to default: `{count} loyal members`",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    @bot_control.command(name='cog')
    @is_owner_check()
    async def cog_manage(self, ctx, action: Literal['load', 'reload', 'unload'], cog: str):
        """
        Dynamically load/reload/unload modules
        
        Usage: $ su bot cog reload loyalty
        """
        cog_name = f"cogs.{cog}"
        
        try:
            if action == 'load':
                await self.bot.load_extension(cog_name)
                message = f"Loaded `{cog}` module"
            elif action == 'reload':
                await self.bot.reload_extension(cog_name)
                message = f"Reloaded `{cog}` module"
            elif action == 'unload':
                await self.bot.unload_extension(cog_name)
                message = f"Unloaded `{cog}` module"
            else:
                embed = create_error_embed(
                    title="Invalid Action",
                    description="Valid actions: load, reload, unload",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
                return
            
            embed = create_success_embed(
                title="Cog Updated",
                description=message,
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                title="Cog Error",
                description=f"Failed to {action} `{cog}`: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    @bot_control.command(name='cmds', aliases=['commands'])
    @is_owner_check()
    async def bot_commands(self, ctx):
        """
        Display total commands available
        
        Usage: $ su bot cmds
        """
        total_commands = len(self.bot.commands)
        cogs_loaded = len(self.bot.cogs)
        
        cog_list = "\n".join([f"• {cog}" for cog in self.bot.cogs.keys()])
        
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description=f"**Total Commands:** {total_commands}\n"
                       f"**Cogs Loaded:** {cogs_loaded}\n\n"
                       f"**Loaded Cogs:**\n{cog_list}",
            color=BRAND_COLOR
        )
        
        if ctx.guild and ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        
        await ctx.send(embed=embed)

# ==================== COG SETUP ====================

async def setup(bot):
    await bot.add_cog(Sudo(bot))