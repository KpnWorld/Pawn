import discord
from discord.ext import commands
from typing import Optional
from datetime import timedelta
import sys
import os

# Add parent directory to path to import from bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import (
    DATA,
    save_data,
    is_trusted_user,
    is_owner,
    BRAND_COLOR,
    BOT_OWNER_ID
)

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed
)

class Security(commands.Cog):
    """Security module - Network-wide security, user management, and system control"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def check_trusted_or_owner(self, user_id: int) -> bool:
        """Check if user is trusted admin or owner"""
        return is_trusted_user(user_id) or is_owner(user_id)
    
    # ==================== SECURITY GROUP ====================
    
    @commands.group(name='security', aliases=['sec'], invoke_without_command=True)
    async def security(self, ctx):
        """Security system commands"""
        if not ctx.guild:
            return
        
        commands_list = [
            {
                "name": "Ban User",
                "syntax": f"{ctx.prefix}sec ban <user_id>"
            },
            {
                "name": "Timeout User",
                "syntax": f"{ctx.prefix}sec timeout <user_id> <5-60m>"
            },
            {
                "name": "Stop System",
                "syntax": f"{ctx.prefix}sec stop"
            },
            {
                "name": "Start System",
                "syntax": f"{ctx.prefix}sec start"
            },
            {
                "name": "Add Trusted User",
                "syntax": f"{ctx.prefix}sec trusted add <@user>"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Security",
            module_icon="🔒",
            description="Network-wide security, user management, and system control.\n\n"
                       "**Features:**\n"
                       "• Global blacklist (auto-ban from all servers)\n"
                       "• Network-wide timeouts\n"
                       "• System enable/disable controls\n"
                       "• Trusted admin management\n\n"
                       "**Required:** Trusted Admin or Owner",
            commands=commands_list,
            guild=ctx.guild
        )
        
        await ctx.send(embed=embed)
    
    # ==================== BAN COMMAND ====================
    
    @security.command(name='ban', aliases=['blacklist'])
    async def ban(self, ctx, user_id: str):
        """
        Add user to global blacklist (auto-ban from all servers)
        
        Usage: $ sec ban 123456789
        """
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Validate user ID
        if not user_id.isdigit():
            embed = create_error_embed(
                title="Invalid User ID",
                description="Please provide a valid numeric user ID.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        user_id_int = int(user_id)
        
        # Prevent banning owner or self
        if user_id_int == BOT_OWNER_ID:
            embed = create_error_embed(
                title="Cannot Ban Owner",
                description="You cannot ban the bot owner.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        if user_id_int == ctx.author.id:
            embed = create_error_embed(
                title="Cannot Ban Self",
                description="You cannot ban yourself.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Check if already banned
        if user_id in DATA.get("global_blacklist", []):
            embed = create_error_embed(
                title="Already Banned",
                description=f"User `{user_id}` is already on the global blacklist.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Add to blacklist
        if "global_blacklist" not in DATA:
            DATA["global_blacklist"] = []
        
        DATA["global_blacklist"].append(user_id)
        save_data()
        
        # Try to ban from all guilds
        banned_count = 0
        failed_count = 0
        
        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user_id_int)
                if member:
                    await guild.ban(member, reason=f"Global blacklist - Banned by {ctx.author}")
                    banned_count += 1
            except:
                failed_count += 1
        
        # Fetch user info
        try:
            user = await self.bot.fetch_user(user_id_int)
            user_name = f"{user.name} ({user.id})"
        except:
            user_name = f"User ID: {user_id}"
        
        embed = create_success_embed(
            title="User Banned",
            description=f"**{user_name}** added to global blacklist\n\n"
                       f"✅ Banned from {banned_count} servers\n"
                       f"❌ Failed in {failed_count} servers\n\n"
                       f"User will be auto-banned if they join any network server.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== TIMEOUT COMMAND ====================
    
    @security.command(name='timeout', aliases=['mute'])
    async def timeout(self, ctx, user_id: str, duration: str):
        """
        Apply Discord timeout across all servers (5-60 min)
        
        Usage: $ sec timeout 123456789 30m
        """
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Validate user ID
        if not user_id.isdigit():
            embed = create_error_embed(
                title="Invalid User ID",
                description="Please provide a valid numeric user ID.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        user_id_int = int(user_id)
        
        # Parse duration
        if not duration.endswith('m'):
            embed = create_error_embed(
                title="Invalid Duration",
                description="Duration must end with 'm' (minutes). Example: 30m",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        try:
            minutes = int(duration[:-1])
        except:
            embed = create_error_embed(
                title="Invalid Duration",
                description="Please provide a valid number. Example: 30m",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Clamp to 5-60 minutes
        if minutes < 5:
            minutes = 5
        elif minutes > 60:
            minutes = 60
        
        timeout_duration = timedelta(minutes=minutes)
        
        # Apply timeout to all guilds
        timed_out_count = 0
        failed_count = 0
        
        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user_id_int)
                if member:
                    await member.timeout(timeout_duration, reason=f"Network-wide timeout by {ctx.author}")
                    timed_out_count += 1
            except:
                failed_count += 1
        
        # Fetch user info
        try:
            user = await self.bot.fetch_user(user_id_int)
            user_name = f"{user.name} ({user.id})"
        except:
            user_name = f"User ID: {user_id}"
        
        embed = create_success_embed(
            title="User Timed Out",
            description=f"**{user_name}** timed out for **{minutes} minutes**\n\n"
                       f"✅ Timed out in {timed_out_count} servers\n"
                       f"❌ Failed in {failed_count} servers\n\n"
                       f"User cannot send messages for {minutes} minutes.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== STOP SYSTEM ====================
    
    @security.command(name='stop', aliases=['disable'])
    async def stop_system(self, ctx):
        """
        Disable entire loyalty system (all commands blocked)
        
        Usage: $ sec stop
        """
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        if not DATA["network_config"]["system_active"]:
            embed = create_error_embed(
                title="Already Disabled",
                description="The loyalty system is already disabled.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm action
        confirm_embed = create_info_embed(
            title="⚠️ Confirm System Stop",
            description="Are you sure you want to disable the entire loyalty system?\n\n"
                       "**This will:**\n"
                       "• Block all loyalty commands\n"
                       "• Stop background tasks\n"
                       "• Prevent user opt-ins\n\n"
                       "React with ✅ to confirm or ❌ to cancel.",
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
                    title="Action Cancelled",
                    description="System stop cancelled.",
                    guild=ctx.guild
                )
                await confirm_msg.edit(embed=embed)
                return
            
            # Stop system
            DATA["network_config"]["system_active"] = False
            save_data()
            
            embed = create_success_embed(
                title="System Stopped",
                description=f"The loyalty system has been disabled by {ctx.author.mention}\n\n"
                           f"All commands are now blocked until system is restarted.\n"
                           f"Use `{ctx.prefix}sec start` to re-enable.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
            
        except:
            embed = create_error_embed(
                title="Confirmation Timeout",
                description="System stop cancelled due to timeout.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== START SYSTEM ====================
    
    @security.command(name='start', aliases=['enable'])
    async def start_system(self, ctx):
        """
        Re-enable loyalty system (all commands work again)
        
        Usage: $ sec start
        """
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        if DATA["network_config"]["system_active"]:
            embed = create_error_embed(
                title="Already Active",
                description="The loyalty system is already active.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Start system
        DATA["network_config"]["system_active"] = True
        save_data()
        
        embed = create_success_embed(
            title="System Started",
            description=f"The loyalty system has been re-enabled by {ctx.author.mention}\n\n"
                       f"All commands are now operational.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== TRUSTED SUBGROUP ====================
    
    @security.group(name='trusted', invoke_without_command=True)
    async def trusted(self, ctx):
        """Trusted user management"""
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Show current trusted users
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
    
    # ==================== ADD TRUSTED ====================
    
    @trusted.command(name='add')
    async def trusted_add(self, ctx, user: discord.Member):
        """
        Grant admin access to user (can use all module commands except sudo)
        
        Usage: $ sec trusted add @user
        """
        if not self.check_trusted_or_owner(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Only trusted admins and the owner can use this command.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Check if already trusted
        trusted_users = DATA.get("network_config", {}).get("trusted_users", [])
        if user.id in trusted_users:
            embed = create_error_embed(
                title="Already Trusted",
                description=f"{user.mention} is already a trusted admin.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Add to trusted list
        trusted_users.append(user.id)
        DATA["network_config"]["trusted_users"] = trusted_users
        save_data()
        
        embed = create_success_embed(
            title="Trusted Admin Added",
            description=f"{user.mention} has been added to the trusted admin list.\n\n"
                       f"**Permissions:**\n"
                       f"• Can use all loyalty, network, security, and server commands\n"
                       f"• Cannot use sudo (owner-only) commands\n"
                       f"• Can manage bans, timeouts, and system control",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
        
        # Send DM to user
        try:
            dm_embed = discord.Embed(
                title="🔐 Trusted Admin Access Granted",
                description=f"You've been granted trusted admin access in **Prime Network** by {ctx.author.mention}.\n\n"
                           f"You can now use all module commands except sudo.",
                color=BRAND_COLOR
            )
            if ctx.guild and ctx.guild.icon:
                dm_embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
            else:
                dm_embed.set_footer(text="Prime Network")
            await user.send(embed=dm_embed)
        except:
            pass

# ==================== COG SETUP ====================

async def setup(bot):
    await bot.add_cog(Security(bot))