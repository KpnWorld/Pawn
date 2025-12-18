"""Loyalty Module - Creed, Leaderboards, Roles"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from typing import Optional
import bot as bot_module
from format import (
    create_module_help_embed,
    create_command_reference_embed,
    create_info_embed,
    create_success_embed,
    create_error_embed
)

class Loyalty(commands.Cog):
    """Manage creed messages, loyalty roles, and leaderboards"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(name='l', aliases=['loyalty'])
    async def loyalty(self, ctx):
        """🎖️ Loyalty Module - Control creed and network joining"""
        if ctx.invoked_subcommand is None:
            commands_list = [
                {
                    "name": "l creed <#channel> <msg>",
                    "description": "Set the creed message and opt-in channel"
                },
                {
                    "name": "l leaderboard <#channel> <5|10>",
                    "description": "Set up leaderboard dashboard (top 5 or 10)"
                },
                {
                    "name": "l leaderboard refresh",
                    "description": "Manually refresh the leaderboard"
                },
                {
                    "name": "l role <@role>",
                    "description": "Set the loyalty reward role"
                },
                {
                    "name": "l user stats <@user>",
                    "description": "View a user's loyalty stats"
                },
                {
                    "name": "l user leave",
                    "description": "Leave the loyalty network"
                }
            ]
            
            embed = create_module_help_embed(
                "Loyalty",
                "🎖️",
                "Manage creed messages, loyalty roles, and leaderboards",
                commands_list,
                ctx.guild
            )
            await ctx.send(embed=embed)
    
    @loyalty.command(name='creed', aliases=['c'])
    @commands.has_permissions(administrator=True)
    async def set_creed(self, ctx, channel: discord.TextChannel, *, message: str):
        """Set creed message and opt-in channel"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        # Check if trusted (admin bypass)
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="You must be an admin or trusted to use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            # Send creed message to channel
            creed_embed = discord.Embed(
                title="🤝 Join the Loyalty Program",
                description=message,
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            creed_embed.add_field(
                name="How to Join",
                value="React with ✅ below to join!",
                inline=False
            )
            if ctx.guild.icon:
                creed_embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                creed_embed.set_footer(text="Prime Network")
            
            creed_msg = await channel.send(embed=creed_embed)
            await creed_msg.add_reaction("✅")
            
            # Save to guild data
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            guild_data["creed_message_id"] = creed_msg.id
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Creed Message Set",
                description=f"Creed message posted in {channel.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to set creed: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @loyalty.command(name='leaderboard', aliases=['lb'])
    @commands.has_permissions(administrator=True)
    async def set_leaderboard(self, ctx, channel: discord.TextChannel, threshold: str = "10"):
        """Set up leaderboard dashboard"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="You must be an admin or trusted to use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            if threshold not in ["5", "10"]:
                threshold = "10"
            
            # Create initial leaderboard
            embed = discord.Embed(
                title="🏆 Prime Network Leaderboard",
                description="Loading top members...",
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            if ctx.guild.icon:
                embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            
            msg = await channel.send(embed=embed)
            
            # Save to guild data
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            guild_data["dashboard_channel_id"] = channel.id
            guild_data["dashboard_msg_id"] = msg.id
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Leaderboard Set",
                description=f"Leaderboard dashboard set in {channel.mention}\nShowing top {threshold}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to set leaderboard: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @loyalty.command(name='refresh')
    @commands.has_permissions(administrator=True)
    async def refresh_leaderboard(self, ctx):
        """Manually refresh the leaderboard"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="You must be an admin or trusted to use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            dashboard_channel_id = guild_data.get("dashboard_channel_id")
            dashboard_msg_id = guild_data.get("dashboard_msg_id")
            
            if not dashboard_channel_id or not dashboard_msg_id:
                embed = create_error_embed(
                    title="Not Configured",
                    description="Leaderboard not yet configured. Use `$ l leaderboard` first.",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
                return
            
            channel = ctx.guild.get_channel(int(dashboard_channel_id))
            if not channel:
                embed = create_error_embed(
                    title="Channel Not Found",
                    description="Leaderboard channel no longer exists.",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
                return
            
            # Create updated leaderboard
            top_users = bot_module.DATA.get("global_users", {})
            loyal_users = [(uid, u) for uid, u in top_users.items() if u.get("is_loyal", False)]
            loyal_users.sort(key=lambda x: x[1].get("streak", 0), reverse=True)
            
            medals = ["🥇", "🥈", "🥉"]
            leaderboard_text = ""
            
            for idx, (user_id_str, user_data) in enumerate(loyal_users[:10], 1):
                member = ctx.guild.get_member(int(user_id_str))
                username = member.display_name if member else f"User {user_id_str}"
                
                if idx <= 3:
                    position = medals[idx - 1]
                else:
                    position = f"`#{idx:02d}`"
                
                streak = user_data.get("streak", 0)
                messages = user_data.get("total_messages", 0)
                leaderboard_text += f"{position} **{username}**\n└─ {messages} msgs • {streak}🔥\n"
            
            if not leaderboard_text:
                leaderboard_text = "No loyal members yet."
            
            embed = discord.Embed(
                title="🏆 Prime Network Leaderboard",
                description=leaderboard_text,
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            if ctx.guild.icon:
                embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            
            msg = await channel.fetch_message(int(dashboard_msg_id))
            await msg.edit(embed=embed)
            
            embed = create_success_embed(
                title="Leaderboard Refreshed",
                description="Leaderboard updated successfully",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to refresh leaderboard: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @loyalty.command(name='role', aliases=['r'])
    @commands.has_permissions(administrator=True)
    async def set_role(self, ctx, role: discord.Role):
        """Set the loyalty reward role"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="You must be an admin or trusted to use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            guild_data["loyal_role_id"] = role.id
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Loyalty Role Set",
                description=f"Loyalty role updated to {role.mention}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to set role: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    # User-only commands
    @commands.group(name='user', aliases=['u'])
    async def user_group(self, ctx):
        """User loyalty commands (no admin required)"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `$ user <@user>` or `$ user leave`")
    
    @user_group.command(name='stats', aliases=['s', 'info'])
    async def user_stats(self, ctx, member: Optional[discord.Member] = None):
        """View a user's loyalty stats in this guild"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        if member is None:
            member = ctx.author
        
        if member is None:
            await ctx.send("❌ User not found.")
            return
        
        try:
            user_data = bot_module.get_user_data(member.id)
            
            embed = discord.Embed(
                title=f"👤 {member.display_name}'s Loyalty Stats",
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            
            if member and member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            
            embed.add_field(
                name="Status",
                value="✅ Loyal" if user_data.get("is_loyal", False) else "❌ Not Loyal",
                inline=True
            )
            
            embed.add_field(
                name="Streak",
                value=f"{user_data.get('streak', 0)} days",
                inline=True
            )
            
            embed.add_field(
                name="Join Date",
                value=user_data.get("opt_in_date", "N/A"),
                inline=True
            )
            
            embed.add_field(
                name="Total Messages",
                value=str(user_data.get("total_messages", 0)),
                inline=True
            )
            
            embed.add_field(
                name="Last Active",
                value=user_data.get("last_activity", "N/A"),
                inline=True
            )
            
            if ctx.guild.icon:
                embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to retrieve stats: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @user_group.command(name='leave')
    async def leave_network(self, ctx):
        """Leave the loyalty network"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        try:
            user_data = bot_module.get_user_data(ctx.author.id)
            user_data["is_loyal"] = False
            user_data["streak"] = 0
            
            # Remove role from current guild
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            if guild_data.get("loyal_role_id"):
                role = ctx.guild.get_role(guild_data["loyal_role_id"])
                if role:
                    try:
                        await ctx.author.remove_roles(role)
                    except:
                        pass
            
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Left Network",
                description="You have left the loyalty network.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to leave: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot: commands.Bot):
    """Load the Loyalty cog"""
    await bot.add_cog(Loyalty(bot))
