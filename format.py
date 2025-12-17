import discord
from datetime import datetime
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
    color: int = Colors.BASE_GRAY
) -> discord.Embed:
    """
    Create a base embed with standard formatting
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer icon
        color: Embed color (defaults to base gray)
    
    Returns:
        discord.Embed: Formatted embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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