"""Graph and visualization utilities for statistics"""
from typing import List, Dict, Any

def create_bar_chart(data: List[int], width: int = 20, height: int = 10) -> str:
    """Create an ASCII bar chart"""
    if not data:
        return "No data to display"
    
    max_val = max(data) if data else 1
    if max_val == 0:
        max_val = 1
    
    chart = ""
    
    # Create bars from top to bottom
    for row in range(height, 0, -1):
        chart += f"{int(max_val * row / height):4d} │ "
        
        for val in data:
            bar_height = int((val / max_val) * height)
            if bar_height >= row:
                chart += "███ "
            else:
                chart += "    "
        
        chart += "\n"
    
    # Bottom axis
    chart += "     └" + ("─" * (len(data) * 4 + 2)) + "\n"
    chart += "       "
    for i in range(len(data)):
        chart += f"{i+1:<4}"
    
    return chart

def create_line_chart(data: List[int], width: int = 40) -> str:
    """Create an ASCII line chart"""
    if not data or len(data) < 2:
        return "Insufficient data"
    
    max_val = max(data) if data else 1
    min_val = min(data) if data else 0
    
    if max_val == min_val:
        return "No variation in data"
    
    range_val = max_val - min_val or 1
    
    # Normalize to 10-unit height
    normalized = [(v - min_val) / range_val * 10 for v in data]
    
    chart = ""
    
    # Draw from top to bottom
    for height in range(10, -1, -1):
        line = f"{int(min_val + height * range_val / 10):4d} │ "
        
        for i, norm_val in enumerate(normalized):
            if i < len(normalized) - 1:
                curr_h = norm_val
                next_h = normalized[i + 1]
                
                if abs(curr_h - height) < 0.5 or abs(next_h - height) < 0.5:
                    line += "●"
                elif (curr_h > height and next_h < height) or (curr_h < height and next_h > height):
                    line += "│"
                elif curr_h >= height:
                    line += "─"
                else:
                    line += " "
                line += "  "
            else:
                if abs(norm_val - height) < 0.5:
                    line += "●"
                else:
                    line += " "
        
        chart += line + "\n"
    
    return chart

def create_trend_summary(trends: List[Dict[str, Any]]) -> str:
    """Create a text summary of trends"""
    if not trends:
        return "No trend data"
    
    summary = "```\n"
    summary += "Date       │ Joins │ Leaves │ Net\n"
    summary += "───────────┼───────┼────────┼─────\n"
    
    for trend in trends:
        date = trend.get("date", "Unknown")
        joins = trend.get("joins", 0)
        leaves = trend.get("leaves", 0)
        net = trend.get("net", 0)
        
        net_str = f"+{net}" if net > 0 else str(net)
        summary += f"{date} │  {joins:3d}  │  {leaves:3d}   │ {net_str:3s}\n"
    
    summary += "```"
    return summary

def create_simple_bar(value: int, max_value: int = 100, length: int = 20) -> str:
    """Create a simple horizontal progress bar"""
    if max_value == 0:
        percentage = 0
    else:
        percentage = int((value / max_value) * 100)
    
    filled = int((percentage / 100) * length)
    bar = "█" * filled + "░" * (length - filled)
    
    return f"{bar} {percentage}%"

def create_donut_text(value: int, total: int) -> str:
    """Create a text representation of percentage"""
    if total == 0:
        percentage = 0
    else:
        percentage = int((value / total) * 100)
    
    segments = 20
    filled = int((percentage / 100) * segments)
    
    donut = "●" * filled + "○" * (segments - filled)
    return f"{donut} {percentage}%"
