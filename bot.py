from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
from discord import app_commands, TextChannel, VoiceChannel, Thread as DiscordThread
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
load_dotenv()

from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_warning_embed,
    create_dashboard_embed,
    create_leaderboard_embed
)

# ==================== CORE CONFIGURATION ====================
# These variables are used across all cogs

MAIN_HUB_ID = 1449199091937443965  # quarterzip
MAIN_HUB_NAME = "quarterzip"
BOT_OWNER_ID = 895767962722660372
HUB_INVITE = "https://discord.gg/F9PB47S3FJ"
HUB_ANN_CHANNEL_ID = 1451697918493855797  # Prime Network announcements channel
BRAND_COLOR = 0x8acaf5  # Special Prime Network blue - ONLY COLOR USED
STREAK_MESSAGE_THRESHOLD = 100  # Messages needed to gain 1 streak day

# Bot Configuration
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

def get_prefix(bot, message):
    """Get custom prefix for guild"""
    if not message.guild:
        return '$'
    guild_id_str = str(message.guild.id)
    if guild_id_str in DATA.get("guilds", {}) and "prefix" in DATA["guilds"][guild_id_str]:
        return DATA["guilds"][guild_id_str]["prefix"]
    return '$'

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# Data Storage
DATA_FILE = 'loyalty_data.json'
DATA: Dict[str, Any] = {}

# ==================== DATA MANAGEMENT ====================

def load_data():
    """Load network data from JSON file"""
    global DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            DATA = json.load(f)
    else:
        DATA = {
            "network_config": {
                "main_hub_id": MAIN_HUB_ID,
                "main_hub_name": MAIN_HUB_NAME,
                "main_hub_invite": HUB_INVITE,
                "hub_ann_channel_id": HUB_ANN_CHANNEL_ID,
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
        save_data()

def save_data():
    """Save network data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(DATA, f, indent=4)

def get_guild_data(guild_id: int) -> Dict[str, Any]:
    """Get or create guild data structure"""
    guild_id_str = str(guild_id)
    if guild_id_str not in DATA["guilds"]:
        guild = bot.get_guild(guild_id)
        DATA["guilds"][guild_id_str] = {
            "name": guild.name if guild else "Unknown",
            "is_hub": guild_id == MAIN_HUB_ID,
            "prefix": "$",
            "announcement_channel": None,
            "hub_ann_channel_id": HUB_ANN_CHANNEL_ID,
            "broadcast_channel": None,
            "loyal_role_id": None,
            "creed_message_id": None,
            "creed_channel_id": None,
            "dashboard_msg_id": None,
            "dashboard_channel_id": None,
            "trusted_local": []
        }
        save_data()
    return DATA["guilds"][guild_id_str]

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get or create user data structure"""
    user_id_str = str(user_id)
    if user_id_str not in DATA["global_users"]:
        DATA["global_users"][user_id_str] = {
            "is_loyal": False,
            "is_inactive": False,
            "streak": 0,
            "total_messages": 0,
            "messages_since_last_streak": 0,
            "last_activity": None,
            "opt_in_date": None,
            "origin_gateway_id": None,
            "origin_gateway_name": None,
            "main_server_id": None,
            "main_server_name": None,
            "is_muted": False
        }
        save_data()
    return DATA["global_users"][user_id_str]

def is_system_active() -> bool:
    """Check if loyalty system is active"""
    return DATA.get("network_config", {}).get("system_active", True)

def is_trusted_user(user_id: int) -> bool:
    """Check if user is in trusted list"""
    return user_id in DATA.get("network_config", {}).get("trusted_users", [])

def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    return user_id == BOT_OWNER_ID

def get_loyal_member_count() -> int:
    """Get total count of loyal members across network"""
    return sum(1 for user in DATA.get("global_users", {}).values() if user.get("is_loyal", False))

def get_active_loyal_count() -> int:
    """Get count of active (non-inactive) loyal members"""
    return sum(1 for user in DATA.get("global_users", {}).values() 
               if user.get("is_loyal", False) and not user.get("is_inactive", False))

def update_user_activity(user_id: int, guild_id: int):
    """Update user's activity, location, and streak"""
    user_data = get_user_data(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update activity
    user_data["last_activity"] = today
    user_data["total_messages"] += 1
    user_data["messages_since_last_streak"] = user_data.get("messages_since_last_streak", 0) + 1
    
    # Mark as active if they were inactive
    if user_data.get("is_inactive", False):
        user_data["is_inactive"] = False
    
    # Track main server (most active server)
    guild = bot.get_guild(guild_id)
    if guild:
        current_main = user_data.get("main_server_id")
        if current_main != guild_id:
            # Update main server to current location
            user_data["main_server_id"] = guild_id
            user_data["main_server_name"] = guild.name
    
    # Streak system: Gain 1 streak day per 100 messages
    if user_data.get("is_loyal", False):
        if user_data["messages_since_last_streak"] >= STREAK_MESSAGE_THRESHOLD:
            user_data["streak"] = user_data.get("streak", 0) + 1
            user_data["messages_since_last_streak"] = 0
    
    save_data()

def check_user_in_hub(user_id: int) -> bool:
    """Check if user is in the main hub server"""
    hub = bot.get_guild(MAIN_HUB_ID)
    if not hub:
        return False
    return hub.get_member(user_id) is not None

# ==================== BOT EVENTS ====================

@bot.event
async def on_member_join(member):
    """Handle member joining - check blacklist"""
    if member.bot:
        return
    
    # Check if user is blacklisted
    user_id_str = str(member.id)
    if user_id_str in DATA.get("global_blacklist", []):
        try:
            await member.guild.ban(member, reason="Global blacklist - Auto-ban on join")
            print(f"Auto-banned blacklisted user {member.id} from {member.guild.name}")
        except:
            print(f"Failed to auto-ban {member.id} from {member.guild.name}")

@bot.event
async def on_ready():
    """Bot startup event"""
    load_data()
    bot_name = bot.user.name if bot.user else "Bot"
    print(f'{bot_name} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds')
    print(f'Loyal members: {get_loyal_member_count()}')
    print(f'Active loyal members: {get_active_loyal_count()}')
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    # Load cogs
    try:
        await bot.load_extension('cogs.loyalty')
        print('✅ Loyalty module loaded')
    except Exception as e:
        print(f'❌ Failed to load Loyalty: {e}')
    
    try:
        await bot.load_extension('cogs.network')
        print('✅ Network module loaded')
    except Exception as e:
        print(f'❌ Failed to load Network: {e}')
    
    try:
        await bot.load_extension('cogs.security')
        print('✅ Security module loaded')
    except Exception as e:
        print(f'❌ Failed to load Security: {e}')
    
    try:
        await bot.load_extension('cogs.server')
        print('✅ Server module loaded')
    except Exception as e:
        print(f'❌ Failed to load Server: {e}')
    
    try:
        await bot.load_extension('cogs.sudo')
        print('✅ Sudo module loaded')
    except Exception as e:
        print(f'❌ Failed to load Sudo: {e}')
    
    # Start background tasks
    update_presence.start()
    update_dashboard.start()
    check_inactive_users.start()

@bot.event
async def on_guild_join(guild):
    """Handle bot joining a new guild"""
    guild_data = get_guild_data(guild.id)
    guild_data["name"] = guild.name
    save_data()
    print(f'Joined guild: {guild.name} ({guild.id})')

@bot.event
async def on_message(message):
    """Handle all message events"""
    if message.author.bot:
        return
    
    # Bot mention responses
    if bot.user and bot.user.mentioned_in(message) and len(message.mentions) == 1:
        content_lower = message.content.lower().strip()
        
        # @bot help - Show all modules
        if 'help' in content_lower:
            prefix = get_prefix(bot, message)
            embed = discord.Embed(
                title="🌐 Pawn - Prime Network Bot",
                description=f"**Prefix:** `{prefix}` (customizable per server)\n\n"
                           f"**Available Modules:**\n"
                           f"`{prefix}l` - Loyalty (creed, roles, leaderboards)\n"
                           f"`{prefix}net` - Network (broadcasts, invites, config)\n"
                           f"`{prefix}sec` - Security (bans, timeouts, system control)\n"
                           f"`{prefix}s` - Server (management, gate controls)\n"
                           f"`{prefix}su` - Sudo (owner-only admin tools)\n\n"
                           f"*Use `{prefix}<module>` to see module commands*",
                color=BRAND_COLOR
            )
            if message.guild and message.guild.icon:
                embed.set_footer(text=f"{message.guild.name} • Prime Network", icon_url=message.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            await message.channel.send(embed=embed)
            return
        
        # @bot count - Member count (exclude bots)
        if 'count' in content_lower:
            if not message.guild:
                return
            
            total_members = message.guild.member_count or 0
            bot_count = sum(1 for member in message.guild.members if member.bot)
            human_count = total_members - bot_count
            
            if 'member' in content_lower or 'human' in content_lower:
                embed = discord.Embed(
                    title="👥 Member Count",
                    description=f"**Human Members:** {human_count}",
                    color=BRAND_COLOR
                )
            elif 'bot' in content_lower:
                embed = discord.Embed(
                    title="🤖 Bot Count",
                    description=f"**Bots:** {bot_count}",
                    color=BRAND_COLOR
                )
            else:
                embed = discord.Embed(
                    title="📊 Server Count",
                    description=f"**Total Members:** {total_members}\n"
                               f"**Humans:** {human_count}\n"
                               f"**Bots:** {bot_count}",
                    color=BRAND_COLOR
                )
            
            if message.guild.icon:
                embed.set_footer(text=f"{message.guild.name} • Prime Network", icon_url=message.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            await message.channel.send(embed=embed)
            return
        
        # Default @bot - Show stats
        if message.guild:
            guild_data = get_guild_data(message.guild.id)
            loyal_in_guild = sum(1 for uid, user in DATA.get("global_users", {}).items() 
                                if user.get("is_loyal") and user.get("main_server_id") == message.guild.id)
            
            embed = discord.Embed(
                title=f"📊 {message.guild.name}",
                description=f"**Members:** {message.guild.member_count or 0}\n"
                           f"**Loyal (Main Server):** {loyal_in_guild}\n"
                           f"**Network Loyal:** {get_loyal_member_count()}\n"
                           f"**Active Loyal:** {get_active_loyal_count()}\n"
                           f"**Status:** {'🏢 Main Hub' if guild_data.get('is_hub') else '🌐 Gateway'}",
                color=BRAND_COLOR
            )
            if message.guild.icon:
                embed.set_footer(text=f"{message.guild.name} • Prime Network", icon_url=message.guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            await message.channel.send(embed=embed)
            return
    
    # Track user activity
    if message.guild:
        update_user_activity(message.author.id, message.guild.id)
    
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """Handle creed message reactions for loyalty opt-in"""
    if not bot.user or payload.user_id == bot.user.id:
        return
    
    if not payload.guild_id:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    guild_data = get_guild_data(guild.id)
    
    # Check if reaction is on creed message
    if guild_data.get("creed_message_id") == payload.message_id and str(payload.emoji) == "✅":
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        user_data = get_user_data(payload.user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Mark as loyal
        user_data["is_loyal"] = True
        user_data["is_inactive"] = False
        user_data["opt_in_date"] = today
        user_data["last_activity"] = today
        user_data["origin_gateway_id"] = guild.id
        user_data["origin_gateway_name"] = guild.name
        user_data["main_server_id"] = guild.id
        user_data["main_server_name"] = guild.name
        user_data["streak"] = 0
        user_data["messages_since_last_streak"] = 0
        
        # Update stats
        if today not in DATA["stats"]["daily_joins"]:
            DATA["stats"]["daily_joins"][today] = 0
        DATA["stats"]["daily_joins"][today] += 1
        
        save_data()
        
        # Assign loyalty role
        if guild_data.get("loyal_role_id"):
            role = guild.get_role(guild_data["loyal_role_id"])
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
        
        # Send welcome DM
        try:
            in_hub = check_user_in_hub(member.id)
            hub_text = "\n✅ You're already in the main hub!" if in_hub else f"\n📨 Watch for invites to join **{MAIN_HUB_NAME}** (main hub)"
            
            embed = discord.Embed(
                title="✅ Welcome to Prime Network!",
                description=f"You've joined the loyalty program in **{guild.name}**.\n\n"
                           f"**What's Next:**\n"
                           f"• Stay active to build your streak (1 day per 100 messages)\n"
                           f"• Your loyalty status is tracked network-wide\n"
                           f"• You'll receive network announcements{hub_text}\n\n"
                           f"**Powered by Pawn Bot**",
                color=BRAND_COLOR
            )
            if guild.icon:
                embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
            else:
                embed.set_footer(text="Prime Network")
            await member.send(embed=embed)
        except:
            pass

# ==================== BACKGROUND TASKS ====================

@tasks.loop(minutes=5)
async def update_presence():
    """Update bot presence with loyal member count"""
    count = get_loyal_member_count()
    activity = discord.Streaming(
        name=f"{count} loyal members",
        url="https://twitch.tv/pawnbot"
    )
    await bot.change_presence(activity=activity)

@tasks.loop(hours=4)
async def update_dashboard():
    """Update leaderboard dashboards in all guilds"""
    for guild_id_str, guild_data in DATA.get("guilds", {}).items():
        guild_id = int(guild_id_str)
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        
        dashboard_channel_id = guild_data.get("dashboard_channel_id")
        dashboard_msg_id = guild_data.get("dashboard_msg_id")
        
        if not dashboard_channel_id:
            continue
        
        channel = guild.get_channel(dashboard_channel_id)
        if not channel or not isinstance(channel, (TextChannel, VoiceChannel, DiscordThread)):
            continue
        
        # Get top 10 loyal members by streak
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
            guild=guild
        )
        
        try:
            if dashboard_msg_id:
                try:
                    msg = await channel.fetch_message(dashboard_msg_id)
                    await msg.edit(embed=embed)
                except:
                    msg = await channel.send(embed=embed)
                    guild_data["dashboard_msg_id"] = msg.id
                    save_data()
            else:
                msg = await channel.send(embed=embed)
                guild_data["dashboard_msg_id"] = msg.id
                save_data()
        except:
            pass

@tasks.loop(hours=24)
async def check_inactive_users():
    """Check for inactive users and mark them"""
    current_time = datetime.now()
    
    for user_id_str, user_data in DATA.get("global_users", {}).items():
        if not user_data.get("is_loyal", False):
            continue
        
        last_activity = user_data.get("last_activity")
        if not last_activity:
            continue
        
        try:
            last_active_date = datetime.strptime(last_activity, "%Y-%m-%d")
            days_inactive = (current_time - last_active_date).days
            
            # Mark as inactive if no activity for 7+ days
            if days_inactive >= 7:
                if not user_data.get("is_inactive", False):
                    user_data["is_inactive"] = True
                    print(f"Marked user {user_id_str} as inactive ({days_inactive} days)")
        except:
            pass
    
    save_data()

# ==================== COMMAND ERROR HANDLER ====================

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command.",
            color=BRAND_COLOR
        )
        if ctx.guild and ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"Missing required argument: `{error.param.name}`",
            color=BRAND_COLOR
        )
        if ctx.guild and ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Prime Network", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text="Prime Network")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Error: {error}")

# ==================== SYSTEM CHECK DECORATOR ====================

def require_active_system():
    """Decorator to check if system is active"""
    async def predicate(ctx):
        if not is_system_active():
            embed = discord.Embed(
                title="❌ System Offline",
                description="The loyalty system is currently disabled.",
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

# ==================== KEEP-ALIVE SERVER ====================

app = Flask('')

@app.route('/')
def home():
    return "Pawn Bot is alive!"

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "bot": "Pawn",
        "network": "Prime Network",
        "guilds": len(bot.guilds),
        "loyal_members": get_loyal_member_count(),
        "active_loyal_members": get_active_loyal_count(),
        "system_active": is_system_active()
    }

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ==================== BOT STARTUP ====================

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set!")
    else:
        bot.run(TOKEN)