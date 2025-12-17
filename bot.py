import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Import format methods (to be created in format.py)
from format import (
    create_base_embed,
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_setup_embed,
    create_dashboard_embed,
    create_leaderboard_embed
)


# Bot Configuration
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.m ', intents=intents)

# Data Storage
DATA_FILE = 'loyalty_data.json'
DATA: Dict[str, Any] = {}

# Setup state tracking
setup_sessions: Dict[int, Dict[str, Any]] = {}

# ==================== DATA MANAGEMENT ====================

def load_data():
    """Load loyalty data from JSON file"""
    global DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            DATA = json.load(f)
    else:
        DATA = {}

def save_data():
    """Save loyalty data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(DATA, f, indent=4)

def get_guild_data(guild_id: int) -> Dict[str, Any]:
    """Get or create guild data structure"""
    guild_id_str = str(guild_id)
    if guild_id_str not in DATA:
        DATA[guild_id_str] = {
            "loyalty": {
                "creed_message_id": None,
                "creed_channel_id": None,
                "loyalty_role_id": None,
                "backup_server_invite": None,
                "dashboard_message_id": None,
                "dashboard_channel_id": None,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "members": {}
            }
        }
        save_data()
    return DATA[guild_id_str]

def update_member_activity(guild_id: int, user_id: int):
    """Update member's last activity timestamp"""
    guild_data = get_guild_data(guild_id)
    user_id_str = str(user_id)
    
    if user_id_str not in guild_data["loyalty"]["members"]:
        guild_data["loyalty"]["members"][user_id_str] = {
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "streak_days": 0,
            "total_messages": 0,
            "opted_in": False
        }
    else:
        guild_data["loyalty"]["members"][user_id_str]["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guild_data["loyalty"]["members"][user_id_str]["total_messages"] += 1
    
    save_data()

def get_loyal_member_count() -> int:
    """Get total count of loyal members across all guilds"""
    count = 0
    for guild_data in DATA.values():
        if "loyalty" in guild_data and "members" in guild_data["loyalty"]:
            count += sum(1 for m in guild_data["loyalty"]["members"].values() if m.get("opted_in", False))
    return count

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    """Bot startup event"""
    load_data()
    bot_name = bot.user.name if bot.user else "Bot"
    print(f'{bot_name} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds')
    
    # Start background tasks
    check_inactivity.start()
    update_presence.start()

@bot.event
async def on_raw_reaction_add(payload):
    """Handle opt-in reactions to creed message"""
    if payload.user_id == bot.user.id if bot.user else 0:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    guild_data = get_guild_data(guild.id)
    loyalty_data = guild_data["loyalty"]
    
    # Check if reaction is on creed message
    if loyalty_data["creed_message_id"] == payload.message_id:
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        user_id_str = str(payload.user_id)
        
        # Mark as opted in
        if user_id_str not in loyalty_data["members"]:
            loyalty_data["members"][user_id_str] = {
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "streak_days": 1,
                "total_messages": 0,
                "opted_in": True
            }
        else:
            loyalty_data["members"][user_id_str]["opted_in"] = True
            loyalty_data["members"][user_id_str]["streak_days"] = 1
        
        # Assign loyalty role
        if loyalty_data["loyalty_role_id"]:
            role = guild.get_role(loyalty_data["loyalty_role_id"])
            if role:
                await member.add_roles(role)
        
        save_data()
        
        # Send confirmation DM
        try:
            embed = create_success_embed(
                title="Welcome to Loyalty Program!",
                description=f"You've successfully joined the loyalty program in **{guild.name}**.\nStay active to maintain your streak!",
                guild=guild
            )
            await member.send(embed=embed)
        except:
            pass

# ==================== BACKGROUND TASKS ====================

@tasks.loop(hours=6)
async def check_inactivity():
    """Check for inactive members and remove loyalty status"""
    current_time = datetime.now()
    
    for guild_id_str, guild_data in DATA.items():
        guild_id = int(guild_id_str)
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        
        loyalty_data = guild_data["loyalty"]
        role_id = loyalty_data.get("loyalty_role_id")
        
        if not role_id:
            continue
        
        role = guild.get_role(role_id)
        if not role:
            continue
        
        members_to_remove = []
        
        for user_id_str, member_data in loyalty_data["members"].items():
            if not member_data.get("opted_in", False):
                continue
            
            last_activity_str = member_data.get("last_activity")
            if not last_activity_str:
                continue
            
            last_activity = datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S")
            days_inactive = (current_time - last_activity).days
            
            # 3-day inactivity rule
            if days_inactive >= 3:
                members_to_remove.append(user_id_str)
                member = guild.get_member(int(user_id_str))
                
                if member:
                    # Remove role
                    await member.remove_roles(role)
                    
                    # Send DM notification
                    try:
                        embed = create_info_embed(
                            title="Loyalty Status Lost",
                            description=f"You've been inactive in **{guild.name}** for 3+ days.\nYour loyalty streak has been reset.",
                            guild=guild
                        )
                        await member.send(embed=embed)
                    except:
                        pass
        
        # Update data
        for user_id_str in members_to_remove:
            loyalty_data["members"][user_id_str]["opted_in"] = False
            loyalty_data["members"][user_id_str]["streak_days"] = 0
        
        save_data()

@tasks.loop(minutes=5)
async def update_presence():
    """Update bot presence with loyal member count"""
    count = get_loyal_member_count()
    activity = discord.Streaming(
        name=f"{count} loyal members",
        url="https://twitch.tv/pawnbot"
    )
    await bot.change_presence(activity=activity)

# ==================== SETUP MESSAGE HANDLER ====================

async def on_message_setup_handler(message):
    """Handle setup flow messages"""
    if message.author.bot:
        return
    
    guild_id = message.guild.id if message.guild else None
    if not guild_id or guild_id not in setup_sessions:
        return
    
    session = setup_sessions[guild_id]
    
    # Verify user and channel
    if message.author.id != session["user_id"] or message.channel.id != session["channel_id"]:
        return
    
    step = session["step"]
    setup_msg = session["message"]
    
    try:
        if step == 1:
            # Step 1: Creed Message
            session["data"]["creed_message"] = message.content
            await message.delete()
            
            embed = create_setup_embed(
                title="Pawn Loyalty Setup",
                description=f"**Step 1/4:** Creed Message\n"
                           f"```{message.content}```\n✅ Completed\n\n"
                           f"**Step 2/4:** Which channel should the creed be sent in?\n"
                           f"(Mention a channel or leave blank for current channel)",
                step=2,
                total_steps=4,
                guild=message.guild
            )
            await setup_msg.edit(embed=embed)
            session["step"] = 2
            
        elif step == 2:
            # Step 2: Creed Channel
            if message.channel_mentions:
                channel = message.channel_mentions[0]
            else:
                channel = message.channel
            
            session["data"]["creed_channel_id"] = channel.id
            await message.delete()
            
            embed = create_setup_embed(
                title="Pawn Loyalty Setup",
                description=f"**Step 1/4:** Creed Message ✅\n"
                           f"**Step 2/4:** Creed Channel: {channel.mention} ✅\n\n"
                           f"**Step 3/4:** Which role should be given to loyal members?\n"
                           f"(Mention the role)",
                step=3,
                total_steps=4,
                guild=message.guild
            )
            await setup_msg.edit(embed=embed)
            session["step"] = 3
            
        elif step == 3:
            # Step 3: Loyalty Role
            if message.role_mentions:
                role = message.role_mentions[0]
                session["data"]["loyalty_role_id"] = role.id
                await message.delete()
                
                embed = create_setup_embed(
                    title="Pawn Loyalty Setup",
                    description=f"**Step 1/4:** Creed Message ✅\n"
                               f"**Step 2/4:** Creed Channel ✅\n"
                               f"**Step 3/4:** Loyalty Role: {role.mention} ✅\n\n"
                               f"**Step 4/4:** Enter the invite link for your backup server\n"
                               f"(Optional - leave blank to skip)",
                    step=4,
                    total_steps=4,
                    guild=message.guild
                )
                await setup_msg.edit(embed=embed)
                session["step"] = 4
            else:
                if message.guild:
                    error_embed = create_error_embed(
                        title="Invalid Role",
                        description="Please mention a valid role.",
                        guild=message.guild
                    )
                    await message.channel.send(embed=error_embed, delete_after=5)
                await message.delete()
            
        elif step == 4:
            # Step 4: Backup Server
            backup_invite = message.content.strip() if message.content.strip() else None
            session["data"]["backup_server_invite"] = backup_invite
            await message.delete()
            
            # Save configuration
            if not message.guild:
                return
                
            guild_data = get_guild_data(guild_id)
            loyalty_data = guild_data["loyalty"]
            
            loyalty_data["creed_channel_id"] = session["data"]["creed_channel_id"]
            loyalty_data["loyalty_role_id"] = session["data"]["loyalty_role_id"]
            loyalty_data["backup_server_invite"] = backup_invite
            
            # Send creed message
            creed_channel = message.guild.get_channel(session["data"]["creed_channel_id"])
            if creed_channel:
                creed_embed = create_base_embed(
                    title="Loyalty Program",
                    description=session["data"]["creed_message"],
                    guild=message.guild
                )
                creed_msg = await creed_channel.send(embed=creed_embed)
                await creed_msg.add_reaction("✅")
                loyalty_data["creed_message_id"] = creed_msg.id
            
            save_data()
            
            # Final completion embed
            backup_text = f"Backup Server: {backup_invite}" if backup_invite else "No backup server configured"
            
            completion_embed = create_success_embed(
                title="Pawn Loyalty Setup Completed!",
                description=f"✅ Creed message posted\n"
                           f"✅ Loyalty role configured\n"
                           f"✅ {backup_text}\n\n"
                           f"Your loyalty system is now active!",
                guild=message.guild
            )
            await setup_msg.edit(embed=completion_embed)
            
            # Cleanup session
            del setup_sessions[guild_id]
            
    except Exception as e:
        if message.guild:
            error_embed = create_error_embed(
                title="Setup Error",
                description=f"An error occurred during setup: {str(e)}",
                guild=message.guild
            )
            await setup_msg.edit(embed=error_embed)
        if guild_id in setup_sessions:
            del setup_sessions[guild_id]

# ==================== COMBINED MESSAGE HANDLER ====================

@bot.event
async def on_message(message):
    """Handle all message events"""
    # Handle setup flow first
    await on_message_setup_handler(message)
    
    # Skip bot messages
    if message.author.bot:
        return
    
    # Track user activity
    if message.guild:
        update_member_activity(message.guild.id, message.author.id)
    
    # Process commands
    await bot.process_commands(message)

# ==================== LOYALTY COMMANDS ====================

@bot.group(name='loyalty', aliases=['l'])
async def loyalty(ctx):
    """Loyalty system commands"""
    if ctx.invoked_subcommand is None:
        embed = create_info_embed(
            title="Pawn Loyalty System",
            description="Available commands:\n"
                       "`.m loyalty setup` - Configure loyalty system\n"
                       "`.m loyalty invite` - Invite loyal members to backup\n"
                       "`.m loyalty bkup <role>` - Register backup server\n"
                       "`.m loyalty stats` - View loyalty statistics\n"
                       "`.m loyalty leaderboard` - View top loyal members",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)

@loyalty.command(name='setup', aliases=['s'])
@commands.has_permissions(administrator=True)
async def loyalty_setup(ctx):
    """Interactive loyalty system setup"""
    if not ctx.guild:
        embed = create_error_embed(
            title="Server Only",
            description="This command can only be used in a server.",
            guild=None
        )
        await ctx.send(embed=embed)
        return
    
    guild_id = ctx.guild.id
    
    # Initialize setup session
    setup_sessions[guild_id] = {
        "step": 0,
        "channel_id": ctx.channel.id,
        "user_id": ctx.author.id,
        "data": {},
        "message": None
    }
    
    # Send initial setup embed
    embed = create_setup_embed(
        title="Pawn Loyalty Setup",
        description="Welcome! Follow the steps to configure your loyalty system.\n\n"
                   "**Step 1/4:** Please enter the creed message for users to opt-in.",
        step=1,
        total_steps=4,
        guild=ctx.guild
    )
    
    msg = await ctx.send(embed=embed)
    setup_sessions[guild_id]["message"] = msg
    setup_sessions[guild_id]["step"] = 1

@loyalty.command(name='invite', aliases=['in'])
@commands.has_permissions(administrator=True)
async def loyalty_invite(ctx, invite_link: str):
    """Send backup server invite to all loyal members"""
    if not ctx.guild:
        embed = create_error_embed(
            title="Server Only",
            description="This command can only be used in a server.",
            guild=None
        )
        await ctx.send(embed=embed)
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    loyalty_data = guild_data["loyalty"]
    
    # Use provided invite or stored backup invite
    backup_invite = invite_link or loyalty_data.get("backup_server_invite")
    
    if not backup_invite:
        embed = create_error_embed(
            title="No Backup Server",
            description="No backup server invite configured. Please provide an invite link or run setup again.",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)
        return
    
    # Get loyal members
    sent_count = 0
    failed_count = 0
    
    for user_id_str, member_data in loyalty_data["members"].items():
        if not member_data.get("opted_in", False):
            continue
        
        member = ctx.guild.get_member(int(user_id_str))
        if not member:
            continue
        
        try:
            embed = create_info_embed(
                title="Backup Server Invitation",
                description=f"Hello from **{ctx.guild.name}**!\n\n"
                           f"As a loyal member, you're invited to our backup server:\n"
                           f"{backup_invite}",
                guild=ctx.guild
            )
            await member.send(embed=embed)
            sent_count += 1
        except:
            failed_count += 1
    
    # Send confirmation
    result_embed = create_success_embed(
        title="Invitations Sent",
        description=f"✅ Sent to {sent_count} loyal members\n"
                   f"❌ Failed to send to {failed_count} members",
        guild=ctx.guild
    )
    await ctx.send(embed=result_embed)

@loyalty.command(name='bkup', aliases=['br'])
@commands.has_permissions(administrator=True)
async def loyalty_backup(ctx, role: discord.Role, invite_link: str):
    """Register backup server and role for loyal users"""
    if not ctx.guild:
        embed = create_error_embed(
            title="Server Only",
            description="This command can only be used in a server.",
            guild=None
        )
        await ctx.send(embed=embed)
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    loyalty_data = guild_data["loyalty"]
    
    # Update backup info
    if invite_link:
        loyalty_data["backup_server_invite"] = invite_link
    
    loyalty_data["loyalty_role_id"] = role.id
    save_data()
    
    embed = create_success_embed(
        title="Backup Configuration Updated",
        description=f"✅ Loyalty Role: {role.mention}\n" +
                   (f"✅ Backup Invite: {invite_link}" if invite_link else ""),
        guild=ctx.guild
    )
    await ctx.send(embed=embed)

@loyalty.command(name='stats', aliases=['st'])
async def loyalty_stats(ctx):
    """Display loyalty statistics"""
    if not ctx.guild:
        embed = create_error_embed(
            title="Server Only",
            description="This command can only be used in a server.",
            guild=None
        )
        await ctx.send(embed=embed)
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    loyalty_data = guild_data["loyalty"]
    
    total_members = len(loyalty_data["members"])
    opted_in = sum(1 for m in loyalty_data["members"].values() if m.get("opted_in", False))
    
    embed = create_info_embed(
        title="Loyalty Statistics",
        description=f"**Total Registered:** {total_members}\n"
                   f"**Active Loyal Members:** {opted_in}\n"
                   f"**Setup Date:** {loyalty_data.get('date', 'N/A')}",
        guild=ctx.guild
    )
    await ctx.send(embed=embed)

@loyalty.command(name='leaderboard', aliases=['lb', 'top'])
async def loyalty_leaderboard(ctx):
    """Display top 10 loyal members"""
    if not ctx.guild:
        embed = create_error_embed(
            title="Server Only",
            description="This command can only be used in a server.",
            guild=None
        )
        await ctx.send(embed=embed)
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    loyalty_data = guild_data["loyalty"]
    
    # Sort members by messages and streak
    members_list = []
    for user_id_str, member_data in loyalty_data["members"].items():
        if member_data.get("opted_in", False):
            members_list.append({
                "user_id": int(user_id_str),
                "messages": member_data.get("total_messages", 0),
                "streak": member_data.get("streak_days", 0)
            })
    
    # Sort by messages, then by streak
    members_list.sort(key=lambda x: (x["messages"], x["streak"]), reverse=True)
    top_10 = members_list[:10]
    
    embed = create_leaderboard_embed(
        title="Top 10 Loyal Members",
        members=top_10,
        guild=ctx.guild
    )
    await ctx.send(embed=embed)

# ==================== ERROR HANDLING ====================

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.MissingPermissions):
        embed = create_error_embed(
            title="Permission Denied",
            description="You don't have permission to use this command.",
            guild=ctx.guild if ctx.guild else None
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = create_error_embed(
            title="Missing Argument",
            description=f"Missing required argument: `{error.param.name}`",
            guild=ctx.guild if ctx.guild else None
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        embed = create_error_embed(
            title="Error",
            description=f"An error occurred: {str(error)}",
            guild=ctx.guild if ctx.guild else None
        )
        await ctx.send(embed=embed)

# ==================== RUN BOT ====================

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set!")
    else:
        bot.run(TOKEN)