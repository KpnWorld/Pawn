import discord
from discord.ext import commands
from typing import Optional, Union
from datetime import datetime
import sys
import os

# Add parent directory to path to import from bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import (
    DATA, 
    save_data, 
    get_guild_data, 
    get_user_data,
    BRAND_COLOR,
    MAIN_HUB_ID,
    STREAK_MESSAGE_THRESHOLD
)

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed,
    create_leaderboard_embed,
    create_user_stats_embed
)

class Loyalty(commands.Cog):
    """Loyalty module - Manage creed messages, loyalty roles, and leaderboards"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== LOYALTY GROUP ====================
    
    @commands.group(name='loyalty', aliases=['l'], invoke_without_command=True)
    async def loyalty(self, ctx):
        """Loyalty system commands"""
        if not ctx.guild:
            return
        
        # Create module help embed with all commands
        commands_list = [
            {
                "name": "Set Creed",
                "syntax": f"{ctx.prefix}l creed <#channel> <message>"
            },
            {
                "name": "Setup Leaderboard",
                "syntax": f"{ctx.prefix}l leaderboard <#channel> <5|10>"
            },
            {
                "name": "Refresh Leaderboard",
                "syntax": f"{ctx.prefix}l refresh"
            },
            {
                "name": "Set Loyalty Role",
                "syntax": f"{ctx.prefix}l role <@role>"
            },
            {
                "name": "View User Stats",
                "syntax": f"{ctx.prefix}l user stats <@user>"
            },
            {
                "name": "Leave Network",
                "syntax": f"{ctx.prefix}l user leave"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Loyalty",
            module_icon="🎖️",
            description="Manage creed messages, loyalty roles, and leaderboard dashboards per server.\n\n"
                       "**Streak System:** Gain 1 streak day per 100 messages\n"
                       "**Inactive Status:** 7+ days without activity",
            commands=commands_list,
            guild=ctx.guild
        )
        
        await ctx.send(embed=embed)
    
    # ==================== CREED COMMAND ====================
    
    @loyalty.command(name='creed')
    @commands.has_permissions(administrator=True)
    async def creed(self, ctx, channel: discord.TextChannel, *, message: str):
        """
        Post creed message with ✅ reaction for users to opt-in
        
        Usage: $ l creed #general Welcome to our loyalty program!
        """
        if not ctx.guild:
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        
        # Create creed embed
        embed = discord.Embed(
            title="🤝 Loyalty Program",
            description=f"{message}\n\n**React with ✅ to join the loyalty program!**",
            color=BRAND_COLOR
        )
        
        embed.add_field(
            name="Benefits",
            value="• Exclusive role\n• Priority in events\n• Network-wide tracking\n• Access to hub server",
            inline=False
        )
        
        embed.add_field(
            name="How It Works",
            value=f"• Gain 1 streak day per {STREAK_MESSAGE_THRESHOLD} messages\n• Stay active to maintain status\n• 7+ days inactive = marked inactive",
            inline=False
        )
        
        if ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        
        # Post creed message
        try:
            creed_msg = await channel.send(embed=embed)
            await creed_msg.add_reaction("✅")
            
            # Save creed message ID and channel
            guild_data["creed_message_id"] = creed_msg.id
            guild_data["creed_channel_id"] = channel.id
            save_data()
            
            # Confirm to admin
            confirm_embed = create_success_embed(
                title="Creed Posted",
                description=f"Creed message posted in {channel.mention}\n"
                           f"Users can now react with ✅ to join!\n\n"
                           f"[Jump to message]({creed_msg.jump_url})",
                guild=ctx.guild
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            embed = create_error_embed(
                title="Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to post creed: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    # ==================== LEADERBOARD COMMAND ====================
    
    @loyalty.command(name='leaderboard', aliases=['lb'])
    @commands.has_permissions(administrator=True)
    async def leaderboard(self, ctx, channel: discord.TextChannel, count: int = 10):
        """
        Setup leaderboard dashboard in channel
        
        Usage: $ l leaderboard #leaderboard 10
        """
        if not ctx.guild:
            return
        
        if count not in [5, 10]:
            embed = create_error_embed(
                title="Invalid Count",
                description="Leaderboard count must be 5 or 10",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        
        # Get top loyal members by streak (active only)
        loyal_members = []
        for user_id_str, user_data in DATA.get("global_users", {}).items():
            if user_data.get("is_loyal") and not user_data.get("is_inactive", False):
                loyal_members.append({
                    "user_id": int(user_id_str),
                    "messages": user_data.get("total_messages", 0),
                    "streak": user_data.get("streak", 0)
                })
        
        loyal_members.sort(key=lambda x: (x["streak"], x["messages"]), reverse=True)
        top_members = loyal_members[:count]
        
        # Create leaderboard embed
        embed = create_leaderboard_embed(
            title=f"Top {count} Loyal Members",
            members=top_members,
            guild=ctx.guild
        )
        
        try:
            dashboard_msg = await channel.send(embed=embed)
            
            # Save dashboard location
            guild_data["dashboard_msg_id"] = dashboard_msg.id
            guild_data["dashboard_channel_id"] = channel.id
            save_data()
            
            # Confirm
            confirm_embed = create_success_embed(
                title="Leaderboard Created",
                description=f"Leaderboard dashboard created in {channel.mention}\n"
                           f"Auto-updates every 4 hours\n\n"
                           f"[Jump to leaderboard]({dashboard_msg.jump_url})",
                guild=ctx.guild
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            embed = create_error_embed(
                title="Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    # ==================== REFRESH COMMAND ====================
    
    @loyalty.command(name='refresh')
    @commands.has_permissions(administrator=True)
    async def refresh(self, ctx):
        """
        Manually refresh leaderboard dashboard
        
        Usage: $ l refresh
        """
        if not ctx.guild:
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        
        dashboard_channel_id = guild_data.get("dashboard_channel_id")
        dashboard_msg_id = guild_data.get("dashboard_msg_id")
        
        if not dashboard_channel_id or not dashboard_msg_id:
            embed = create_error_embed(
                title="No Dashboard",
                description=f"No leaderboard dashboard configured.\nUse `{ctx.prefix}l leaderboard` first.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        channel = ctx.guild.get_channel(dashboard_channel_id)
        if not channel:
            embed = create_error_embed(
                title="Channel Not Found",
                description="Dashboard channel no longer exists.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Get top 10 active loyal members
        loyal_members = []
        for user_id_str, user_data in DATA.get("global_users", {}).items():
            if user_data.get("is_loyal") and not user_data.get("is_inactive", False):
                loyal_members.append({
                    "user_id": int(user_id_str),
                    "messages": user_data.get("total_messages", 0),
                    "streak": user_data.get("streak", 0)
                })
        
        loyal_members.sort(key=lambda x: (x["streak"], x["messages"]), reverse=True)
        top_10 = loyal_members[:10]
        
        embed = create_leaderboard_embed(
            title="Top 10 Loyal Members",
            members=top_10,
            guild=ctx.guild
        )
        
        try:
            msg = await channel.fetch_message(dashboard_msg_id)
            await msg.edit(embed=embed)
            
            confirm_embed = create_success_embed(
                title="Leaderboard Refreshed",
                description=f"Dashboard updated in {channel.mention}\n\n"
                           f"[Jump to leaderboard]({msg.jump_url})",
                guild=ctx.guild
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.NotFound:
            embed = create_error_embed(
                title="Message Not Found",
                description=f"Dashboard message no longer exists.\nUse `{ctx.prefix}l leaderboard` to create a new one.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = create_error_embed(
                title="Permission Error",
                description="I don't have permission to edit messages in that channel.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    # ==================== ROLE COMMAND ====================
    
    @loyalty.command(name='role')
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, role: discord.Role):
        """
        Set loyalty role for this server
        
        Usage: $ l role @Loyal
        """
        if not ctx.guild:
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        guild_data["loyal_role_id"] = role.id
        save_data()
        
        embed = create_success_embed(
            title="Loyalty Role Set",
            description=f"Loyalty role set to {role.mention}\n\n"
                       f"Users who react to the creed message will receive this role automatically.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== USER SUBGROUP ====================
    
    @loyalty.group(name='user', invoke_without_command=True)
    async def user(self, ctx):
        """User loyalty commands"""
        commands_list = [
            {
                "name": "View User Stats",
                "syntax": f"{ctx.prefix}l user stats <@user>"
            },
            {
                "name": "Leave Network",
                "syntax": f"{ctx.prefix}l user leave"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Loyalty - User Commands",
            module_icon="👤",
            description="View stats and manage your loyalty status",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== USER STATS COMMAND ====================
    
    @user.command(name='stats')
    async def user_stats(self, ctx, user: Optional[Union[discord.Member, discord.User]] = None):
        """
        View loyalty statistics for a user
        
        Usage: $ l user stats @user
        """
        if not ctx.guild:
            return
        
        target = user or ctx.author
        
        # Ensure we have a Member object, not just User
        if isinstance(target, discord.User):
            # Try to get the member from the guild
            member = ctx.guild.get_member(target.id)
            if not member:
                embed = create_error_embed(
                    title="User Not Found",
                    description=f"User is not in this server.",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
                return
            target = member
        
        user_data = get_user_data(target.id)
        
        if not user_data.get("is_loyal"):
            embed = create_error_embed(
                title="Not Loyal",
                description=f"{target.mention} is not in the loyalty network.\n\n"
                           f"React to the creed message with ✅ to join!",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Use the enhanced user stats embed
        embed = create_user_stats_embed(
            user=target,
            user_data=user_data,
            guild=ctx.guild
        )
        
        await ctx.send(embed=embed)
    
    # ==================== USER LEAVE COMMAND ====================
    
    @user.command(name='leave')
    async def user_leave(self, ctx):
        """
        Leave the loyalty network
        
        Usage: $ l user leave
        """
        if not ctx.guild:
            return
        
        user_data = get_user_data(ctx.author.id)
        
        if not user_data.get("is_loyal"):
            embed = create_error_embed(
                title="Not in Network",
                description="You're not in the loyalty network.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Remove loyalty status
        user_data["is_loyal"] = False
        user_data["is_inactive"] = False
        user_data["streak"] = 0
        user_data["messages_since_last_streak"] = 0
        user_data["opt_in_date"] = None
        user_data["main_server_id"] = None
        user_data["main_server_name"] = None
        
        # Update stats
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in DATA["stats"]["daily_leaves"]:
            DATA["stats"]["daily_leaves"][today] = 0
        DATA["stats"]["daily_leaves"][today] += 1
        
        save_data()
        
        # Remove role from current guild
        guild_data = get_guild_data(ctx.guild.id)
        if guild_data.get("loyal_role_id"):
            role = ctx.guild.get_role(guild_data["loyal_role_id"])
            if role and role in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(role)
                except:
                    pass
        
        embed = create_success_embed(
            title="Left Network",
            description="You've been removed from the loyalty network.\n"
                       "Your streak and stats have been reset.\n\n"
                       "You can rejoin anytime by reacting to the creed message with ✅",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)

# ==================== COG SETUP ====================

async def setup(bot):
    await bot.add_cog(Loyalty(bot))