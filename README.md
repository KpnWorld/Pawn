# 🌐 Prime Network Discord Bot

A modular Discord bot managing a hub-and-spoke loyalty network system with global user tracking, network-wide permissions, and comprehensive admin tools.

## ⚙️ Core Configuration

| Setting | Value |
|---------|-------|
| Main Hub ID | `1449199091937443965` |
| Bot Owner ID | `895767962722660372` |
| Hub Invite | `https://discord.gg/F9PB47S3FJ` |
| Command Prefix | `$` (per-guild configurable) |
| Embed Color | `0x8acaf5` (Prime Network brand blue) |
| Footer Format | `[Server Name] • Prime Network` |

---

## 📋 Command Structure

### Core Commands (All Users)
```
@botname help          → Show all modules
@botname count         → Guild member count (exclude bots)
```

---

## 🎖️ Module 1: Loyalty (`$ l`)

**Purpose:** Manage creed messages, loyalty roles, and leaderboard dashboards per server.

### Admin Commands

| Command | Syntax | Behavior |
|---------|--------|----------|
| Set Creed | `$ l creed <#channel> <msg>` | Posts creed message with ✅ reaction. Users who react mark themselves as loyal, gain role, and are tracked globally. |
| Setup Leaderboard | `$ l leaderboard <#channel> <5|10>` | Creates empty leaderboard dashboard message in specified channel. Displays top 5 or 10 members by streak. |
| Refresh Leaderboard | `$ l refresh` | Manually refreshes leaderboard with current top 10 members. (Auto-refreshes every 4 hours) |
| Set Loyalty Role | `$ l role <@role>` | Assigns role to users who react to creed. Auto-grants on network join. |

### User Commands

| Command | Syntax | Behavior |
|---------|--------|----------|
| View Stats | `$ l user stats <@user>` | Display member's loyalty stats: streak, join date, message count, last active time. Shows "Not Loyal" if user hasn't reacted to creed. |
| Leave Network | `$ l user leave` | User opts-out of network. Removes loyalty status, loses streak, role removed from current guild. |

---

## 🌐 Module 2: Network (`$ net`)

**Purpose:** Manage network-wide communications, guild settings, and invites.

### Guild Configuration

| Command | Syntax | Behavior |
|---------|--------|----------|
| View Guild Config | `$ net guild` | Display current server's network settings (prefix, announcement channel, trusted users) |
| Change Prefix | `$ net guild prefix <prefix>` | Set bot prefix for this guild only (max 3 chars). Default: `$` |
| Set Announcement Channel | `$ net guild ann <#channel>` | Setup channel to receive announcements from hub news channel. Channel automatically becomes read-only. Creates webhook link to source. |

### Announcement Channel System

**How It Works:**
1. **Source Channel (Hardcoded):** Hub news channel (ID: 1450940467872006355) - this is where all announcements are posted
2. **Setup Command:** Any server admin runs `$ net guild ann #channel` 
3. **Bot Actions:**
   - ✅ Fetches the source announcement channel from hub
   - ✅ Makes the target channel read-only for everyone (@everyone cannot send messages)
   - ✅ Creates Discord webhook to link target channel to source
   - ✅ Saves channel configuration to database

4. **Auto-Broadcast:** Hub admin posts in source channel → Appears in all linked gateway channels (Discord handles it)

**Key Features:**
✓ Discord native channel following (webhooks) - works 24/7 without bot  
✓ Target channels automatically read-only (members can only view announcements)  
✓ One-time setup: `$ net guild ann #announcements`  
✓ Hardcoded source ensures all gateways sync from same hub channel  
✓ Up to 10 follower channels per source (Discord limit)  

**Permissions Required:**
- Bot needs **Manage Channels** (to set read-only permissions)
- Bot needs **Manage Webhooks** (to create follower webhook)

### Broadcasting

| Command | Syntax | Behavior |
|---------|--------|----------|
| Local Broadcast DM | `$ net broadcast dm <msg>` | DM loyal members in **current guild only**. (1s delay between messages) |
| Global Broadcast DM | `$ net broadcast global dm <msg>` | DM **all loyal members network-wide**. (1s delay between messages) |

### Network Operations

| Command | Syntax | Behavior |
|---------|--------|----------|
| Send Hub Invite | `$ net invite` | Send hub invite link to loyal members in this gateway. **Cannot use in main hub.** |
| Pick Random Members | `$ net pick <1-10>` | Select N random members from network. Returns list with IDs. |
| Direct Message User | `$ net dm <user_id|mention|name> <msg>` | Send DM to specific user. Accepts: user ID, mention `<@user>`, or name. Partial name matching supported. |

---

## 🔒 Module 3: Security (`$ sec`)

**Purpose:** Network-wide security, user management, and system control.

### User Management

| Command | Syntax | Behavior |
|---------|--------|----------|
| Ban User | `$ sec ban <user_id>` | Add user to global blacklist. Auto-ban from all servers on join. Prevents network access entirely. |
| Timeout User | `$ sec timeout <user_id> <5-60m>` | Apply Discord timeout across all servers (5-60 min range, clamped automatically). User cannot send messages. |

### System Control (Trusted Only)

| Command | Syntax | Behavior |
|---------|--------|----------|
| Stop System | `$ sec stop` | Disable entire loyalty system. All commands blocked. (Trusted users + Owner only) |
| Start System | `$ sec start` | Re-enable loyalty system. All commands work again. (Trusted users + Owner only) |
| Add Trusted User | `$ sec trusted add <@user>` | Grant admin access to user. Can use all module commands except sudo. (Trusted users + Owner only) |

---

## 🏢 Module 4: Server (`$ s`)

**Purpose:** Server management and network membership.

| Command | Syntax | Behavior |
|---------|--------|----------|
| Rename Server | `$ s name <newname>` | Change server name via bot. Updates guild name and internal database. |
| Leave Network | `$ s leave` | Remove this server from network completely. Deletes all server data and settings. |
| Lock Server | `$ s gate lock` | Disable `@everyone` send messages. Channel access denied (read-only). Users cannot post. |
| Nuke Server | `$ s gate nuke` | Delete **all channels and roles**. Create new read-only channel with hub invite link. Resets server. |
| View Config | `$ s config` | Display server settings: creed message, loyalty role, trusted users, leaderboard status, is_hub flag. |

---

## ⚙️ Module 5: Sudo (`$ su`) - Owner Only

**Purpose:** Bot owner administration, diagnostics, and system control. Owner ID: `895767962722660372`

### Trusted User Management

| Command | Syntax | Behavior |
|---------|--------|----------|
| Remove Trusted User | `$ su trusted remove <user_id>` | Remove user from global trusted list. Cannot remove self (owner). |
| Remove All Trusted | `$ su trusted remove all` | Clear all trusted users **except owner**. System requires at least owner. |

### Database Schema Inspection

| Command | Syntax | Behavior |
|---------|--------|----------|
| View Database Table | `$ su schema view <table>` | Inspect raw JSON table. Supports: `network_config`, `global_blacklist`, `global_users`, `guilds`, `stats`. Truncated to 1950 chars. |
| Check Schema Health | `$ su schema health` | Validate database structure. Reports missing tables/fields or ✅ if valid. |

### Network Statistics

| Command | Syntax | Behavior |
|---------|--------|----------|
| Network Overview | `$ su stats overview` | Total gateways, total users, loyal count, blacklisted count, trusted admin count. |
| Activity Stats | `$ su stats activity` | Active members today, activity percentage, average message count, average streak length. |
| Network Trends | `$ su stats network` | 7-day join/leave trends with ASCII table visualization. |

### Bot Control

| Command | Syntax | Behavior |
|---------|--------|----------|
| Change Presence | `$ su bot presence switch <type> <msg>` | Change bot status. Types: `streaming`, `playing`, `listening`, `watching`. Example: `$ su bot presence switch playing Prime Network` |
| Reset Presence | `$ su bot presence default` | Reset status to display loyal member count. |
| Manage Cogs | `$ su bot cog <load\|reload\|unload> <cog>` | Dynamically load/reload/unload modules at runtime. Example: `$ su bot cog reload loyalty` |
| Command Count | `$ su bot cmds` | Display total commands available across all cogs. |

---

## 🎯 Announcement System Configuration

**Hardcoded Source Channel ID:** `1450940467872006355`  
**Location:** Hub's news/announcements channel  
**Purpose:** All gateways follow this channel to receive announcements

```
HUB (News Channel)
  ↓ (webhook link)
Gateway 1 (Read-Only Channel) - receives all messages
Gateway 2 (Read-Only Channel) - receives all messages  
Gateway 3 (Read-Only Channel) - receives all messages
```

**Setup Command (for each gateway):**
```
$ net guild ann #announcements
```
This will:
1. ✅ Locate source channel in hub
2. ✅ Make target channel read-only (@everyone blocked)
3. ✅ Create webhook follower link
4. ✅ Save configuration

---

## 💾 Database Schema

File: `loyalty_data.json`

```json
{
    "network_config": {
        "main_hub_id": 1449199091937443965,
        "main_hub_invite": "https://discord.gg/F9PB47S3FJ",
        "system_active": true,
        "trusted_users": [895767962722660372]
    },
    "global_blacklist": [],
    "global_users": {
        "user_id_str": {
            "is_loyal": false,
            "streak": 0,
            "total_messages": 0,
            "last_activity": "YYYY-MM-DD",
            "opt_in_date": null,
            "origin_gateway_id": null,
            "origin_gateway_name": null,
            "active_location_id": null,
            "is_muted": false
        }
    },
    "guilds": {
        "guild_id_str": {
            "name": "String",
            "is_hub": false,
            "prefix": "$",
            "announcement_channel": null,
            "hub_ann_channel_id": null,
            "broadcast_channel": null,
            "loyal_role_id": null,
            "creed_message_id": null,
            "dashboard_msg_id": null,
            "dashboard_channel_id": null,
            "trusted_local": []
        }
    },
    "stats": {
        "daily_joins": {"YYYY-MM-DD": 0, ...},
        "daily_leaves": {"YYYY-MM-DD": 0, ...},
        "activity_snapshots": {"YYYY-MM-DD": 0, ...}
    }
}
```

---

## 🔐 Permission Tiers

| Tier | Users | Access |
|------|-------|--------|
| **Public** | Everyone | Help, count, user stats, leave network, view config |
| **Guild Admin** | Server admins + Trusted | Creed setup, leaderboard, roles, broadcasts, guild config, server management |
| **Trusted Admin** | Designated users | All guild commands + network bans, timeouts, system control, trusted management |
| **Owner Only** | 895767962722660372 | Sudo module, schema inspection, bot control, presence management, cog management |

---

## 📊 Background Tasks

| Task | Interval | Behavior |
|------|----------|----------|
| Update Presence | 5 minutes | Display bot status: "N loyal members" |
| Update Dashboard | 4 hours | Refresh leaderboard embeds in all guilds with top 10 members by streak |

---

## 🚀 Deployment

### Prerequisites
- Python 3.8+
- discord.py library
- Flask (keep-alive server)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set Discord token
export DISCORD_TOKEN="your_bot_token_here"

# Run bot
python bot.py
```

### What the Bot Does on Startup
✅ Loads `loyalty_data.json` (creates if missing)  
✅ Initializes all 5 cogs (loyalty, network, security, server, sudo)  
✅ Starts background tasks (presence update, dashboard refresh)  
✅ Launches Flask keep-alive server on port 8080  
✅ Syncs commands with Discord  
✅ Listens for `$` commands  

---

## 🛠️ Architecture

### Core Files

| File | Purpose |
|------|---------|
| `bot.py` | Core bot logic, data management, event handlers, background tasks, help system, cog loader |
| `format.py` | Centralized embed factory - all UI responses |
| `stats.py` | Shared statistics utilities (network overview, activity, trends) |
| `graph.py` | ASCII visualization functions (bar charts, trend tables) |

### Cog Modules

| File | Commands | Purpose |
|------|----------|---------|
| `cogs/loyalty.py` | 7 commands | Creed, leaderboards, roles, user stats |
| `cogs/network.py` | 8+ commands | Broadcasting, invites, guild config, random pick |
| `cogs/security.py` | 5 commands | Bans, timeouts, system control, trusted management |
| `cogs/server.py` | 5 commands | Rename, leave, gate control, config viewer |
| `cogs/sudo.py` | 10+ commands | Admin diagnostics, bot control, statistics |

---

## 🔄 User Flow Example

### Join Network as Loyal Member
1. User joins gateway guild
2. Admin posts creed with `$ l creed #general "Welcome to our loyalty program!"`
3. User reacts with ✅ to creed message
4. Bot automatically:
   - Marks user as `is_loyal: true`
   - Records `opt_in_date`, `origin_gateway_id`, `origin_gateway_name`
   - Grants loyalty role
   - Sends welcome DM
   - Increments `daily_joins` stat
5. User appears on leaderboard, tracked globally
6. All `$ broadcast global dm` reach this user network-wide

### Admin Broadcast Message
1. Admin runs `$ broadcast global dm "Hello network!"`
2. Bot fetches all users where `is_loyal: true`
3. Sends DM to each loyal member with 1-second delays
4. Excludes blacklisted users automatically

### System Lockdown
1. Owner runs `$ sec stop`
2. Sets `system_active: false`
3. All commands blocked with "System is offline" message
4. Owner later runs `$ sec start` to restore

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Commands not working | Check `$ net guild` prefix setting, may be different per server |
| Leaderboard not updating | Run `$ l leaderboard refresh` manually, or wait for 4-hour auto-refresh |
| User not appearing in network | Verify user reacted to creed message with ✅ |
| Bot offline | Check `$ su stats overview` to see if `system_active: false` |
| Database errors | Run `$ su schema health` to validate JSON structure |

---

## 📈 Statistics Features

The bot tracks:
- **Daily Joins/Leaves** - Members joining/leaving network per date
- **Activity Snapshots** - Active member count per date
- **User Streaks** - Consecutive active days per user
- **Message Counts** - Total messages per user across network
- **Guild Stats** - Members per guild, loyalty role status

View with: `$ su stats overview`, `$ su stats activity`, `$ su stats network`

---

## 🎨 Code Quality & Branding

### Embed Color System
All embeds use consistent **Prime Network brand color**: `0x8acaf5` (brand blue)
- **Base/Primary**: All main embeds use brand blue
- **Success**: Green `0x57F287` (confirmations, success messages)
- **Error**: Red `0xED4245` (errors, failures)
- **Info**: Blurple `0x5865F2` (general information)
- **Warning**: Yellow `0xFEE75C` (warnings, alerts)

### Input Interpreters

**User ID Commands** (`$ sec ban`, `$ sec timeout`) accept:
- User ID (e.g., `895767962722660372`)

**User Lookup Commands** (`$ net dm`, `$ l user stats`) accept:
- **User ID**: Numeric ID (e.g., `895767962722660372`)
- **Mention**: `<@user_id>` format (e.g., `<@895767962722660372>`)
- **Display Name**: Exact or partial name matching (case-insensitive)
- **Username**: Discord username (case-insensitive)

**Channel Commands** (`$ net guild ann`, `$ l creed`, `$ l leaderboard`) accept:
- **Mention**: `#channel-name` (recommended)
- **Channel ID**: Raw channel ID

**Role Commands** (`$ l role`) accept:
- **Mention**: `@role-name` (recommended)
- **Role ID**: Raw role ID

### Module Structure

| Module | File | Aliases | Main Group |
|--------|------|---------|-----------|
| Loyalty | `cogs/loyalty.py` | `l`, `loyalty` | `$ l` |
| Network | `cogs/network.py` | `net`, `network` | `$ net` |
| Security | `cogs/security.py` | `sec`, `security` | `$ sec` |
| Server | `cogs/server.py` | `s`, `server` | `$ s` |
| Sudo (Admin) | `cogs/sudo.py` | `su`, `sudo` | `$ su` |

### Subcommand Structure

**Loyalty Module:**
- `$ l user` → user stats, user leave
- Direct: creed, leaderboard, refresh, role

**Network Module:**
- `$ net guild` → guild config, prefix, announcement
- `$ net broadcast` → dm, global (with dm subcommand)
- Direct: invite, pick, dm

**Security Module:**
- `$ sec trusted` → add, remove
- Direct: ban, timeout, stop, start

**Sudo Module:**
- `$ su trusted` → remove
- `$ su schema` → view, health
- `$ su stats` → overview, activity, network
- `$ su bot` → presence (switch, default), cog, cmds

---

**Version:** 2.0 (Cog-Based Architecture)  
**Status:** Production Ready  
**Last Updated:** December 17, 2025  
**Commands Verified:** 35+ commands with accurate syntax and parameters
