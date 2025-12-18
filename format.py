import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# ==================== COLOR SCHEME ====================

class Colors:
    """Color palette for Pawn bot embeds"""
    BASE_GRAY = 0x2B2D31      # Discord dark gray - base color
    SUCCESS = 0x57F287        # Green - success messages
    ERROR = 0xED4245          # Red - error messages
    INFO = 0x5865F2           # Blurple - info messages
    WARNING = 0xFEE75C        # Yellow - warning messages
    SPECIAL = 0xEB459E        # Pink - special UI elements

# ==================== BASE EMBED CREATOR ====================

def create_base_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None,
    color: int = Colors.BASE_GRAY,
    show_timestamp: bool = False
) -> discord.Embed:
    """
    Create a base embed with standard formatting
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
        color: Embed color (defaults to base gray)
        show_timestamp: Whether to show timestamp (default False)
    
    Returns:
        discord.Embed: Formatted embed
    """
    if show_timestamp:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
    else:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
    
    # Set footer with server icon if guild provided
    if guild and guild.icon:
        embed.set_footer(
            text="Pawn",
            icon_url=guild.icon.url
        )
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== SUCCESS EMBED ====================

def create_success_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create a success embed with green color
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
    
    Returns:
        discord.Embed: Success embed
    """
    embed = create_base_embed(
        title=f"✅ {title}",
        description=description,
        guild=guild,
        color=Colors.SUCCESS
    )
    return embed

# ==================== ERROR EMBED ====================

def create_error_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create an error embed with red color
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
    
    Returns:
        discord.Embed: Error embed
    """
    embed = create_base_embed(
        title=f"❌ {title}",
        description=description,
        guild=guild,
        color=Colors.ERROR
    )
    return embed

# ==================== INFO EMBED ====================

def create_info_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create an info embed with blurple color
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
    
    Returns:
        discord.Embed: Info embed
    """
    embed = create_base_embed(
        title=title,
        description=description,
        guild=guild,
        color=Colors.INFO
    )
    return embed

# ==================== WARNING EMBED ====================

def create_warning_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create a warning embed with yellow color
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
    
    Returns:
        discord.Embed: Warning embed
    """
    embed = create_base_embed(
        title=f"⚠️ {title}",
        description=description,
        guild=guild,
        color=Colors.WARNING
    )
    return embed

# ==================== SETUP EMBED ====================

def create_setup_embed(
    title: str,
    description: str,
    step: int,
    total_steps: int,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create a setup flow embed with progress indicator
    
    Args:
        title: Embed title
        description: Embed description
        step: Current step number
        total_steps: Total number of steps
        guild: Guild object for footer icon
    
    Returns:
        discord.Embed: Setup embed
    """
    embed = create_base_embed(
        title=title,
        description=description,
        guild=guild,
        color=Colors.BASE_GRAY
    )
    
    # Add progress bar to footer
    progress_bar = create_progress_bar(step, total_steps)
    current_footer = embed.footer.text if embed.footer else "Pawn"
    embed.set_footer(
        text=f"{current_footer} • {progress_bar} Step {step}/{total_steps}",
        icon_url=embed.footer.icon_url if embed.footer else None
    )
    
    return embed

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Create a visual progress bar
    
    Args:
        current: Current step
        total: Total steps
        length: Length of progress bar
    
    Returns:
        str: Progress bar string
    """
    filled = int((current / total) * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar

# ==================== DASHBOARD EMBED ====================

def create_dashboard_embed(
    guild: discord.Guild,
    total_members: int,
    active_members: int,
    top_member: Optional[Dict[str, Any]] = None,
    setup_date: str = "N/A"
) -> discord.Embed:
    """
    Create a loyalty dashboard embed
    
    Args:
        guild: Guild object
        total_members: Total registered members
        active_members: Active loyal members
        top_member: Top member data (user_id, messages, streak)
        setup_date: Date loyalty system was set up
    
    Returns:
        discord.Embed: Dashboard embed
    """
    embed = discord.Embed(
        title="📊 Loyalty Dashboard",
        description=f"**{guild.name}** Loyalty Statistics",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Add statistics fields
    embed.add_field(
        name="Total Registered",
        value=f"```{total_members}```",
        inline=True
    )
    
    embed.add_field(
        name="Active Members",
        value=f"```{active_members}```",
        inline=True
    )
    
    embed.add_field(
        name="Retention Rate",
        value=f"```{(active_members/total_members*100):.1f}%```" if total_members > 0 else "```0%```",
        inline=True
    )
    
    # Top member section
    if top_member:
        user_id = top_member.get("user_id")
        if user_id and isinstance(user_id, int):
            top_user = guild.get_member(user_id)
        else:
            top_user = None
        
        if top_user:
            embed.add_field(
                name="🏆 Top Member",
                value=f"{top_user.mention}\n"
                      f"Messages: {top_member.get('messages', 0)} | "
                      f"Streak: {top_member.get('streak', 0)} days",
                inline=False
            )
    
    # Setup info
    embed.add_field(
        name="Setup Date",
        value=f"```{setup_date}```",
        inline=False
    )
    
    # Set thumbnail and footer
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== LEADERBOARD EMBED ====================

def create_leaderboard_embed(
    title: str,
    members: List[Dict[str, Any]],
    guild: discord.Guild
) -> discord.Embed:
    """
    Create a leaderboard embed for top members
    
    Args:
        title: Embed title
        members: List of member dictionaries with user_id, messages, streak
        guild: Guild object
    
    Returns:
        discord.Embed: Leaderboard embed
    """
    embed = discord.Embed(
        title=f"🏆 {title}",
        description="",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Medal emojis for top 3
    medals = ["🥇", "🥈", "🥉"]
    
    if not members:
        embed.description = "No loyal members to display yet."
    else:
        leaderboard_text = ""
        
        for idx, member_data in enumerate(members, start=1):
            user_id = member_data.get("user_id")
            if not user_id or not isinstance(user_id, int):
                continue
                
            messages = member_data.get("messages", 0)
            streak = member_data.get("streak", 0)
            
            member = guild.get_member(user_id)
            if not member:
                continue
            
            # Add medal for top 3, number for others
            if idx <= 3:
                position = medals[idx - 1]
            else:
                position = f"`#{idx:02d}`"
            
            leaderboard_text += (
                f"{position} **{member.display_name}**\n"
                f"└ {messages} messages • {streak} day streak\n\n"
            )
        
        embed.description = leaderboard_text if leaderboard_text else "No data available."
    
    # Set footer
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== MEMBER PROFILE EMBED ====================

def create_member_profile_embed(
    member: discord.Member,
    member_data: Dict[str, Any],
    guild: discord.Guild,
    rank: int = 0
) -> discord.Embed:
    """
    Create a profile embed for a loyal member
    
    Args:
        member: Discord member object
        member_data: Member's loyalty data
        guild: Guild object
        rank: Member's rank in leaderboard
    
    Returns:
        discord.Embed: Member profile embed
    """
    embed = discord.Embed(
        title=f"Profile: {member.display_name}",
        description="",
        color=Colors.INFO,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Set member avatar
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    # Add fields
    embed.add_field(
        name="Joined Program",
        value=f"```{member_data.get('joined_date', 'N/A')}```",
        inline=True
    )
    
    embed.add_field(
        name="Last Active",
        value=f"```{member_data.get('last_activity', 'N/A')}```",
        inline=True
    )
    
    embed.add_field(
        name="Status",
        value="```✅ Active```" if member_data.get('opted_in', False) else "```❌ Inactive```",
        inline=True
    )
    
    embed.add_field(
        name="Total Messages",
        value=f"```{member_data.get('total_messages', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Current Streak",
        value=f"```{member_data.get('streak_days', 0)} days```",
        inline=True
    )
    
    if rank > 0:
        embed.add_field(
            name="Leaderboard Rank",
            value=f"```#{rank}```",
            inline=True
        )
    
    # Set footer
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== CREED EMBED ====================

def create_creed_embed(
    creed_message: str,
    guild: discord.Guild
) -> discord.Embed:
    """
    Create the loyalty creed embed for opt-in
    
    Args:
        creed_message: The creed message text
        guild: Guild object
    
    Returns:
        discord.Embed: Creed embed
    """
    embed = discord.Embed(
        title="🤝 Loyalty Program",
        description=creed_message + "\n\n**React with ✅ to join the loyalty program!**",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Add instructions
    embed.add_field(
        name="Benefits",
        value="• Exclusive role\n• Priority in events\n• Access to backup server",
        inline=False
    )
    
    embed.add_field(
        name="Requirements",
        value="• Stay active (3+ days inactivity = removed)\n• Follow server rules\n• Maintain positive standing",
        inline=False
    )
    
    # Set footer
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== NOTIFICATION EMBEDS ====================

def create_role_assigned_embed(guild: discord.Guild) -> discord.Embed:
    """Create embed for successful role assignment"""
    return create_success_embed(
        title="Loyalty Role Assigned",
        description=f"You've been granted the loyalty role in **{guild.name}**!\n"
                   "Stay active to keep your status.",
        guild=guild
    )

def create_role_removed_embed(guild: discord.Guild, reason: str = "inactivity") -> discord.Embed:
    """Create embed for role removal notification"""
    return create_warning_embed(
        title="Loyalty Role Removed",
        description=f"Your loyalty role in **{guild.name}** has been removed due to {reason}.\n"
                   "React to the creed message again to rejoin!",
        guild=guild
    )

def create_streak_milestone_embed(
    member: discord.Member,
    streak_days: int,
    guild: discord.Guild
) -> discord.Embed:
    """Create embed for streak milestones"""
    embed = discord.Embed(
        title="🔥 Streak Milestone!",
        description=f"Congratulations {member.mention}!\n"
                   f"You've reached a **{streak_days} day streak** in **{guild.name}**!",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== BACKUP SERVER EMBEDS ====================

def create_backup_invite_embed(
    guild_name: str,
    invite_link: str,
    guild_icon_url: Optional[str] = None
) -> discord.Embed:
    """Create embed for backup server invitation"""
    embed = discord.Embed(
        title="🔐 Backup Server Invitation",
        description=f"Hello from **{guild_name}**!\n\n"
                   f"As a loyal member, you're invited to our backup server for safety and continuity.\n\n"
                   f"**Invite Link:**\n{invite_link}",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Why Join?",
        value="• Stay connected if main server has issues\n"
              "• Exclusive loyal member community\n"
              "• Keep your status safe",
        inline=False
    )
    
    if guild_icon_url:
        embed.set_thumbnail(url=guild_icon_url)
        embed.set_footer(text="Pawn", icon_url=guild_icon_url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== ADMIN NOTIFICATION EMBEDS ====================

def create_setup_complete_embed(guild: discord.Guild) -> discord.Embed:
    """Create embed for setup completion"""
    embed = discord.Embed(
        title="✅ Setup Complete",
        description=f"Loyalty system is now active in **{guild.name}**!",
        color=Colors.SUCCESS,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Next Steps",
        value="• Members can now react to join\n"
              "• Monitor dashboard with `.m loyalty stats`\n"
              "• View leaderboard with `.m loyalty leaderboard`",
        inline=False
    )
    
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

def create_bulk_action_embed(
    action: str,
    success_count: int,
    failed_count: int,
    guild: discord.Guild
) -> discord.Embed:
    """Create embed for bulk action results"""
    embed = discord.Embed(
        title=f"Bulk {action.title()} Complete",
        description=f"**Results:**\n"
                   f"✅ Successful: {success_count}\n"
                   f"❌ Failed: {failed_count}",
        color=Colors.SUCCESS if failed_count == 0 else Colors.WARNING,
        timestamp=datetime.now(timezone.utc)
    )
    
    if guild.icon:
        embed.set_footer(text="Pawn", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Pawn")
    
    return embed

# ==================== HELPER FUNCTIONS ====================

def format_relative_time(timestamp_str: str) -> str:
    """
    Format timestamp string to relative time
    
    Args:
        timestamp_str: Timestamp in format "YYYY-MM-DD HH:MM:SS"
    
    Returns:
        str: Relative time string (e.g., "2 hours ago")
    """
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - timestamp
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def truncate_text(text: str, max_length: int = 1024) -> str:
    """
    Truncate text to fit Discord embed limits
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 1024 for embed field)
    
    Returns:
        str: Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

# ==================== PRIME NETWORK EMBEDS ====================

def create_welcome_embed(
    guild_name: str,
    hub_invite: str
) -> discord.Embed:
    """
    Create Prime Network welcome embed for new loyal members
    
    Args:
        guild_name: Gateway server name
        hub_invite: Main Hub invite link
    
    Returns:
        discord.Embed: Welcome embed with Hub invite
    """
    embed = discord.Embed(
        title="🎉 Welcome to Prime Network",
        description=f"Congratulations on joining the loyalty program in **{guild_name}**!\n\n"
                   f"You are now part of the **Prime Network** - a community of loyal members across multiple servers.",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="🏢 Visit the Main Hub",
        value=f"Connect with loyal members from across the network:\n{hub_invite}",
        inline=False
    )
    
    embed.add_field(
        name="✨ Your Status",
        value="✅ Active • 📍 Origin Gateway Recorded • 🌐 Network-Wide Recognition",
        inline=False
    )
    
    embed.set_footer(text=f"{guild_name} • Prime Network")
    
    return embed

def create_user_stats_embed(
    member: discord.Member,
    user_data: Dict[str, Any],
    guild: discord.Guild
) -> discord.Embed:
    """
    Create user statistics embed showing loyalty profile
    
    Args:
        member: Discord member object
        user_data: User's global loyalty data
        guild: Current guild object
    
    Returns:
        discord.Embed: User stats embed
    """
    embed = discord.Embed(
        title=f"👤 Loyalty Profile: {member.display_name}",
        description="",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc)
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    # Origin Gateway
    origin_gateway = user_data.get("origin_gateway_name", "Unknown")
    embed.add_field(
        name="🏠 Origin Gateway",
        value=f"```{origin_gateway}```",
        inline=True
    )
    
    # Current Active Location
    active_location = user_data.get("active_location_name", "None")
    embed.add_field(
        name="📍 Current Station",
        value=f"```{active_location}```",
        inline=True
    )
    
    # Streak
    streak = user_data.get("streak", 0)
    embed.add_field(
        name="🔥 Streak",
        value=f"```{streak} days```",
        inline=True
    )
    
    # Total Messages
    messages = user_data.get("total_messages", 0)
    embed.add_field(
        name="💬 Messages",
        value=f"```{messages}```",
        inline=True
    )
    
    # Status
    is_loyal = user_data.get("is_loyal", False)
    is_muted = user_data.get("is_muted", False)
    is_blacklisted = user_data.get("is_blacklisted", False)
    
    status_text = ""
    if is_blacklisted:
        status_text = "🚫 Blacklisted"
    elif is_muted:
        status_text = "🔇 Muted"
    elif is_loyal:
        status_text = "✅ Active"
    else:
        status_text = "❌ Inactive"
    
    embed.add_field(
        name="🎖️ Status",
        value=f"```{status_text}```",
        inline=True
    )
    
    # Join Date
    opt_in_date = user_data.get("opt_in_date", "Unknown")
    embed.add_field(
        name="📅 Join Date",
        value=f"```{opt_in_date}```",
        inline=True
    )
    
    embed.set_footer(text=f"{guild.name} • Prime Network")
    
    return embed

def create_broadcast_status_embed(
    guild: discord.Guild,
    message_text: str,
    sent_count: int,
    failed_count: int,
    is_global: bool = False
) -> discord.Embed:
    """
    Create broadcast status embed showing delivery results
    
    Args:
        guild: Current guild
        message_text: Message that was broadcast
        sent_count: Number of successful DMs
        failed_count: Number of failed DMs
        is_global: Whether this was a global broadcast
    
    Returns:
        discord.Embed: Broadcast status embed
    """
    scope = "🌐 Network-Wide" if is_global else "📍 Local Gateway"
    
    embed = discord.Embed(
        title=f"📢 Broadcast Complete {scope}",
        description=f"```{truncate_text(message_text, 256)}```",
        color=Colors.SUCCESS if failed_count == 0 else Colors.WARNING,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="✅ Sent",
        value=f"```{sent_count}```",
        inline=True
    )
    
    embed.add_field(
        name="❌ Failed",
        value=f"```{failed_count}```",
        inline=True
    )
    
    total = sent_count + failed_count
    if total > 0:
        success_rate = (sent_count / total) * 100
        embed.add_field(
            name="📊 Success Rate",
            value=f"```{success_rate:.1f}%```",
            inline=True
        )
    
    embed.set_footer(text=f"{guild.name} • Prime Network")
    
    return embed

def create_dashboard_embed_prime(
    guild: discord.Guild,
    top_users: List[Dict[str, Any]],
    total_loyal: int
) -> discord.Embed:
    """
    Create Prime Network 12-hour leaderboard dashboard
    
    Args:
        guild: Gateway server
        top_users: Top 10 users globally with rank data
        total_loyal: Total loyal members in network
    
    Returns:
        discord.Embed: Dashboard embed with medals
    """
    embed = discord.Embed(
        title="🏆 Prime Network Leaderboard",
        description=f"**Top Loyal Members** • Updated every 12 hours",
        color=0x2B2D31,
        timestamp=datetime.now(timezone.utc)
    )
    
    medals = ["🥇", "🥈", "🥉"]
    leaderboard_text = ""
    
    if not top_users:
        leaderboard_text = "No data available yet."
    else:
        for idx, user_data in enumerate(top_users[:10], start=1):
            user_id = user_data.get("user_id")
            streak = user_data.get("streak", 0)
            messages = user_data.get("total_messages", 0)
            
            # Get member from current guild or show ID
            if user_id is not None:
                try:
                    member = guild.get_member(int(user_id))
                    username = member.display_name if member else f"User {user_id}"
                except:
                    username = f"User {user_id}"
            else:
                username = "Unknown User"
            
            # Use medal or number
            if idx <= 3:
                position = medals[idx - 1]
            else:
                position = f"`#{idx:02d}`"
            
            leaderboard_text += (
                f"{position} **{username}**\n"
                f"└─ {messages} msgs • {streak}🔥\n"
            )
    
    embed.add_field(
        name="📊 Leaderboard",
        value=leaderboard_text if leaderboard_text else "No data",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Network Stats",
        value=f"Total Loyal Members: **{total_loyal}**",
        inline=False
    )
    
    embed.set_footer(text=f"{guild.name} • Prime Network")
    
    return embed

def create_admin_action_embed(
    action_type: str,
    target_user: Optional[discord.Member],
    target_id: Optional[int],
    reason: str = "",
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create admin action confirmation embed
    
    Args:
        action_type: Type of action (blacklist_add, blacklist_remove, mute, unmute, remove_loyalty)
        target_user: Discord member object if available
        target_id: User ID if member not available
        reason: Reason for action
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Admin action embed
    """
    # Determine action details
    action_map = {
        "blacklist_add": ("🚫 Added to Blacklist", Colors.ERROR),
        "blacklist_remove": ("✅ Removed from Blacklist", Colors.SUCCESS),
        "mute": ("🔇 Member Muted", Colors.WARNING),
        "unmute": ("🔊 Member Unmuted", Colors.SUCCESS),
        "remove_loyalty": ("❌ Loyalty Removed", Colors.ERROR),
    }
    
    title, color = action_map.get(action_type, ("⚙️ Action Completed", Colors.INFO))
    
    if target_user:
        user_text = target_user.mention
    elif target_id:
        user_text = f"<@{target_id}>"
    else:
        user_text = "Unknown User"
    
    embed = discord.Embed(
        title=title,
        description=f"**Target:** {user_text}",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    
    if reason:
        embed.add_field(name="📝 Reason", value=reason, inline=False)
    
    if "blacklist" in action_type:
        embed.add_field(
            name="🌐 Scope",
            value="Network-wide (all gateways)",
            inline=False
        )
    
    if guild:
        embed.set_footer(text=f"{guild.name} • Prime Network")
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_invite_status_embed(
    guild: discord.Guild,
    hub_invite: str,
    sent_count: int,
    failed_count: int
) -> discord.Embed:
    """
    Create Hub invite delivery status embed
    
    Args:
        guild: Current gateway
        hub_invite: Hub invite link sent
        sent_count: Number of invites sent
        failed_count: Number of failures
    
    Returns:
        discord.Embed: Invite status embed
    """
    embed = discord.Embed(
        title="📮 Hub Invitations Sent",
        description=f"Loyal members in **{guild.name}** have been invited to the Main Hub",
        color=Colors.SUCCESS if failed_count == 0 else Colors.WARNING,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="🔗 Hub Link",
        value=hub_invite,
        inline=False
    )
    
    embed.add_field(
        name="✅ Sent",
        value=f"```{sent_count}```",
        inline=True
    )
    
    embed.add_field(
        name="❌ Failed",
        value=f"```{failed_count}```",
        inline=True
    )
    
    total = sent_count + failed_count
    if total > 0:
        success_rate = (sent_count / total) * 100
        embed.add_field(
            name="📊 Rate",
            value=f"```{success_rate:.1f}%```",
            inline=True
        )
    
    embed.set_footer(text=f"{guild.name} • Prime Network")
    
    return embed

# ==================== MOD COGS EMBEDS ====================

def create_module_help_embed(
    module_name: str,
    module_emoji: str,
    module_description: str,
    commands_list: List[Dict[str, str]],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create help embed for a module"""
    embed = discord.Embed(
        title=f"{module_emoji} {module_name.title()} Module",
        description=module_description,
        color=Colors.BASE_GRAY,
        timestamp=datetime.now(timezone.utc)
    )
    
    for cmd in commands_list:
        embed.add_field(
            name=f"`${cmd['name']}`",
            value=cmd['description'],
            inline=False
        )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_command_reference_embed(
    command_name: str,
    syntax: str,
    description: str,
    examples: List[str],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create detailed command reference"""
    embed = discord.Embed(
        title=f"Command: {command_name}",
        description=description,
        color=Colors.INFO,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Syntax",
        value=f"```\n{syntax}\n```",
        inline=False
    )
    
    if examples:
        examples_text = "\n".join(f"• `{ex}`" for ex in examples)
        embed.add_field(
            name="Examples",
            value=examples_text,
            inline=False
        )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_stats_overview_embed(
    stats: Dict[str, int],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create network statistics overview"""
    embed = discord.Embed(
        title="📊 Network Overview",
        description="Prime Network Statistics",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Gateways",
        value=f"```{stats.get('total_guilds', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Total Users",
        value=f"```{stats.get('total_users', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Loyal Members",
        value=f"```{stats.get('loyal_users', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Blacklisted",
        value=f"```{stats.get('blacklisted_users', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Trusted Admins",
        value=f"```{stats.get('trusted_users', 0)}```",
        inline=True
    )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_activity_stats_embed(
    stats: Dict[str, Any],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create activity statistics embed"""
    embed = discord.Embed(
        title="📈 Activity Statistics",
        description="Loyalty System Activity",
        color=Colors.INFO,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="Total Loyal",
        value=f"```{stats.get('total_loyal', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Active Today",
        value=f"```{stats.get('active_today', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Activity %",
        value=f"```{stats.get('activity_percentage', 0)}%```",
        inline=True
    )
    
    embed.add_field(
        name="Avg Messages",
        value=f"```{stats.get('average_messages', 0)}```",
        inline=True
    )
    
    embed.add_field(
        name="Avg Streak",
        value=f"```{stats.get('average_streak', 0)} days```",
        inline=True
    )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_server_config_embed(
    guild_name: str,
    config: Dict[str, Any],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create server configuration viewer"""
    embed = discord.Embed(
        title=f"⚙️ {guild_name} Configuration",
        description="Server Settings",
        color=Colors.BASE_GRAY,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Creed message
    creed_msg = config.get("creed_message_id")
    embed.add_field(
        name="Creed Message",
        value=f"```{creed_msg if creed_msg else 'Not Set'}```",
        inline=True
    )
    
    # Loyal role
    loyal_role = config.get("loyal_role_id")
    embed.add_field(
        name="Loyalty Role",
        value=f"```{loyal_role if loyal_role else 'Not Set'}```",
        inline=True
    )
    
    # Trusted admins
    trusted = config.get("trusted_local", [])
    embed.add_field(
        name="Local Trusted",
        value=f"```{len(trusted)} admin(s)```",
        inline=True
    )
    
    # Dashboard channel
    dashboard = config.get("dashboard_channel_id")
    embed.add_field(
        name="Dashboard Channel",
        value=f"```{dashboard if dashboard else 'Not Set'}```",
        inline=True
    )
    
    # Broadcast channel
    broadcast = config.get("broadcast_channel_id")
    embed.add_field(
        name="Broadcast Channel",
        value=f"```{broadcast if broadcast else 'Not Set'}```",
        inline=True
    )
    
    # System status
    is_hub = config.get("is_hub", False)
    embed.add_field(
        name="Hub Server",
        value=f"```{'Yes ✅' if is_hub else 'No ❌'}```",
        inline=True
    )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild_name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

def create_trend_embed(
    trend_data: List[Dict[str, Any]],
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """Create network join/leave trends embed"""
    embed = discord.Embed(
        title="📊 Network Trends",
        description="Join/Leave Activity",
        color=Colors.SPECIAL,
        timestamp=datetime.now(timezone.utc)
    )
    
    trend_text = "```\nDate       │ Joins │ Leaves\n"
    trend_text += "───────────┼───────┼────────\n"
    
    for trend in trend_data:
        date = trend.get("date", "Unknown")
        joins = trend.get("joins", 0)
        leaves = trend.get("leaves", 0)
        trend_text += f"{date} │  {joins:3d}  │  {leaves:3d}\n"
    
    trend_text += "```"
    
    embed.add_field(
        name="7-Day Activity",
        value=trend_text,
        inline=False
    )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed