from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich import box
from datetime import datetime, timedelta
import os
import json
import time
import threading
import signal
console = Console()
DEFAULT_WORK_MINUTES = 25
DEFAULT_SHORT_BREAK_MINUTES = 5
DEFAULT_LONG_BREAK_MINUTES = 15
DEFAULT_POMODOROS_BEFORE_LONG_BREAK = 4
POMODORO_DATA_PATH = os.path.expanduser("~/.standlog/pomodoro_data.json")
timer_running = False
timer_thread = None
timer_stop_event = threading.Event()

def load_pomodoro_data():
    """Load Pomodoro data from file"""
    if not os.path.exists(POMODORO_DATA_PATH):
        return {}
    try:
        with open(POMODORO_DATA_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Error loading Pomodoro data: {e}[/yellow]")
        return {}

def save_pomodoro_data(data):
    """Save Pomodoro data to file"""
    os.makedirs(os.path.dirname(POMODORO_DATA_PATH), exist_ok=True)
    try:
        with open(POMODORO_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        console.print(f"[red]Error saving Pomodoro data: {e}[/red]")

def log_completed_pomodoro(duration_minutes, task_description):
    """Log a completed Pomodoro session"""
    data = load_pomodoro_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in data:
        data[today] = []
    
    data[today].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration_minutes": duration_minutes,
        "task": task_description
    })
    
    save_pomodoro_data(data)
    from main import DATA_DIR, get_today_path
    today_path = get_today_path()
    if os.path.exists(today_path):
        try:
            with open(today_path, 'r') as f:
                entry = json.load(f)
            entry['pomodoro_count'] = entry.get('pomodoro_count', 0) + 1
            
            with open(today_path, 'w') as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]Error updating today's log with Pomodoro data: {e}[/yellow]")

def run_timer(minutes, timer_type, task_description=""):
    """Run a timer for the specified number of minutes"""
    global timer_running
    
    seconds = minutes * 60
    end_time = datetime.now() + timedelta(minutes=minutes)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.fields[time_remaining]}"),
        TimeElapsedColumn(),
        expand=True
    ) as progress:
        task = progress.add_task(f"[cyan]{timer_type}[/cyan]", total=seconds, time_remaining="")
        
        while not progress.finished and not timer_stop_event.is_set():
            remaining = end_time - datetime.now()
            remaining_seconds = max(0, int(remaining.total_seconds()))
            mins, secs = divmod(remaining_seconds, 60)
            progress.update(task, completed=seconds - remaining_seconds, 
                          time_remaining=f"{mins:02d}:{secs:02d}")
            time.sleep(0.1)
    
    if not timer_stop_event.is_set():
        if timer_type == "Work Session":
            console.print(f"[bold green]✅ Pomodoro completed![/bold green]")
            log_completed_pomodoro(minutes, task_description)
        else:
            console.print(f"[bold blue]Break time over![/bold blue]")
    
    timer_running = False
    timer_stop_event.clear()

def start_timer_thread(minutes, timer_type, task_description=""):
    """Start a timer in a separate thread"""
    global timer_running, timer_thread, timer_stop_event
    
    if timer_running:
        console.print("[yellow]Timer already running![/yellow]")
        return
    
    timer_running = True
    timer_stop_event.clear()
    timer_thread = threading.Thread(
        target=run_timer, 
        args=(minutes, timer_type, task_description)
    )
    timer_thread.daemon = True
    timer_thread.start()

def stop_timer():
    """Stop the currently running timer"""
    global timer_running, timer_stop_event
    
    if not timer_running:
        console.print("[yellow]No timer is currently running![/yellow]")
        return
    
    timer_stop_event.set()
    console.print("[yellow]Timer stopped![/yellow]")

def start_pomodoro_session():
    """Start a Pomodoro session with customizable settings"""
    console.print(Panel("[bold cyan]Pomodoro Timer[/bold cyan]", expand=False))
    work_minutes = int(Prompt.ask("Work session length (minutes)", default=str(DEFAULT_WORK_MINUTES)))
    short_break_minutes = int(Prompt.ask("Short break length (minutes)", default=str(DEFAULT_SHORT_BREAK_MINUTES)))
    long_break_minutes = int(Prompt.ask("Long break length (minutes)", default=str(DEFAULT_LONG_BREAK_MINUTES)))
    pomodoros_before_long_break = int(Prompt.ask("Pomodoros before long break", default=str(DEFAULT_POMODOROS_BEFORE_LONG_BREAK)))
    task_description = Prompt.ask("What are you working on? (optional)", default="")
    console.print(f"[bold green]Starting Pomodoro session: {work_minutes} min work, "
                 f"{short_break_minutes} min short breaks, {long_break_minutes} min long breaks[/bold green]")
    
    pomodoro_count = 0
    try:
        while True:
            console.print(f"\n[bold cyan]Pomodoro #{pomodoro_count + 1}[/bold cyan]")
            start_timer_thread(work_minutes, "Work Session", task_description)
            while timer_running:
                try:
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    stop_timer()
                    raise KeyboardInterrupt
            
            pomodoro_count += 1
            if not Prompt.ask("Continue with next session?", choices=["y", "n"], default="y") == "y":
                break
            if pomodoro_count % pomodoros_before_long_break == 0:
                console.print(f"\n[bold magenta]Long Break ({long_break_minutes} min)[/bold magenta]")
                start_timer_thread(long_break_minutes, "Long Break")
            else:
                console.print(f"\n[bold blue]Short Break ({short_break_minutes} min)[/bold blue]")
                start_timer_thread(short_break_minutes, "Short Break")
            while timer_running:
                try:
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    stop_timer()
                    raise KeyboardInterrupt
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Pomodoro session interrupted![/yellow]")
    
    console.print(f"\n[bold green]Session summary: {pomodoro_count} Pomodoros completed![/bold green]")

def show_pomodoro_stats():
    """Show Pomodoro statistics"""
    data = load_pomodoro_data()
    
    if not data:
        console.print("[yellow]No Pomodoro data available yet.[/yellow]")
        return
    daily_stats = {}
    for date, sessions in data.items():
        total_minutes = sum(session["duration_minutes"] for session in sessions)
        daily_stats[date] = {
            "count": len(sessions),
            "total_minutes": total_minutes
        }
    table = Table(title="Recent Pomodoro Stats", box=box.ROUNDED)
    table.add_column("Date", style="cyan")
    table.add_column("Pomodoros", style="magenta")
    table.add_column("Total Time", style="green")
    sorted_dates = sorted(daily_stats.keys(), reverse=True)
    for date in sorted_dates[:7]:
        stats = daily_stats[date]
        hours, minutes = divmod(stats["total_minutes"], 60)
        time_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        table.add_row(date, str(stats["count"]), time_str)
    console.print(table)
    total_pomodoros = sum(stats["count"] for stats in daily_stats.values())
    total_minutes = sum(stats["total_minutes"] for stats in daily_stats.values())
    hours, minutes = divmod(total_minutes, 60)
    
    console.print(f"\n[bold]Total Pomodoros:[/bold] {total_pomodoros}")
    console.print(f"[bold]Total Focus Time:[/bold] {hours}h {minutes}m")
    if len(sorted_dates) >= 3:
        console.print("\n[bold]Productivity Pattern:[/bold]")
        recent_counts = [daily_stats[date]["count"] for date in sorted_dates[:7]]
        avg_count = sum(recent_counts) / len(recent_counts)
        if avg_count > 6:
            console.print("[green]Excellent productivity! Keep up the great work![/green]")
        elif avg_count > 4:
            console.print("[cyan]Good productivity level. You're doing well![/cyan]")
        elif avg_count > 2:
            console.print("[yellow]Moderate productivity. Consider increasing your focus sessions.[/yellow]")
        else:
            console.print("[red]Low productivity detected. Try to establish a more consistent Pomodoro routine.[/red]")
def pomodoro_menu():
    """Main Pomodoro menu"""
    while True:
        console.print("\n[bold cyan]Pomodoro Timer[/bold cyan]")
        console.print("[1] Start Pomodoro Session\n[2] View Pomodoro Stats\n[3] Back")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            start_pomodoro_session()
        elif choice == "2":
            show_pomodoro_stats()
            Prompt.ask("Press Enter to continue")
        elif choice == "3":
            break