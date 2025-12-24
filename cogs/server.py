import discord
from discord.ext import commands
from typing import Optional
import sys
import os

# Add parent directory to path to import from bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import (
    DATA,
    save_data,
    get_guild_data,
    is_trusted_user,
    is_owner,
    BRAND_COLOR,
    MAIN_HUB_ID,
    HUB_INVITE
)

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed,
    create_guild_config_embed
)

class Server(commands.Cog):
    """Server module - Server management and network membership"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def check_admin_or_trusted(self, ctx) -> bool:
        """Check if user is server admin or trusted"""
        return ctx.author.guild_permissions.administrator or is_trusted_user(ctx.author.id) or is_owner(ctx.author.id)
    
    # ==================== SERVER GROUP ====================
    
    @commands.group(name='server', aliases=['s'], invoke_without_command=True)
    async def server(self, ctx):
        """Server management commands"""
        if not ctx.guild:
            return
        
        commands_list = [
            {
                "name": "Rename Server",
                "syntax": f"{ctx.prefix}s name <newname>"
            },
            {
                "name": "Leave Network",
                "syntax": f"{ctx.prefix}s leave"
            },
            {
                "name": "Lock Server",
                "syntax": f"{ctx.prefix}s gate lock"
            },
            {
                "name": "Nuke Server",
                "syntax": f"{ctx.prefix}s gate nuke"
            },
            {
                "name": "View Config",
                "syntax": f"{ctx.prefix}s config"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Server",
            module_icon="🏢",
            description="Server management and network membership.\n\n"
                       "**Features:**\n"
                       "• Rename server\n"
                       "• Leave network (removes all data)\n"
                       "• Gate controls (lock/nuke)\n"
                       "• View server configuration\n\n"
                       "**Required:** Server Admin or Trusted",
            commands=commands_list,
            guild=ctx.guild
        )
        
        await ctx.send(embed=embed)
    
    # ==================== NAME COMMAND ====================
    
    @server.command(name='name', aliases=['rename'])
    @commands.has_permissions(administrator=True)
    async def name(self, ctx, *, new_name: str):
        """
        Change server name via bot
        
        Usage: $ s name My New Server Name
        """
        if not ctx.guild:
            return
        
        if len(new_name) > 100:
            embed = create_error_embed(
                title="Name Too Long",
                description="Server name must be 100 characters or less.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        old_name = ctx.guild.name
        
        try:
            await ctx.guild.edit(name=new_name, reason=f"Renamed by {ctx.author}")
            
            # Update in database
            guild_data = get_guild_data(ctx.guild.id)
            guild_data["name"] = new_name
            save_data()
            
            embed = create_success_embed(
                title="Server Renamed",
                description=f"**Old Name:** {old_name}\n**New Name:** {new_name}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = create_error_embed(
                title="Permission Error",
                description="I don't have permission to rename this server.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed(
                title="Rename Failed",
                description=f"Error: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
    
    # ==================== LEAVE COMMAND ====================
    
    @server.command(name='leave', aliases=['remove'])
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx):
        """
        Remove this server from network (deletes all data)
        
        Usage: $ s leave
        """
        if not ctx.guild:
            return
        
        # Check if this is the hub
        if ctx.guild.id == MAIN_HUB_ID:
            embed = create_error_embed(
                title="Cannot Leave Hub",
                description="The main hub cannot leave the network.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm action
        confirm_embed = create_info_embed(
            title="⚠️ Confirm Leave Network",
            description=f"Are you sure you want to remove **{ctx.guild.name}** from Prime Network?\n\n"
                       "**This will:**\n"
                       "• Delete ALL server data\n"
                       "• Remove all loyalty settings\n"
                       "• Clear creed and leaderboard\n"
                       "• Cannot be undone\n\n"
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
                    description="Server removal cancelled.",
                    guild=ctx.guild
                )
                await confirm_msg.edit(embed=embed)
                return
            
            # Remove guild data
            guild_id_str = str(ctx.guild.id)
            if guild_id_str in DATA.get("guilds", {}):
                del DATA["guilds"][guild_id_str]
                save_data()
            
            embed = create_success_embed(
                title="Left Network",
                description=f"**{ctx.guild.name}** has been removed from Prime Network.\n\n"
                           f"All server data has been deleted.\n"
                           f"Bot is now leaving the server...",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
            
            # Leave the server
            try:
                await ctx.guild.leave()
            except Exception as e:
                print(f"Failed to leave guild {ctx.guild.id}: {e}")
            
        except:
            embed = create_error_embed(
                title="Confirmation Timeout",
                description="Server removal cancelled due to timeout.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== GATE SUBGROUP ====================
    
    @server.group(name='gate', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def gate(self, ctx):
        """Gate control commands"""
        commands_list = [
            {
                "name": "Lock Server",
                "syntax": f"{ctx.prefix}s gate lock"
            },
            {
                "name": "Nuke Server",
                "syntax": f"{ctx.prefix}s gate nuke"
            }
        ]
        
        embed = create_module_help_embed(
            module_name="Server - Gate Controls",
            module_icon="🚪",
            description="Extreme server control measures",
            commands=commands_list,
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
    
    # ==================== LOCK COMMAND ====================
    
    @gate.command(name='lock')
    @commands.has_permissions(administrator=True)
    async def gate_lock(self, ctx):
        """
        Disable @everyone send messages (read-only server)
        
        Usage: $ s gate lock
        """
        if not ctx.guild:
            return
        
        # Confirm action
        confirm_embed = create_info_embed(
            title="⚠️ Confirm Server Lock",
            description=f"Lock **{ctx.guild.name}**?\n\n"
                       "**This will:**\n"
                       "• Disable @everyone send messages in ALL channels\n"
                       "• Server becomes read-only for regular members\n"
                       "• Admins and bots can still send messages\n\n"
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
                    description="Server lock cancelled.",
                    guild=ctx.guild
                )
                await confirm_msg.edit(embed=embed)
                return
            
            # Lock all channels
            locked_count = 0
            failed_count = 0
            
            for channel in ctx.guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    try:
                        await channel.set_permissions(
                            ctx.guild.default_role,
                            send_messages=False,
                            reason=f"Server locked by {ctx.author}"
                        )
                        locked_count += 1
                    except:
                        failed_count += 1
            
            embed = create_success_embed(
                title="Server Locked",
                description=f"**{ctx.guild.name}** is now in read-only mode.\n\n"
                           f"✅ Locked {locked_count} channels\n"
                           f"❌ Failed to lock {failed_count} channels\n\n"
                           f"Regular members cannot send messages.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
            
        except:
            embed = create_error_embed(
                title="Confirmation Timeout",
                description="Server lock cancelled due to timeout.",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== NUKE COMMAND ====================
    
    @gate.command(name='nuke')
    @commands.has_permissions(administrator=True)
    async def gate_nuke(self, ctx):
        """
        Delete all channels and roles, create read-only channel with hub invite
        
        Usage: $ s gate nuke
        """
        if not ctx.guild:
            return
        
        # Check if this is the hub
        if ctx.guild.id == MAIN_HUB_ID:
            embed = create_error_embed(
                title="Cannot Nuke Hub",
                description="The main hub cannot be nuked.",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm action with double confirmation
        confirm_embed = create_info_embed(
            title="🚨 CONFIRM SERVER NUKE 🚨",
            description=f"**DANGER:** Nuke **{ctx.guild.name}**?\n\n"
                       "**THIS WILL:**\n"
                       "• **DELETE ALL CHANNELS**\n"
                       "• **DELETE ALL ROLES**\n"
                       "• Create single read-only channel\n"
                       "• Post hub invite link\n"
                       "• **CANNOT BE UNDONE**\n\n"
                       "Type `NUKE` to confirm (you have 30 seconds)",
            guild=ctx.guild
        )
        confirm_msg = await ctx.send(embed=confirm_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == "NUKE"
        
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check)
            
            # Execute nuke
            status_embed = create_info_embed(
                title="🚨 Nuking Server...",
                description="Deleting all channels and roles...",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=status_embed)
            
            # Delete all channels
            for channel in ctx.guild.channels:
                try:
                    await channel.delete(reason=f"Server nuked by {ctx.author}")
                except:
                    pass
            
            # Delete all roles (except @everyone and managed roles)
            for role in ctx.guild.roles:
                if role != ctx.guild.default_role and not role.managed:
                    try:
                        await role.delete(reason=f"Server nuked by {ctx.author}")
                    except:
                        pass
            
            # Create new read-only channel
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    send_messages=False,
                    read_messages=True
                )
            }
            
            new_channel = await ctx.guild.create_text_channel(
                name="hub-invite",
                overwrites=overwrites,
                reason=f"Server nuked by {ctx.author}"
            )
            
            # Post hub invite
            nuke_embed = discord.Embed(
                title="🚨 Server Nuked",
                description=f"This server has been reset.\n\n"
                           f"**Join the Prime Network hub:**\n{HUB_INVITE}",
                color=BRAND_COLOR
            )
            nuke_embed.set_footer(text="Prime Network")
            
            await new_channel.send(embed=nuke_embed)
            
        except:
            embed = create_error_embed(
                title="Nuke Cancelled",
                description="Server nuke cancelled (timeout or invalid confirmation).",
                guild=ctx.guild
            )
            await confirm_msg.edit(embed=embed)
    
    # ==================== CONFIG COMMAND ====================
    
    @server.command(name='config', aliases=['settings', 'info'])
    async def config(self, ctx):
        """
        Display server settings and configuration
        
        Usage: $ s config
        """
        if not ctx.guild:
            return
        
        guild_data = get_guild_data(ctx.guild.id)
        embed = create_guild_config_embed(
            guild=ctx.guild,
            guild_data=guild_data
        )
        await ctx.send(embed=embed)

# ==================== COG SETUP ====================

async def setup(bot):
    await bot.add_cog(Server(bot))