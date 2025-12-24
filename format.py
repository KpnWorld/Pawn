import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# ==================== COLOR SCHEME ====================

BRAND_COLOR = 0x8acaf5  # Prime Network blue - ONLY COLOR USED

# ==================== BASE EMBED CREATOR ====================

def create_base_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None,
    show_timestamp: bool = False
) -> discord.Embed:
    """
    Create a base embed with standard formatting
    Uses BRAND_COLOR for all embeds (no green/red/etc)
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer
        show_timestamp: Whether to show timestamp
    
    Returns:
        discord.Embed: Formatted embed
    """
    if show_timestamp:
        embed = discord.Embed(
            title=title,
            description=description,
            color=BRAND_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
    else:
        embed = discord.Embed(
            title=title,
            description=description,
            color=BRAND_COLOR
        )
    
    # Set footer with [Server Name] • Prime Network format
    if guild and guild.icon:
        embed.set_footer(
            text=f"{guild.name} • Prime Network",
            icon_url=guild.icon.url
        )
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

# ==================== SUCCESS EMBED ====================

def create_success_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create a success embed (uses same BRAND_COLOR)
    
    Args:
        title: Embed title (✅ will be added)
        description: Embed description
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Success embed
    """
    return create_base_embed(
        title=f"✅ {title}",
        description=description,
        guild=guild
    )

# ==================== ERROR EMBED ====================

def create_error_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create an error embed (uses same BRAND_COLOR)
    
    Args:
        title: Embed title (❌ will be added)
        description: Embed description
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Error embed
    """
    return create_base_embed(
        title=f"❌ {title}",
        description=description,
        guild=guild
    )

# ==================== INFO EMBED ====================

def create_info_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create an info embed (uses same BRAND_COLOR)
    
    Args:
        title: Embed title
        description: Embed description
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Info embed
    """
    return create_base_embed(
        title=title,
        description=description,
        guild=guild
    )

# ==================== WARNING EMBED ====================

def create_warning_embed(
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create a warning embed (uses same BRAND_COLOR)
    
    Args:
        title: Embed title (⚠️ will be added)
        description: Embed description
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Warning embed
    """
    return create_base_embed(
        title=f"⚠️ {title}",
        description=description,
        guild=guild
    )

# ==================== MODULE HELP EMBED ====================

def create_module_help_embed(
    module_name: str,
    module_icon: str,
    description: str,
    commands: List[Dict[str, str]],
    guild: Optional[discord.Guild] = None,
    page: int = 1,
    total_pages: int = 1
) -> discord.Embed:
    """
    Create a module help embed with command syntax
    
    Args:
        module_name: Name of the module (e.g., "Loyalty")
        module_icon: Emoji icon for module
        description: Module description
        commands: List of dicts with 'name' and 'syntax' keys
        guild: Guild object for footer
        page: Current page number
        total_pages: Total number of pages
    
    Returns:
        discord.Embed: Module help embed
    
    Example:
        commands = [
            {"name": "Set Creed", "syntax": "$ l creed <#channel> <message>"},
            {"name": "Setup Leaderboard", "syntax": "$ l leaderboard <#channel> <5|10>"}
        ]
    """
    embed = discord.Embed(
        title=f"{module_icon} {module_name} Module",
        description=description,
        color=BRAND_COLOR
    )
    
    # Add commands with syntax in code blocks
    for cmd in commands:
        embed.add_field(
            name=cmd["name"],
            value=f"```{cmd['syntax']}```",
            inline=False
        )
    
    # Add page info if multiple pages
    if total_pages > 1:
        footer_text = f"Prime Network • Page {page}/{total_pages}"
    else:
        footer_text = "Prime Network"
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • {footer_text}", icon_url=guild.icon.url)
    else:
        embed.set_footer(text=footer_text)
    
    return embed

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
        color=BRAND_COLOR
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
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
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
        color=BRAND_COLOR
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
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

# ==================== USER STATS EMBED ====================

def create_user_stats_embed(
    user: discord.Member,
    user_data: Dict[str, Any],
    guild: discord.Guild
) -> discord.Embed:
    """
    Create a user statistics embed
    
    Args:
        user: Discord member object
        user_data: User's loyalty data
        guild: Guild object
    
    Returns:
        discord.Embed: User stats embed
    """
    embed = discord.Embed(
        title=f"📊 {user.display_name}'s Loyalty Stats",
        color=BRAND_COLOR
    )
    
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    
    # Status
    is_loyal = user_data.get("is_loyal", False)
    is_inactive = user_data.get("is_inactive", False)
    
    if is_loyal and not is_inactive:
        status = "✅ Active Loyal"
    elif is_loyal and is_inactive:
        status = "⚠️ Inactive Loyal"
    else:
        status = "❌ Not Loyal"
    
    embed.add_field(
        name="Status",
        value=status,
        inline=True
    )
    
    # Streak
    embed.add_field(
        name="Streak",
        value=f"{user_data.get('streak', 0)} days",
        inline=True
    )
    
    # Messages
    embed.add_field(
        name="Total Messages",
        value=str(user_data.get('total_messages', 0)),
        inline=True
    )
    
    # Progress to next streak
    messages_since = user_data.get('messages_since_last_streak', 0)
    progress = f"{messages_since}/100"
    embed.add_field(
        name="Next Streak Progress",
        value=progress,
        inline=True
    )
    
    # Origin gateway
    origin = user_data.get('origin_gateway_name', 'Unknown')
    embed.add_field(
        name="Origin Gateway",
        value=origin,
        inline=True
    )
    
    # Main server
    main_server = user_data.get('main_server_name', 'Unknown')
    embed.add_field(
        name="Main Server",
        value=main_server,
        inline=True
    )
    
    # Joined date
    joined = user_data.get('opt_in_date', 'Unknown')
    embed.add_field(
        name="Joined Network",
        value=joined,
        inline=True
    )
    
    # Last activity
    last_active = user_data.get('last_activity', 'Unknown')
    embed.add_field(
        name="Last Active",
        value=last_active,
        inline=True
    )
    
    if guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

# ==================== NETWORK STATS EMBED ====================

def create_network_stats_embed(
    total_guilds: int,
    total_users: int,
    loyal_count: int,
    active_loyal: int,
    blacklisted: int,
    trusted_count: int,
    guild: Optional[discord.Guild] = None
) -> discord.Embed:
    """
    Create network overview statistics embed
    
    Args:
        total_guilds: Total gateway servers
        total_users: Total registered users
        loyal_count: Total loyal members
        active_loyal: Active loyal members
        blacklisted: Blacklisted users count
        trusted_count: Trusted admins count
        guild: Guild object for footer
    
    Returns:
        discord.Embed: Network stats embed
    """
    embed = discord.Embed(
        title="🌐 Prime Network Overview",
        description="Network-wide statistics",
        color=BRAND_COLOR
    )
    
    embed.add_field(
        name="Gateways",
        value=f"```{total_guilds}```",
        inline=True
    )
    
    embed.add_field(
        name="Total Users",
        value=f"```{total_users}```",
        inline=True
    )
    
    embed.add_field(
        name="Loyal Members",
        value=f"```{loyal_count}```",
        inline=True
    )
    
    embed.add_field(
        name="Active Loyal",
        value=f"```{active_loyal}```",
        inline=True
    )
    
    embed.add_field(
        name="Blacklisted",
        value=f"```{blacklisted}```",
        inline=True
    )
    
    embed.add_field(
        name="Trusted Admins",
        value=f"```{trusted_count}```",
        inline=True
    )
    
    if guild and guild.icon:
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

# ==================== GUILD CONFIG EMBED ====================

def create_guild_config_embed(
    guild: discord.Guild,
    guild_data: Dict[str, Any]
) -> discord.Embed:
    """
    Create guild configuration display embed
    
    Args:
        guild: Guild object
        guild_data: Guild's configuration data
    
    Returns:
        discord.Embed: Guild config embed
    """
    embed = discord.Embed(
        title=f"⚙️ {guild.name} Configuration",
        description="Server network settings",
        color=BRAND_COLOR
    )
    
    # Prefix
    embed.add_field(
        name="Prefix",
        value=f"`{guild_data.get('prefix', '$')}`",
        inline=True
    )
    
    # Hub status
    is_hub = guild_data.get('is_hub', False)
    embed.add_field(
        name="Status",
        value="🏢 Main Hub" if is_hub else "🌐 Gateway",
        inline=True
    )
    
    # Loyal role
    role_id = guild_data.get('loyal_role_id')
    if role_id:
        role = guild.get_role(role_id)
        role_text = role.mention if role else "Not Found"
    else:
        role_text = "Not Set"
    
    embed.add_field(
        name="Loyalty Role",
        value=role_text,
        inline=True
    )
    
    # Creed channel
    creed_channel_id = guild_data.get('creed_channel_id')
    if creed_channel_id:
        channel = guild.get_channel(creed_channel_id)
        creed_text = channel.mention if channel else "Not Found"
    else:
        creed_text = "Not Set"
    
    embed.add_field(
        name="Creed Channel",
        value=creed_text,
        inline=True
    )
    
    # Announcement channel
    ann_channel_id = guild_data.get('announcement_channel')
    if ann_channel_id:
        channel = guild.get_channel(ann_channel_id)
        ann_text = channel.mention if channel else "Not Found"
    else:
        ann_text = "Not Set"
    
    embed.add_field(
        name="Announcement Channel",
        value=ann_text,
        inline=True
    )
    
    # Dashboard channel
    dash_channel_id = guild_data.get('dashboard_channel_id')
    if dash_channel_id:
        channel = guild.get_channel(dash_channel_id)
        dash_text = channel.mention if channel else "Not Found"
    else:
        dash_text = "Not Set"
    
    embed.add_field(
        name="Leaderboard Channel",
        value=dash_text,
        inline=True
    )
    
    # Trusted local admins
    trusted = guild_data.get('trusted_local', [])
    trusted_text = f"{len(trusted)} local admins" if trusted else "None"
    
    embed.add_field(
        name="Trusted Admins",
        value=trusted_text,
        inline=True
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"{guild.name} • Prime Network", icon_url=guild.icon.url)
    else:
        embed.set_footer(text="Prime Network")
    
    return embed

# ==================== HELPER FUNCTIONS ====================

def format_relative_time(timestamp_str: str) -> str:
    """
    Format timestamp string to relative time
    
    Args:
        timestamp_str: Timestamp in format "YYYY-MM-DD"
    
    Returns:
        str: Relative time string (e.g., "2 days ago")
    """
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
        delta = datetime.now() - timestamp
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        else:
            return "Today"
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