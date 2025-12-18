"""Server Module - Server Configuration and Management"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional
import bot as bot_module
from format import (
    create_module_help_embed,
    create_info_embed,
    create_success_embed,
    create_error_embed,
    create_server_config_embed
)

class Server(commands.Cog):
    """Server configuration and management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(name='s', aliases=['server'])
    async def server(self, ctx):
        """🏢 Server Module - Server configuration"""
        if ctx.invoked_subcommand is None:
            commands_list = [
                {
                    "name": "s name <newname>",
                    "description": "Rename the server"
                },
                {
                    "name": "s leave",
                    "description": "Remove server from network"
                },
                {
                    "name": "s gate <lock/nuke>",
                    "description": "Lock/nuke all channels"
                },
                {
                    "name": "s config",
                    "description": "View server configuration"
                }
            ]
            
            embed = create_module_help_embed(
                "Server",
                "🏢",
                "Server configuration and management",
                commands_list,
                ctx.guild
            )
            await ctx.send(embed=embed)
    
    @server.command(name='name')
    @commands.has_permissions(administrator=True)
    async def rename_server(self, ctx, *, newname: str):
        """Rename the server"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if len(newname) > 100:
            embed = create_error_embed(
                title="Name Too Long",
                description="Server name must be 100 characters or less",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        try:
            old_name = ctx.guild.name
            await ctx.guild.edit(name=newname)
            
            # Update in data
            guild_data = bot_module.get_guild_data(ctx.guild.id)
            guild_data["name"] = newname
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Server Renamed",
                description=f"'{old_name}' → '{newname}'",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                title="Error",
                description=f"Failed to rename server: {str(e)}",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @server.command(name='leave')
    @commands.has_permissions(administrator=True)
    async def leave_network(self, ctx):
        """Remove this server from the network"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        guild_id_str = str(ctx.guild.id)
        if guild_id_str in bot_module.DATA["guilds"]:
            del bot_module.DATA["guilds"][guild_id_str]
            bot_module.save_data()
            
            embed = create_success_embed(
                title="Server Removed",
                description=f"{ctx.guild.name} has been removed from the network",
                guild=ctx.guild
            )
            await ctx.send(embed=embed)
        else:
            embed = create_info_embed(
                title="Not in Network",
                description="Server is not in the network",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @server.command(name='gate')
    @commands.has_permissions(administrator=True)
    async def gate_server(self, ctx, action: str):
        """Lock or nuke all channels"""
        if not ctx.author.guild_permissions.administrator and not bot_module.is_trusted(ctx.author.id):
            embed = create_error_embed(
                title="Permission Denied",
                description="Admin or trusted only",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if action.lower() == "lock":
            try:
                # Disable send messages permission for @everyone
                for channel in ctx.guild.channels:
                    try:
                        await channel.set_permissions(
                            ctx.guild.default_role,
                            send_messages=False,
                            reason="Server locked by bot"
                        )
                    except:
                        pass
                
                embed = create_success_embed(
                    title="Server Locked",
                    description="All channels locked - members cannot send messages",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            
            except Exception as e:
                embed = create_error_embed(
                    title="Error",
                    description=f"Failed to lock server: {str(e)}",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
        
        elif action.lower() == "nuke":
            try:
                # Delete all channels
                deleted = 0
                for channel in list(ctx.guild.channels):
                    try:
                        await channel.delete()
                        deleted += 1
                    except:
                        pass
                
                # Create new channel with hub invite
                try:
                    category = await ctx.guild.create_category("Network")
                    channel = await category.create_text_channel("hub-invite")
                    
                    embed = discord.Embed(
                        title="🏢 Welcome to Prime Network",
                        description=f"This server was reset. Join the hub:\n{bot_module.MAIN_HUB_INVITE}",
                        color=0x2B2D31
                    )
                    await channel.send(embed=embed)
                    
                    # Lock the channel
                    await channel.set_permissions(
                        ctx.guild.default_role,
                        send_messages=False,
                        read_messages=True
                    )
                except:
                    pass
                
                embed = create_success_embed(
                    title="Server Nuked",
                    description=f"Deleted {deleted} channels - reset complete",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed)
            
            except Exception as e:
                embed = create_error_embed(
                    title="Error",
                    description=f"Failed to nuke server: {str(e)}",
                    guild=ctx.guild
                )
                await ctx.send(embed=embed, delete_after=5)
        
        else:
            embed = create_error_embed(
                title="Invalid Action",
                description="Use `lock` or `nuke`",
                guild=ctx.guild
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @server.command(name='config')
    async def view_config(self, ctx):
        """View server configuration"""
        guild_data = bot_module.get_guild_data(ctx.guild.id)
        
        embed = create_server_config_embed(
            ctx.guild.name,
            guild_data,
            ctx.guild
        )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Load the Server cog"""
    await bot.add_cog(Server(bot))
