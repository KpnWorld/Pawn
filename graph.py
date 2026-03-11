"""Statistics and analytics utilities for the Prime Network bot"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any
import json
import os

DATA_FILE = 'loyalty_data.json'

def load_data() -> Dict[str, Any]:
    """Load data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def get_network_overview() -> Dict[str, int]:
    """Get overall network statistics"""
    data = load_data()
    
    total_guilds = len(data.get("guilds", {}))
    total_users = len(data.get("global_users", {}))
    loyal_users = sum(1 for u in data.get("global_users", {}).values() if u.get("is_loyal", False))
    blacklisted_users = len(data.get("global_blacklist", []))
    
    return {
        "total_guilds": total_guilds,
        "total_users": total_users,
        "loyal_users": loyal_users,
        "blacklisted_users": blacklisted_users,
        "trusted_users": len(data.get("network_config", {}).get("trusted_users", []))
    }

def get_activity_stats() -> Dict[str, Any]:
    """Get activity statistics"""
    data = load_data()
    
    loyal_users = [u for u in data.get("global_users", {}).values() if u.get("is_loyal", False)]
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    active_today = sum(1 for u in loyal_users if u.get("last_activity") == today)
    
    average_messages = int(sum(u.get("total_messages", 0) for u in loyal_users) / len(loyal_users)) if loyal_users else 0
    average_streak = int(sum(u.get("streak", 0) for u in loyal_users) / len(loyal_users)) if loyal_users else 0
    
    return {
        "total_loyal": len(loyal_users),
        "active_today": active_today,
        "activity_percentage": int((active_today / len(loyal_users) * 100) if loyal_users else 0),
        "average_messages": average_messages,
        "average_streak": average_streak
    }

def get_network_trends(days: int = 7) -> Dict[str, Any]:
    """Get network join/leave trends over past N days"""
    data = load_data()
    stats = data.get("stats", {})
    
    daily_joins = stats.get("daily_joins", {})
    daily_leaves = stats.get("daily_leaves", {})
    
    today = datetime.now(timezone.utc)
    trend_data = []
    
    for i in range(days):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        joins = daily_joins.get(date_str, 0)
        leaves = daily_leaves.get(date_str, 0)
        trend_data.append({
            "date": date_str,
            "joins": joins,
            "leaves": leaves,
            "net": joins - leaves
        })
    
    trend_data.reverse()
    
    return {
        "period_days": days,
        "trends": trend_data,
        "total_joins": sum(t["joins"] for t in trend_data),
        "total_leaves": sum(t["leaves"] for t in trend_data)
    }

def record_join(user_id: int):
    """Record a user joining the network"""
    data = load_data()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    daily_joins = data.get("stats", {}).get("daily_joins", {})
    daily_joins[today] = daily_joins.get(today, 0) + 1
    
    if "stats" not in data:
        data["stats"] = {}
    data["stats"]["daily_joins"] = daily_joins
    
    save_data(data)

def record_leave(user_id: int):
    """Record a user leaving the network"""
    data = load_data()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    daily_leaves = data.get("stats", {}).get("daily_leaves", {})
    daily_leaves[today] = daily_leaves.get(today, 0) + 1
    
    if "stats" not in data:
        data["stats"] = {}
    data["stats"]["daily_leaves"] = daily_leaves
    
    save_data(data)

def record_activity_snapshot():
    """Record daily activity snapshot"""
    data = load_data()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    loyal_users = [u for u in data.get("global_users", {}).values() if u.get("is_loyal", False)]
    activity_snapshots = data.get("stats", {}).get("activity_snapshots", {})
    activity_snapshots[today] = len(loyal_users)
    
    if "stats" not in data:
        data["stats"] = {}
    data["stats"]["activity_snapshots"] = activity_snapshots
    
    save_data(data)

def save_data(data: Dict[str, Any]):
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving stats data: {e}")

def validate_schema() -> Tuple[bool, List[str]]:
    """Validate data schema integrity"""
    data = load_data()
    errors = []
    
    # Check network_config
    if "network_config" not in data:
        errors.append("Missing network_config table")
    else:
        required_fields = ["main_hub_id", "main_hub_invite", "system_active", "trusted_users"]
        for field in required_fields:
            if field not in data["network_config"]:
                errors.append(f"Missing network_config.{field}")
    
    # Check other tables exist
    required_tables = ["global_blacklist", "global_users", "guilds", "stats"]
    for table in required_tables:
        if table not in data:
            errors.append(f"Missing {table} table")
    
    # Check stats structure
    if "stats" in data:
        required_stats = ["daily_joins", "daily_leaves", "activity_snapshots"]
        for stat in required_stats:
            if stat not in data["stats"]:
                errors.append(f"Missing stats.{stat}")
    
    return len(errors) == 0, errors

def get_top_users(limit: int = 10) -> List[Tuple[int, Dict[str, Any]]]:
    """Get top users by streak"""
    data = load_data()
    
    users = [
        (int(uid), u) for uid, u in data.get("global_users", {}).items()
        if u.get("is_loyal", False)
    ]
    users.sort(key=lambda x: x[1].get("streak", 0), reverse=True)
    
    return users[:limit]

def get_guild_stats(guild_id: int) -> Dict[str, Any]:
    """Get statistics for a specific guild"""
    data = load_data()
    guild_data = data.get("guilds", {}).get(str(guild_id), {})
    
    loyal_in_guild = sum(
        1 for u in data.get("global_users", {}).values()
        if u.get("is_loyal", False) and u.get("active_location_id") == guild_id
    )
    
    return {
        "guild_id": guild_id,
        "guild_name": guild_data.get("name", "Unknown"),
        "is_hub": guild_data.get("is_hub", False),
        "loyal_members": loyal_in_guild,
        "has_creed": guild_data.get("creed_message_id") is not None,
        "trusted_local": len(guild_data.get("trusted_local", []))
    }
