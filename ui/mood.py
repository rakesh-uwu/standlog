from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from rich.columns import Columns
from rich.text import Text
from datetime import datetime, timedelta
import os
import json
import re
from collections import defaultdict

console = Console()


MOOD_DATA_PATH = os.path.expanduser("~/.standlog/mood_data.json")

MOOD_EMOJIS = {
    "1": "😢 Very Sad",
    "2": "😕 Sad",
    "3": "😐 Neutral",
    "4": "🙂 Happy",
    "5": "😄 Very Happy"
}

MOOD_COLORS = {
    "1": "red",
    "2": "yellow",
    "3": "blue",
    "4": "green",
    "5": "magenta"
}

def load_mood_data():
    """Load mood data from file"""
    if not os.path.exists(MOOD_DATA_PATH):
        return {}
    try:
        with open(MOOD_DATA_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Error loading mood data: {e}[/yellow]")
        return {}

def save_mood_data(data):
    """Save mood data to file"""
    os.makedirs(os.path.dirname(MOOD_DATA_PATH), exist_ok=True)
    try:
        with open(MOOD_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        console.print(f"[red]Error saving mood data: {e}[/red]")

def select_mood():
    """Prompt user to select a mood"""
    console.print(Panel("[bold cyan]How are you feeling today?[/bold cyan]", expand=False))
    for key, value in MOOD_EMOJIS.items():
        console.print(f"[{key}] {value}")
    
    mood = Prompt.ask("Select your mood (1-5)", choices=["1", "2", "3", "4", "5"], default="3")
    
    return mood

def log_mood(mood, date=None):
    """Log a mood entry"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    data = load_mood_data()
    
    if date not in data:
        data[date] = {}
    
    data[date]["mood"] = mood
    data[date]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_mood_data(data)
    console.print(f"[green]Mood logged: {MOOD_EMOJIS[mood]}[/green]")

def get_mood_for_date(date):
    """Get mood for a specific date"""
    data = load_mood_data()
    return data.get(date, {}).get("mood")

def show_mood_trends():
    """Show mood trends over time"""
    data = load_mood_data()
    
    if not data:
        console.print("[yellow]No mood data available yet.[/yellow]")
        return
    sorted_dates = sorted(data.keys())

    table = Table(title="Mood History", box=box.ROUNDED)
    table.add_column("Date", style="cyan")
    table.add_column("Mood", style="magenta")

    for date in sorted_dates[-14:]:  
        mood = data[date].get("mood")
        if mood:
            mood_text = MOOD_EMOJIS[mood]
            table.add_row(date, f"[{MOOD_COLORS[mood]}]{mood_text}[/{MOOD_COLORS[mood]}]")
    
    console.print(table)
    
    mood_counts = defaultdict(int)
    for date_data in data.values():
        mood = date_data.get("mood")
        if mood:
            mood_counts[mood] += 1
    
    total_moods = sum(mood_counts.values())
    if total_moods > 0:
        console.print("\n[bold]Mood Distribution:[/bold]")
        for mood, count in sorted(mood_counts.items()):
            percentage = (count / total_moods) * 100
            bar = "█" * int(percentage / 5)
            console.print(f"[{MOOD_COLORS[mood]}]{MOOD_EMOJIS[mood]}: {bar} {percentage:.1f}%[/{MOOD_COLORS[mood]}]")
    
    if len(sorted_dates) >= 3:
        console.print("\n[bold]Mood Trend:[/bold]")
        recent_moods = [int(data[date].get("mood", "3")) for date in sorted_dates[-7:] if "mood" in data[date]]
        
        if recent_moods:
            trend_line = ""
            for mood in recent_moods:
                trend_line += f"[{MOOD_COLORS[str(mood)]}]●[/{MOOD_COLORS[str(mood)]}]─"
            trend_line = trend_line[:-1]  
            console.print(trend_line)
            if len(recent_moods) >= 2:
                first_half = sum(recent_moods[:len(recent_moods)//2]) / (len(recent_moods)//2)
                second_half = sum(recent_moods[len(recent_moods)//2:]) / (len(recent_moods) - len(recent_moods)//2)
                
                if second_half > first_half + 0.5:
                    console.print("[green]Your mood is improving! 📈[/green]")
                elif first_half > second_half + 0.5:
                    console.print("[yellow]Your mood has been declining lately. 📉[/yellow]")
                else:
                    console.print("[blue]Your mood has been relatively stable. ↔️[/blue]")

def correlate_mood_with_productivity():
    """Correlate mood with productivity and blockers"""
    from main import DATA_DIR
    
    mood_data = load_mood_data()
    if not mood_data:
        console.print("[yellow]No mood data available for correlation.[/yellow]")
        return
    log_entries = {}
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and re.match(r'\d{4}-\d{2}-\d{2}\.json$', f)]
    
    for fname in files:
        date = fname.replace('.json', '')
        try:
            with open(os.path.join(DATA_DIR, fname)) as f:
                log_entries[date] = json.load(f)
        except Exception:
            continue

    common_dates = set(mood_data.keys()) & set(log_entries.keys())
    
    if not common_dates:
        console.print("[yellow]No overlapping data between mood and logs for correlation.[/yellow]")
        return
    
    mood_productivity = defaultdict(list)
    mood_blockers = defaultdict(int)
    
    for date in common_dates:
        mood = mood_data[date].get("mood")
        if not mood:
            continue
        
        time_spent = log_entries[date].get("time_spent", 0)
        pomodoro_count = log_entries[date].get("pomodoro_count", 0)
        has_blockers = bool(log_entries[date].get("blockers", "").strip())
        mood_productivity[mood].append((time_spent, pomodoro_count))
        if has_blockers:
            mood_blockers[mood] += 1
    console.print(Panel("[bold cyan]Mood & Productivity Correlation[/bold cyan]", expand=False))
    table = Table(title="Mood vs. Productivity", box=box.ROUNDED)
    table.add_column("Mood", style="cyan")
    table.add_column("Avg. Time (min)", style="green")
    table.add_column("Avg. Pomodoros", style="magenta")
    table.add_column("Correlation", style="yellow")
    
    for mood in sorted(mood_productivity.keys()):
        data_points = mood_productivity[mood]
        avg_time = sum(point[0] for point in data_points) / len(data_points) if data_points else 0
        avg_pomodoros = sum(point[1] for point in data_points) / len(data_points) if data_points else 0
        if avg_time > 90 or avg_pomodoros > 3:
            correlation = "[green]High productivity[/green]"
        elif avg_time > 45 or avg_pomodoros > 1:
            correlation = "[blue]Moderate productivity[/blue]"
        else:
            correlation = "[yellow]Lower productivity[/yellow]"   
        table.add_row(
            f"[{MOOD_COLORS[mood]}]{MOOD_EMOJIS[mood]}[/{MOOD_COLORS[mood]}]", 
            f"{avg_time:.1f}", 
            f"{avg_pomodoros:.1f}",
            correlation
        )
    console.print(table)
    console.print("\n[bold]Mood vs. Blockers:[/bold]")
    for mood in sorted(mood_blockers.keys()):
        total_entries = len(mood_productivity[mood])
        blocker_entries = mood_blockers[mood]
        percentage = (blocker_entries / total_entries) * 100 if total_entries else 0
        bar = "█" * int(percentage / 10)
        console.print(f"[{MOOD_COLORS[mood]}]{MOOD_EMOJIS[mood]}: {bar} {percentage:.1f}% days with blockers[/{MOOD_COLORS[mood]}]")
    console.print("\n[bold]Insights:[/bold]")
    if mood_productivity:
        best_mood = max(mood_productivity.keys(), 
                       key=lambda m: sum(p[0] + p[1]*25 for p in mood_productivity[m]) / len(mood_productivity[m]) if mood_productivity[m] else 0)
        console.print(f"[green]You tend to be most productive when your mood is: [{MOOD_COLORS[best_mood]}]{MOOD_EMOJIS[best_mood]}[/{MOOD_COLORS[best_mood]}][/green]")
    if mood_blockers:
        fewest_blockers_mood = min(mood_blockers.keys(), 
                                 key=lambda m: mood_blockers[m] / len(mood_productivity[m]) if mood_productivity[m] else float('inf'))
        console.print(f"[cyan]You report fewer blockers when your mood is: [{MOOD_COLORS[fewest_blockers_mood]}]{MOOD_EMOJIS[fewest_blockers_mood]}[/{MOOD_COLORS[fewest_blockers_mood]}][/cyan]")
def mood_menu():
    """Main mood tracking menu"""
    while True:
        console.print("\n[bold cyan]Mood Tracking[/bold cyan]")
        console.print("[1] Log Today's Mood\n[2] View Mood Trends\n[3] Mood & Productivity Correlation\n[4] Back")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            mood = select_mood()
            log_mood(mood)
        elif choice == "2":
            show_mood_trends()
            Prompt.ask("Press Enter to continue")
        elif choice == "3":
            correlate_mood_with_productivity()
            Prompt.ask("Press Enter to continue")
        elif choice == "4":
            break