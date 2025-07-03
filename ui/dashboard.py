from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import box
from datetime import datetime, timedelta
import os
import json
import re
from collections import defaultdict, Counter
import random

console = Console()
DATA_DIR = os.path.expanduser("~/.standlog/entries")
GOALS_PATH = os.path.expanduser("~/.standlog/goals.json")
DASHBOARD_CONFIG_PATH = os.path.expanduser("~/.standlog/dashboard_config.json")
THEMES_PATH = os.path.expanduser("~/.standlog/themes.json")

AVAILABLE_WIDGETS = {
    "goal_progress": "Weekly Goal Progress",
    "recent_logs": "Recent Logs",
    "time_tracking": "Time Tracking Stats",
    "mood_summary": "Mood Summary",
    "pomodoro_stats": "Pomodoro Statistics",
    "tag_cloud": "Tag Cloud",
    "streak_info": "Logging Streak",
    "custom_kpi": "Personal KPIs",
    "custom_ascii": "Custom ASCII Art"
}

DEFAULT_THEMES = {
    "default": {
        "name": "Default",
        "primary_color": "cyan",
        "secondary_color": "magenta",
        "accent_color": "green",
        "warning_color": "yellow",
        "error_color": "red",
        "box_style": "ROUNDED",
        "ascii_art": "default"
    },
    "dark_mode": {
        "name": "Dark Mode",
        "primary_color": "blue",
        "secondary_color": "purple",
        "accent_color": "green",
        "warning_color": "yellow",
        "error_color": "red",
        "box_style": "HEAVY",
        "ascii_art": "minimal"
    },
    "retro": {
        "name": "Retro",
        "primary_color": "bright_green",
        "secondary_color": "bright_yellow",
        "accent_color": "bright_blue",
        "warning_color": "bright_red",
        "error_color": "bright_magenta",
        "box_style": "DOUBLE",
        "ascii_art": "retro"
    }
}

ASCII_ART_VARIATIONS = {
    "default": [
        ("   _____ _             _      _                _     _     _ ", "magenta"),
        ("  / ____| |           | |    | |              | |   | |   | |", "blue"),
        (" | (___ | |_ __ _ _ __| | __ | |     ___   ___| | __| | __| |", "cyan"),
        ("  \___ \| __/ _` | '__| |/ / | |    / _ \ / __| |/ _` |/ _` |", "green"),
        ("  ____) | || (_| | |  |   <  | |___| (_) | (__| | (_| | (_| |", "yellow"),
        (" |_____/ \__\__,_|_|  |_|\_\ |______\___/ \___|_|\__,_|\__,_|", "red")
    ],
    "minimal": [
        ("╔═╗╔╦╗╔═╗╔╗╔╔╦╗╦  ╔═╗╔═╗", "blue"),
        ("╚═╗ ║ ╠═╣║║║ ║║║  ║ ║║ ╦", "cyan"),
        ("╚═╝ ╩ ╩ ╩╝╚╝═╩╝╩═╝╚═╝╚═╝", "green")
    ],
    "retro": [
        ("┌─┐┌┬┐┌─┐┌┐┌┌┬┐┬  ┌─┐┌─┐", "bright_green"),
        ("└─┐ │ ├─┤│││ │││  │ ││ ┬", "bright_yellow"),
        ("└─┘ ┴ ┴ ┴┘└┘─┴┘┴─┘└─┘└─┘", "bright_blue")
    ]
}

DEFAULT_DASHBOARD_CONFIG = {
    "active_widgets": ["goal_progress", "recent_logs", "time_tracking", "mood_summary"],
    "layout": "2x2",  
    "theme": "default",
    "custom_kpis": [
        {"name": "Weekly Pomodoros", "target": 20, "current": 0, "unit": "pomodoros"},
        {"name": "Daily Writing", "target": 30, "current": 0, "unit": "minutes"}
    ],
    "custom_ascii": None
}

def load_dashboard_config():
    """Load dashboard configuration or create default if not exists"""
    if not os.path.exists(DASHBOARD_CONFIG_PATH):
        os.makedirs(os.path.dirname(DASHBOARD_CONFIG_PATH), exist_ok=True)
        with open(DASHBOARD_CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_DASHBOARD_CONFIG, f, indent=2)
        return DEFAULT_DASHBOARD_CONFIG
    
    try:
        with open(DASHBOARD_CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        console.print(f"[red]Error loading dashboard config: {e}[/red]")
        return DEFAULT_DASHBOARD_CONFIG


def save_dashboard_config(config):
    """Save dashboard configuration"""
    try:
        with open(DASHBOARD_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        console.print(f"[red]Error saving dashboard config: {e}[/red]")
        return False


def load_themes():
    """Load themes or create default if not exists"""
    if not os.path.exists(THEMES_PATH):
        os.makedirs(os.path.dirname(THEMES_PATH), exist_ok=True)
        with open(THEMES_PATH, "w") as f:
            json.dump(DEFAULT_THEMES, f, indent=2)
        return DEFAULT_THEMES
    
    try:
        with open(THEMES_PATH, "r") as f:
            themes = json.load(f)
        return themes
    except Exception as e:
        console.print(f"[red]Error loading themes: {e}[/red]")
        return DEFAULT_THEMES


def save_themes(themes):
    """Save themes"""
    try:
        with open(THEMES_PATH, "w") as f:
            json.dump(themes, f, indent=2)
        return True
    except Exception as e:
        console.print(f"[red]Error saving themes: {e}[/red]")
        return False


def load_entry(filename):
    """Load a log entry from file"""
    try:
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading {filename}: {e}[/red]")
        return None


def get_all_entries():
    """Get all log entries"""
    entries = {}
    if not os.path.exists(DATA_DIR):
        return entries
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and re.match(r'\d{4}-\d{2}-\d{2}\.json$', f)]
    for fname in files:
        entry = load_entry(fname)
        if entry:
            date = fname.replace('.json', '')
            entries[date] = entry
    
    return entries


def load_goals():
    """Load weekly goals"""
    if not os.path.exists(GOALS_PATH):
        return []
    
    try:
        with open(GOALS_PATH, "r") as f:
            goals = json.load(f)
        return goals
    except Exception as e:
        console.print(f"[red]Error loading goals: {e}[/red]")
        return []


def get_current_streak():
    """Calculate current logging streak"""
    entries = get_all_entries()
    if not entries:
        return 0
    
    dates = sorted(entries.keys())
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if today not in dates and yesterday not in dates:
        return 0
    
    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        date1 = datetime.strptime(dates[i], "%Y-%m-%d")
        date2 = datetime.strptime(dates[i-1], "%Y-%m-%d")
        if (date1 - date2).days == 1:
            streak += 1
        else:
            break
    
    return streak


def get_mood_summary():
    """Get mood summary for the last 7 days"""
    try:
        from ui.mood import load_mood_data, MOOD_EMOJIS, MOOD_COLORS
        has_mood_module = True
    except ImportError:
        has_mood_module = False
        return None
    
    if not has_mood_module:
        return None
    
    mood_data = load_mood_data()
    if not mood_data:
        return None
    
    dates = sorted(mood_data.keys())[-7:]
    moods = []
    for date in dates:
        mood = mood_data[date].get("mood")
        if mood and mood.isdigit():
            moods.append((date, int(mood)))
    
    return moods


def get_pomodoro_stats():
    """Get pomodoro statistics"""
    entries = get_all_entries()
    if not entries:
        return None
    
    dates = sorted(entries.keys())[-7:]
    pomodoros = []
    for date in dates:
        entry = entries[date]
        count = entry.get("pomodoro_count", 0)
        try:
            count = int(count)
        except Exception:
            count = 0
        pomodoros.append((date, count))
    
    return pomodoros


def get_time_tracking_stats():
    """Get time tracking statistics"""
    entries = get_all_entries()
    if not entries:
        return None
    
    dates = sorted(entries.keys())[-7:]
    times = []
    for date in dates:
        entry = entries[date]
        time_spent = entry.get("time_spent", 0)
        try:
            time_spent = int(time_spent)
        except Exception:
            time_spent = 0
        times.append((date, time_spent))
    
    return times


def update_kpi_values(config):
    """Update KPI values based on log data"""
    entries = get_all_entries()
    if not entries or "custom_kpis" not in config:
        return config
    
    dates = sorted(entries.keys())[-7:]
    
    for i, kpi in enumerate(config["custom_kpis"]):
        if kpi["name"] == "Weekly Pomodoros":
            total_pomodoros = sum(entries[date].get("pomodoro_count", 0) for date in dates if date in entries)
            config["custom_kpis"][i]["current"] = total_pomodoros
        elif kpi["name"] == "Daily Writing":
            avg_time = sum(entries[date].get("time_spent", 0) for date in dates if date in entries) / max(1, len(dates))
            config["custom_kpis"][i]["current"] = round(avg_time)
    
    return config


def render_widget(widget_name, theme, box_width=40):
    """Render a single widget based on its type"""
    themes = load_themes()
    theme_config = themes.get(theme, themes["default"])
    primary_color = theme_config["primary_color"]
    secondary_color = theme_config["secondary_color"]
    accent_color = theme_config["accent_color"]
    warning_color = theme_config["warning_color"]
    box_style = getattr(box, theme_config["box_style"])
    
    if widget_name == "goal_progress":
        goals = load_goals()
        if not goals:
            return Panel("[italic]No goals set for this week[/italic]", 
                         title=f"[{primary_color}]Weekly Goal Progress[/{primary_color}]",
                         box=box_style, width=box_width)
        
        goal_text = ""
        for i, goal in enumerate(goals[:5]):  
            status = "✅" if goal.get("completed", False) else "⬜"
            goal_text += f"{status} [{accent_color}]{goal['goal']}[/{accent_color}]\n"
        
        return Panel(goal_text, 
                     title=f"[{primary_color}]Weekly Goal Progress[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "recent_logs":
        entries = get_all_entries()
        if not entries:
            return Panel("[italic]No logs found[/italic]", 
                         title=f"[{primary_color}]Recent Logs[/{primary_color}]",
                         box=box_style, width=box_width)
        
        dates = sorted(entries.keys(), reverse=True)[:3]  
        log_text = ""
        for date in dates:
            entry = entries[date]
            log_text += f"[{secondary_color}]{date}[/{secondary_color}]\n"
            log_text += f"[{accent_color}]Did:[/{accent_color}] {entry['did'][:40]}...\n"
        
        return Panel(log_text, 
                     title=f"[{primary_color}]Recent Logs[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "time_tracking":
        times = get_time_tracking_stats()
        if not times:
            return Panel("[italic]No time tracking data[/italic]", 
                         title=f"[{primary_color}]Time Tracking Stats[/{primary_color}]",
                         box=box_style, width=box_width)
        
        time_text = ""
        total_time = sum(t for _, t in times)
        time_text += f"[{secondary_color}]Total time:[/{secondary_color}] {total_time} min\n"
        for date, time in times[-3:]:  
            bar = "[" + accent_color + "]" + "█"*(time//10) + "[/" + accent_color + "]" if time else ""
            time_text += f"{date}: {time} min {bar}\n"
        
        return Panel(time_text, 
                     title=f"[{primary_color}]Time Tracking Stats[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "mood_summary":
        moods = get_mood_summary()
        if not moods:
            return Panel("[italic]No mood data available[/italic]", 
                         title=f"[{primary_color}]Mood Summary[/{primary_color}]",
                         box=box_style, width=box_width)
        
        try:
            from ui.mood import MOOD_EMOJIS, MOOD_COLORS
            mood_text = ""
            for date, mood in moods:
                emoji = MOOD_EMOJIS.get(str(mood), "")
                color = MOOD_COLORS.get(str(mood), "white")
                mood_text += f"{date}: [{color}]{emoji}[/{color}]\n"
            
            avg_mood = sum(m for _, m in moods) / len(moods)
            mood_text += f"\n[{secondary_color}]Average mood:[/{secondary_color}] {avg_mood:.1f}/5"
            
            return Panel(mood_text, 
                         title=f"[{primary_color}]Mood Summary[/{primary_color}]",
                         box=box_style, width=box_width)
        except ImportError:
            return Panel("[italic]Mood tracking module not available[/italic]", 
                         title=f"[{primary_color}]Mood Summary[/{primary_color}]",
                         box=box_style, width=box_width)
    
    elif widget_name == "pomodoro_stats":
        pomodoros = get_pomodoro_stats()
        if not pomodoros:
            return Panel("[italic]No pomodoro data available[/italic]", 
                         title=f"[{primary_color}]Pomodoro Statistics[/{primary_color}]",
                         box=box_style, width=box_width)
        
        pomo_text = ""
        total_pomodoros = sum(p for _, p in pomodoros)
        pomo_text += f"[{secondary_color}]Total pomodoros:[/{secondary_color}] {total_pomodoros}\n"
        for date, count in pomodoros[-3:]:  
            bar = "[" + accent_color + "]" + "●"*count + "[/" + accent_color + "]" if count else ""
            pomo_text += f"{date}: {count} {bar}\n"
        
        avg_pomodoros = total_pomodoros / len(pomodoros)
        pomo_text += f"\n[{secondary_color}]Average:[/{secondary_color}] {avg_pomodoros:.1f} per day"
        
        return Panel(pomo_text, 
                     title=f"[{primary_color}]Pomodoro Statistics[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "tag_cloud":
        entries = get_all_entries()
        if not entries:
            return Panel("[italic]No tags available[/italic]", 
                         title=f"[{primary_color}]Tag Cloud[/{primary_color}]",
                         box=box_style, width=box_width)
        
        all_tags = []
        for entry in entries.values():
            all_tags.extend(entry.get("tags", []))
        
        tag_counts = Counter(all_tags)
        if not tag_counts:
            return Panel("[italic]No tags found in logs[/italic]", 
                         title=f"[{primary_color}]Tag Cloud[/{primary_color}]",
                         box=box_style, width=box_width)
        
        top_tags = tag_counts.most_common(5)  
        tag_text = ""
        for tag, count in top_tags:
            tag_text += f"[{accent_color}]{tag}[/{accent_color}]: {count}\n"
        
        return Panel(tag_text, 
                     title=f"[{primary_color}]Tag Cloud[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "streak_info":
        streak = get_current_streak()
        streak_text = f"[{secondary_color}]Current streak:[/{secondary_color}] {streak} days\n"
        
        if streak >= 7:
            streak_text += f"[{accent_color}]🔥 Impressive streak! Keep it up![/{accent_color}]"
        elif streak >= 3:
            streak_text += f"[{accent_color}]👍 Good consistency![/{accent_color}]"
        elif streak > 0:
            streak_text += f"[{warning_color}]📝 Starting a new streak![/{warning_color}]"
        else:
            streak_text += f"[{warning_color}]⚠️ Log today to start a streak![/{warning_color}]"
        
        return Panel(streak_text, 
                     title=f"[{primary_color}]Logging Streak[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "custom_kpi":
        config = load_dashboard_config()
        config = update_kpi_values(config)
        
        if "custom_kpis" not in config or not config["custom_kpis"]:
            return Panel("[italic]No custom KPIs defined[/italic]", 
                         title=f"[{primary_color}]Personal KPIs[/{primary_color}]",
                         box=box_style, width=box_width)
        
        kpi_text = ""
        for kpi in config["custom_kpis"]:
            name = kpi.get("name", "KPI")
            current = kpi.get("current", 0)
            target = kpi.get("target", 100)
            unit = kpi.get("unit", "")
            
            percentage = min(100, int((current / max(1, target)) * 100))
            if percentage >= 80:
                color = accent_color
            elif percentage >= 50:
                color = secondary_color
            else:
                color = warning_color
            bar_width = 20
            filled = int((percentage / 100) * bar_width)
            bar = "[" + color + "]" + "█"*filled + "[/" + color + "]" + "░"*(bar_width-filled)
            
            kpi_text += f"[{secondary_color}]{name}[/{secondary_color}]\n"
            kpi_text += f"{current}/{target} {unit} ({percentage}%)\n"
            kpi_text += f"{bar}\n\n"
        
        return Panel(kpi_text, 
                     title=f"[{primary_color}]Personal KPIs[/{primary_color}]",
                     box=box_style, width=box_width)
    
    elif widget_name == "custom_ascii":
        config = load_dashboard_config()
        custom_ascii = config.get("custom_ascii")
        
        if custom_ascii:
            return Panel(custom_ascii, 
                         title=f"[{primary_color}]Custom ASCII Art[/{primary_color}]",
                         box=box_style, width=box_width)
        else:
            quotes = [
                "The secret of getting ahead is getting started. - Mark Twain",
                "It always seems impossible until it's done. - Nelson Mandela",
                "Don't watch the clock; do what it does. Keep going. - Sam Levenson",
                "The way to get started is to quit talking and begin doing. - Walt Disney",
                "You don't have to be great to start, but you have to start to be great. - Zig Ziglar"
            ]
            quote = random.choice(quotes)
            return Panel(f"[italic]{quote}[/italic]", 
                         title=f"[{primary_color}]Daily Inspiration[/{primary_color}]",
                         box=box_style, width=box_width)
    
    return Panel(f"[italic]Widget '{widget_name}' not found[/italic]", 
                 title=f"[{primary_color}]Unknown Widget[/{primary_color}]",
                 box=box_style, width=box_width)


def render_dashboard():
    """Render the customizable dashboard"""
    config = load_dashboard_config()
    themes = load_themes()
    theme = config.get("theme", "default")
    theme_config = themes.get(theme, themes["default"])
    primary_color = theme_config["primary_color"]
    box_style = getattr(box, theme_config["box_style"])
    
    ascii_art_type = theme_config.get("ascii_art", "default")
    art_lines = ASCII_ART_VARIATIONS.get(ascii_art_type, ASCII_ART_VARIATIONS["default"])
    art = "\n".join([f"[bold {color}]{line}[/bold {color}]" for line, color in art_lines])
    
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%H:%M:%S")
    clock_art = f"""
[bold white]┌───────────────┐
│   [{primary_color}]{time_str}[/{primary_color}]   │
│ [{theme_config['secondary_color']}]{date_str}[/{theme_config['secondary_color']}] │
└───────────────┘[/bold white]
"""
    
    console.print("\n")
    console.print(Align.center(Text.from_markup(art)))
    console.print(Align.center(Text.from_markup(clock_art)))
    console.print(Align.center(f"[bold {primary_color}]Welcome to your StandLog Dashboard![/bold {primary_color}] :notebook_with_decorative_cover: :sparkles:"))
    console.print(Align.center(f"[dim]Theme: {theme_config['name']}[/dim]"))
    console.print("\n")
    
    layout_type = config.get("layout", "2x2")
    active_widgets = config.get("active_widgets", [])
    
    if layout_type == "1x4": 
        layout = Layout()
        layout.split_row(
            Layout(name="left"),
            Layout(name="middle_left"),
            Layout(name="middle_right"),
            Layout(name="right")
        )
        
        for i, widget_name in enumerate(active_widgets[:4]):
            if i == 0:
                layout["left"].update(render_widget(widget_name, theme, box_width=30))
            elif i == 1:
                layout["middle_left"].update(render_widget(widget_name, theme, box_width=30))
            elif i == 2:
                layout["middle_right"].update(render_widget(widget_name, theme, box_width=30))
            elif i == 3:
                layout["right"].update(render_widget(widget_name, theme, box_width=30))
        
        console.print(layout)
    
    elif layout_type == "4x1":  
        for widget_name in active_widgets[:4]:
            console.print(render_widget(widget_name, theme, box_width=100))
    
    elif layout_type == "custom":  
        layout = Layout()
        layout.split(
            Layout(name="top"),
            Layout(name="bottom")
        )
        layout["bottom"].split_row(
            Layout(name="bottom_left"),
            Layout(name="bottom_right")
        )
        for i, widget_name in enumerate(active_widgets[:3]):
            if i == 0:
                layout["top"].update(render_widget(widget_name, theme, box_width=100))
            elif i == 1:
                layout["bottom_left"].update(render_widget(widget_name, theme, box_width=48))
            elif i == 2:
                layout["bottom_right"].update(render_widget(widget_name, theme, box_width=48))
        
        console.print(layout)
    
    else:  
        layout = Layout()
        layout.split(
            Layout(name="top"),
            Layout(name="bottom")
        )
        layout["top"].split_row(
            Layout(name="top_left"),
            Layout(name="top_right")
        )
        layout["bottom"].split_row(
            Layout(name="bottom_left"),
            Layout(name="bottom_right")
        )
        
        for i, widget_name in enumerate(active_widgets[:4]):
            if i == 0:
                layout["top_left"].update(render_widget(widget_name, theme, box_width=48))
            elif i == 1:
                layout["top_right"].update(render_widget(widget_name, theme, box_width=48))
            elif i == 2:
                layout["bottom_left"].update(render_widget(widget_name, theme, box_width=48))
            elif i == 3:
                layout["bottom_right"].update(render_widget(widget_name, theme, box_width=48))
        
        console.print(layout)


def configure_widgets():
    """Configure which widgets to display on the dashboard"""
    config = load_dashboard_config()
    active_widgets = config.get("active_widgets", [])
    
    console.print(Panel("[bold]Configure Dashboard Widgets[/bold]", style=f"bold cyan"))
    console.print("Select which widgets to display on your dashboard:\n")
    
    table = Table(title="Available Widgets")
    table.add_column("#", style="cyan")
    table.add_column("Widget", style="green")
    table.add_column("Status", style="yellow")
    
    for i, (widget_id, widget_name) in enumerate(AVAILABLE_WIDGETS.items(), 1):
        status = "[green]Active[/green]" if widget_id in active_widgets else "[dim]Inactive[/dim]"
        table.add_row(str(i), widget_name, status)
    
    console.print(table)
    console.print("\n")
    
    selected = Prompt.ask("Enter widget numbers to toggle (comma-separated)", default="")
    selected_indices = [int(s.strip()) for s in selected.split(",") if s.strip().isdigit()]

    widget_ids = list(AVAILABLE_WIDGETS.keys())
    for idx in selected_indices:
        if 1 <= idx <= len(widget_ids):
            widget_id = widget_ids[idx-1]
            if widget_id in active_widgets:
                active_widgets.remove(widget_id)
            else:
                active_widgets.append(widget_id)
    
    config["active_widgets"] = active_widgets
    save_dashboard_config(config)
    console.print("[green]Widget configuration updated![/green]")


def configure_layout():
    """Configure dashboard layout"""
    config = load_dashboard_config()
    current_layout = config.get("layout", "2x2")
    
    console.print(Panel("[bold]Configure Dashboard Layout[/bold]", style=f"bold cyan"))
    console.print(f"Current layout: [cyan]{current_layout}[/cyan]\n")
    console.print("Available layouts:\n")
    console.print("1. 2x2 Grid (default)")
    console.print("2. 1x4 Row")
    console.print("3. 4x1 Column")
    console.print("4. Custom (3 widgets in different sizes)\n")
    
    choice = Prompt.ask("Select layout", choices=["1", "2", "3", "4"], default="1")
    
    if choice == "1":
        config["layout"] = "2x2"
    elif choice == "2":
        config["layout"] = "1x4"
    elif choice == "3":
        config["layout"] = "4x1"
    elif choice == "4":
        config["layout"] = "custom"
    
    save_dashboard_config(config)
    console.print("[green]Layout configuration updated![/green]")


def configure_theme():
    """Configure dashboard theme"""
    config = load_dashboard_config()
    themes = load_themes()
    current_theme = config.get("theme", "default")
    
    console.print(Panel("[bold]Configure Dashboard Theme[/bold]", style=f"bold cyan"))
    console.print(f"Current theme: [cyan]{themes[current_theme]['name']}[/cyan]\n")
    console.print("Available themes:\n")
    
    for i, (theme_id, theme_data) in enumerate(themes.items(), 1):
        console.print(f"{i}. [{theme_data['primary_color']}]{theme_data['name']}[/{theme_data['primary_color']}]")
    
    console.print("\n")
    choice = Prompt.ask("Select theme", choices=[str(i) for i in range(1, len(themes)+1)], default="1")
    
    theme_ids = list(themes.keys())
    selected_idx = int(choice) - 1
    if 0 <= selected_idx < len(theme_ids):
        config["theme"] = theme_ids[selected_idx]
    
    save_dashboard_config(config)
    console.print("[green]Theme configuration updated![/green]")


def create_custom_theme():
    """Create a new custom theme"""
    themes = load_themes()
    
    console.print(Panel("[bold]Create Custom Theme[/bold]", style=f"bold cyan"))
    
    theme_name = Prompt.ask("Theme name", default="My Custom Theme")
    theme_id = theme_name.lower().replace(" ", "_")
    
    if theme_id in themes:
        console.print(f"[yellow]A theme with ID '{theme_id}' already exists. It will be overwritten.[/yellow]")
    
    color_options = [
        "red", "green", "blue", "cyan", "magenta", "yellow", "white", 
        "bright_red", "bright_green", "bright_blue", "bright_cyan", 
        "bright_magenta", "bright_yellow", "bright_white", 
        "purple", "orange", "pink"
    ]
    
    console.print("\nAvailable colors: " + ", ".join([f"[{c}]{c}[/{c}]" for c in color_options]))
    
    primary_color = Prompt.ask("Primary color", default="cyan", choices=color_options)
    secondary_color = Prompt.ask("Secondary color", default="magenta", choices=color_options)
    accent_color = Prompt.ask("Accent color", default="green", choices=color_options)
    
    box_styles = ["ROUNDED", "HEAVY", "DOUBLE", "SIMPLE"]
    box_style = Prompt.ask("Box style", default="ROUNDED", choices=box_styles)
    
    ascii_options = list(ASCII_ART_VARIATIONS.keys())
    ascii_art = Prompt.ask("ASCII art style", default="default", choices=ascii_options)
    
    themes[theme_id] = {
        "name": theme_name,
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "accent_color": accent_color,
        "warning_color": "yellow",
        "error_color": "red",
        "box_style": box_style,
        "ascii_art": ascii_art
    }
    
    save_themes(themes)
    console.print(f"[green]Custom theme '{theme_name}' created![/green]")
    
    apply_theme = Prompt.ask("Apply this theme now?", choices=["y", "n"], default="y")
    if apply_theme.lower() == "y":
        config = load_dashboard_config()
        config["theme"] = theme_id
        save_dashboard_config(config)
        console.print("[green]Theme applied![/green]")


def configure_kpis():
    """Configure personal KPIs"""
    config = load_dashboard_config()
    kpis = config.get("custom_kpis", [])
    
    console.print(Panel("[bold]Configure Personal KPIs[/bold]", style=f"bold cyan"))
    
    if kpis:
        console.print("Current KPIs:\n")
        for i, kpi in enumerate(kpis, 1):
            console.print(f"{i}. [cyan]{kpi['name']}[/cyan]: Target {kpi['target']} {kpi['unit']}")
    else:
        console.print("[yellow]No custom KPIs defined yet.[/yellow]")
    
    console.print("\nOptions:\n")
    console.print("1. Add new KPI")
    console.print("2. Edit existing KPI")
    console.print("3. Remove KPI")
    console.print("4. Back")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="1")
    
    if choice == "1":  
        name = Prompt.ask("KPI name", default="New KPI")
        target = Prompt.ask("Target value", default="100")
        try:
            target = int(target)
        except ValueError:
            target = 100
        unit = Prompt.ask("Unit (e.g., minutes, pomodoros)", default="units")
        
        new_kpi = {
            "name": name,
            "target": target,
            "current": 0,
            "unit": unit
        }
        
        kpis.append(new_kpi)
        config["custom_kpis"] = kpis
        save_dashboard_config(config)
        console.print("[green]New KPI added![/green]")
    
    elif choice == "2" and kpis:  
        idx = Prompt.ask("Enter KPI number to edit", choices=[str(i) for i in range(1, len(kpis)+1)])
        idx = int(idx) - 1
        
        name = Prompt.ask("KPI name", default=kpis[idx]["name"])
        target = Prompt.ask("Target value", default=str(kpis[idx]["target"]))
        try:
            target = int(target)
        except ValueError:
            target = kpis[idx]["target"]
        unit = Prompt.ask("Unit", default=kpis[idx]["unit"])
        
        kpis[idx]["name"] = name
        kpis[idx]["target"] = target
        kpis[idx]["unit"] = unit
        
        config["custom_kpis"] = kpis
        save_dashboard_config(config)
        console.print("[green]KPI updated![/green]")
    
    elif choice == "3" and kpis:  
        idx = Prompt.ask("Enter KPI number to remove", choices=[str(i) for i in range(1, len(kpis)+1)])
        idx = int(idx) - 1
        
        removed = kpis.pop(idx)
        config["custom_kpis"] = kpis
        save_dashboard_config(config)
        console.print(f"[green]KPI '{removed['name']}' removed![/green]")
    
    elif choice == "4" or not kpis:  
        return


def configure_custom_ascii():
    """Configure custom ASCII art"""
    config = load_dashboard_config()
    current_ascii = config.get("custom_ascii")
    
    console.print(Panel("[bold]Configure Custom ASCII Art[/bold]", style=f"bold cyan"))
    
    if current_ascii:
        console.print("Current custom ASCII art:\n")
        console.print(current_ascii)
    else:
        console.print("[yellow]No custom ASCII art defined yet.[/yellow]")
    
    console.print("\nOptions:\n")
    console.print("1. Create new ASCII art")
    console.print("2. Clear custom ASCII art")
    console.print("3. Back")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
    
    if choice == "1":  
        console.print("\nEnter your custom ASCII art (press Enter twice to finish):\n")
        ascii_art = multiline_input("")
        
        config["custom_ascii"] = ascii_art
        save_dashboard_config(config)
        console.print("[green]Custom ASCII art saved![/green]")
    
    elif choice == "2":  
        config["custom_ascii"] = None
        save_dashboard_config(config)
        console.print("[green]Custom ASCII art cleared![/green]")
    
    elif choice == "3":  
        return


def multiline_input(prompt):
    """Get multiline input from user"""
    if prompt:
        console.print(f"[bold]{prompt}[/bold]")
    console.print("[dim](Press Enter twice to finish)[/dim]")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    
    return "\n".join(lines)


def dashboard_menu():
    """Main dashboard menu"""
    while True:
        render_dashboard()
        
        console.print("\n[bold cyan]Dashboard Options[/bold cyan]")
        console.print("[1] Configure Widgets\n[2] Change Layout\n[3] Select Theme\n[4] Create Custom Theme\n[5] Configure Personal KPIs\n[6] Custom ASCII Art\n[7] Back to Main Menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
        
        if choice == "1":
            configure_widgets()
        elif choice == "2":
            configure_layout()
        elif choice == "3":
            configure_theme()
        elif choice == "4":
            create_custom_theme()
        elif choice == "5":
            configure_kpis()
        elif choice == "6":
            configure_custom_ascii()
        elif choice == "7":
            break