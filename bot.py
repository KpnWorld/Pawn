import discord
import json
import os
from flask import Flask
from threading import Thread
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import asyncio

load_dotenv()

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_module_help_embed,
    create_command_reference_embed
)

# Bot Configuration
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# Data Storage
DATA_FILE = 'loyalty_data.json'
DATA: Dict[str, Any] = {}

# Constants
MAIN_HUB_ID = 1449199091937443965
MAIN_HUB_INVITE = "https://discord.gg/F9PB47S3FJ"
BOT_OWNER_ID = 895767962722660372

# ==================== DATA MANAGEMENT ====================

def load_data():
    """Load loyalty data from JSON file"""
    global DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                DATA = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {DATA_FILE} is corrupted, initializing with defaults")
            DATA = initialize_data()
    else:
        DATA = initialize_data()

def initialize_data() -> Dict[str, Any]:
    """Initialize default data structure"""
    return {
        "network_config": {
            "main_hub_id": MAIN_HUB_ID,
            "main_hub_invite": MAIN_HUB_INVITE,
            "system_active": True,
            "trusted_users": [BOT_OWNER_ID]
        },
        "global_blacklist": [],
        "global_users": {},
        "guilds": {},
        "stats": {
            "daily_joins": {},
            "daily_leaves": {},
            "activity_snapshots": {}
        }
    }

def save_data():
    """Save loyalty data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(DATA, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get or create global user profile"""
    # Ensure global_users key exists
    if "global_users" not in DATA:
        DATA["global_users"] = {}
    
    user_id_str = str(user_id)
    if user_id_str not in DATA["global_users"]:
        DATA["global_users"][user_id_str] = {
            "is_loyal": False,
            "streak": 0,
            "total_messages": 0,
            "last_activity": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "opt_in_date": None,
            "origin_gateway_id": None,
            "origin_gateway_name": None,
            "active_location_id": None,
            "is_muted": False
        }
        save_data()
    return DATA["global_users"][user_id_str]

def get_guild_data(guild_id: int) -> Dict[str, Any]:
    """Get or create guild config"""
    # Ensure guilds key exists
    if "guilds" not in DATA:
        DATA["guilds"] = {}
    
    guild_id_str = str(guild_id)
    if guild_id_str not in DATA["guilds"]:
        DATA["guilds"][guild_id_str] = {
            "name": "Unknown",
            "is_hub": guild_id == MAIN_HUB_ID,
            "prefix": "$",
            "announcement_channel": None,
            "broadcast_channel": None,
            "loyal_role_id": None,
            "creed_message_id": None,
            "dashboard_msg_id": None,
            "dashboard_channel_id": None,
            "trusted_local": []
        }
        save_data()
    return DATA["guilds"][guild_id_str]

def is_trusted(user_id: int) -> bool:
    """Check if user is globally trusted"""
    if "network_config" not in DATA or "trusted_users" not in DATA["network_config"]:
        return False
    return user_id in DATA["network_config"]["trusted_users"]

def is_blacklisted(user_id: int) -> bool:
    """Check if user is globally blacklisted"""
    if "global_blacklist" not in DATA:
        return False
    return user_id in DATA["global_blacklist"]

def is_muted(user_id: int) -> bool:
    """Check if user is globally muted"""
    user_data = get_user_data(user_id)
    return user_data.get("is_muted", False)

def is_system_active() -> bool:
    """Check if loyalty system is active"""
    return DATA["network_config"].get("system_active", True)

def update_activity(user_id: int, guild_id: int, guild_name: str):
    """Update user activity timestamp and message count"""
    user_data = get_user_data(user_id)
    user_data["last_activity"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_data["active_location_id"] = guild_id
    user_data["total_messages"] = user_data.get("total_messages", 0) + 1
    save_data()

def get_loyal_count() -> int:
    """Get total count of loyal users globally"""
    return sum(1 for u in DATA["global_users"].values() if u.get("is_loyal", False))

def get_guild_member_count(guild: discord.Guild) -> int:
    """Get member count excluding bots"""
    return sum(1 for m in guild.members if not m.bot)

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    """Bot startup event"""
    load_data()
    bot_name = bot.user.name if bot.user else "Bot"
    print(f'{bot_name} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds')
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    update_presence.start()
    update_dashboard.start()

@bot.event
async def on_message(message):
    """Handle all message events"""
    if message.author.bot:
        return
    
    # Check if system is active
    if not is_system_active():
        await bot.process_commands(message)
        return
    
    # Check blacklist
    if is_blacklisted(message.author.id):
        try:
            await message.delete()
        except:
            pass
        return
    
    # Check mute - auto-delete
    if is_muted(message.author.id):
        try:
            await message.delete()
        except:
            pass
        return
    
    # Bot mention response - show status
    if bot.user and bot.user.mentioned_in(message) and len(message.mentions) == 1:
        guild_count = len(bot.guilds)
        total_members = sum(get_guild_member_count(g) for g in bot.guilds)
        loyal_count = get_loyal_count()
        
        embed = create_info_embed(
            title="Prime Network Status",
            description=f"**Gateways:** {guild_count}\n**Total Members:** {total_members}\n**Loyal Members:** {loyal_count}",
            guild=message.guild
        )
        await message.channel.send(embed=embed)
        return
    
    # Track activity
    if message.guild:
        update_activity(message.author.id, message.guild.id, message.guild.name)
    
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """Handle opt-in reactions to creed message"""
    if payload.user_id == (bot.user.id if bot.user else 0):
        return
    
    # Check blacklist
    if is_blacklisted(payload.user_id):
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    guild_data = get_guild_data(guild.id)
    
    # Check if this is the creed message
    if guild_data["creed_message_id"] != payload.message_id:
        return
    
    member = guild.get_member(payload.user_id)
    if not member:
        return
    
    # Get or create user profile
    user_data = get_user_data(payload.user_id)
    
    # Set origin if new user
    if user_data["origin_gateway_id"] is None:
        user_data["origin_gateway_id"] = guild.id
        user_data["origin_gateway_name"] = guild.name
    
    # Mark as loyal
    user_data["is_loyal"] = True
    if user_data["opt_in_date"] is None:
        user_data["opt_in_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Grant local loyalty role
    if guild_data["loyal_role_id"]:
        try:
            role = guild.get_role(guild_data["loyal_role_id"])
            if role:
                await member.add_roles(role)
        except:
            pass
    
    save_data()
    
    # Send welcome DM
    try:
        embed = create_info_embed(
            title="🎉 Welcome to Prime Network",
            description=f"You've joined the loyalty program in **{guild.name}**!\n\nVisit the Main Hub: {MAIN_HUB_INVITE}",
            guild=guild
        )
        await member.send(embed=embed)
    except:
        pass

# ==================== BACKGROUND TASKS ====================

@tasks.loop(minutes=5)
async def update_presence():
    """Update bot presence with loyal member count"""
    try:
        count = get_loyal_count()
        activity = discord.Streaming(
            name=f"{count} loyal members",
            url="https://twitch.tv/pawnbot"
        )
        await bot.change_presence(activity=activity)
    except Exception as e:
        print(f"Error updating presence: {e}")

@tasks.loop(hours=4)
async def update_dashboard():
    """Update dashboard every 4 hours - localized per gateway"""
    if not is_system_active():
        return
    
    try:
        # Get top 10 loyal users globally
        top_users = []
        loyal_users = [
            (uid, u) for uid, u in DATA["global_users"].items()
            if u.get("is_loyal", False)
        ]
        sorted_users = sorted(loyal_users, key=lambda x: x[1].get("streak", 0), reverse=True)
        top_users = sorted_users[:10]
        
        # Update dashboard in each gateway
        for guild_id_str, guild_config in DATA.get("guilds", {}).items():
            guild_id = int(guild_id_str)
            guild = bot.get_guild(guild_id)
            if not guild:
                continue
            
            channel_id = guild_config.get("dashboard_channel_id")
            if not channel_id:
                continue
            
            channel = guild.get_channel(int(channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                continue
            
            # Create dashboard embed
            medals = ["🥇", "🥈", "🥉"]
            leaderboard_text = ""
            
            for idx, (user_id_str, user_data) in enumerate(top_users[:10], 1):
                member = guild.get_member(int(user_id_str))
                username = member.display_name if member else f"User {user_id_str}"
                
                if idx <= 3:
                    position = medals[idx - 1]
                else:
                    position = f"`#{idx:02d}`"
                
                streak = user_data.get("streak", 0)
                messages = user_data.get("total_messages", 0)
                leaderboard_text += f"{position} **{username}**\n└─ {messages} msgs • {streak}🔥\n"
            
            if not leaderboard_text:
                leaderboard_text = "No data available yet."
            
            embed = discord.Embed(
                title="🏆 Prime Network Leaderboard",
                description=leaderboard_text,
                color=0x2B2D31,
                timestamp=datetime.now(timezone.utc)
            )
            
            if guild.icon:
                embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
            else:
                embed.set_footer(text=f"{guild.name} • Prime Network")
            
            try:
                msg_id = guild_config.get("dashboard_msg_id")
                if msg_id:
                    try:
                        msg = await channel.fetch_message(int(msg_id))
                        await msg.edit(embed=embed)
                    except discord.NotFound:
                        msg = await channel.send(embed=embed)
                        guild_config["dashboard_msg_id"] = msg.id
                        save_data()
                else:
                    msg = await channel.send(embed=embed)
                    guild_config["dashboard_msg_id"] = msg.id
                    save_data()
            except Exception as e:
                print(f"Error updating dashboard in {guild.name}: {e}")
    except Exception as e:
        print(f"Error in update_dashboard: {e}")

# ==================== HELP COMMAND ====================

MODULE_INFO = {
    "loyalty": {"emoji": "🎖️", "description": "Manage creed, leaderboards, and loyalty roles"},
    "network": {"emoji": "🌐", "description": "Control global network broadcasting and invites"},
    "security": {"emoji": "🔒", "description": "Network security, bans, timeouts, and system control"},
    "server": {"emoji": "🏢", "description": "Server configuration and management"},
    "sudo": {"emoji": "⚙️", "description": "Bot owner utilities and system diagnostics"}
}

@bot.command(name='help')
async def help_command(ctx):
    """Show all available modules"""
    embed = discord.Embed(
        title="📚 Prime Network Bot Help",
        description="Choose a module to learn more",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc)
    )
    
    for module, info in MODULE_INFO.items():
        embed.add_field(
            name=f"{info['emoji']} {module.title()}",
            value=f"{info['description']}\n`$ {module}`",
            inline=False
        )
    
    if ctx.guild and ctx.guild.icon:
        embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    await ctx.send(embed=embed)

@bot.command(name='count')
async def count_command(ctx):
    """Show member count excluding bots"""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    member_count = get_guild_member_count(ctx.guild)
    embed = create_info_embed(
        title="Member Count",
        description=f"**{ctx.guild.name}** has **{member_count}** members (excluding bots)",
        guild=ctx.guild
    )
    await ctx.send(embed=embed)

# ==================== COG LOADER ====================

async def load_cogs():
    """Load all cogs from cogs directory"""
    cogs_dir = "cogs"
    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename[:-3]}")
            except Exception as e:
                print(f"Error loading cog {filename[:-3]}: {e}")

@bot.event
async def setup_hook():
    """Called when bot is loading"""
    await load_cogs()

# ==================== ERROR HANDLING ====================

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.MissingPermissions):
        embed = create_error_embed(
            title="Permission Denied",
            description="You don't have permission to use this command.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed, delete_after=5)
    
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = create_error_embed(
            title="Missing Argument",
            description=f"Missing required argument: `{error.param.name}`",
            guild=ctx.guild
        )
        await ctx.send(embed=embed, delete_after=5)
    
    elif isinstance(error, commands.CommandNotFound):
        pass  # Silent on unknown commands
    
    else:
        print(f"Unhandled error: {error}")

# ==================== KEEP-ALIVE ====================

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "guilds": len(bot.guilds),
        "loyal_members": get_loyal_count()
    }

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set!")
    else:
        bot.run(TOKEN)
