# StandLog CLI - All-in-one
from ui.viewer import viewer_menu, reminder
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from datetime import datetime
import os
import json

DATA_DIR = os.path.expanduser("~/.standlog/entries")
console = Console()


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_today_path():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"{today}.json")


def log_entry():
    console.print(Panel("[bold cyan]StandLog CLI - Daily Standup[/bold cyan]", expand=False))
    did = Prompt.ask("[green]What did you work on today?[/green]")
    will_do = Prompt.ask("[yellow]What will you work on next?[/yellow]")
    blockers = Prompt.ask("[red]Any blockers?[/red]")
    tags = Prompt.ask("[magenta]Tags (comma separated, optional)[/magenta]", default="")
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "did": did,
        "will_do": will_do,
        "blockers": blockers,
        "tags": [t.strip() for t in tags.split(",") if t.strip()]
    }
    path = get_today_path()
    with open(path, "w") as f:
        json.dump(entry, f, indent=2)
    console.print("[bold green]Entry saved![/bold green]")


def view_entry():
    path = get_today_path()
    if not os.path.exists(path):
        console.print("[red]No entry for today yet.[/red]")
        return
    with open(path) as f:
        entry = json.load(f)
    panel = Panel(f"[b]What I did:[/b] {entry['did']}\n[b]What I'll do:[/b] {entry['will_do']}\n[b]Blockers:[/b] {entry['blockers']}\n[b]Tags:[/b] {', '.join(entry['tags']) if entry['tags'] else '-'}\n[b]Date:[/b] {entry['date']}", title="Today's Log", expand=False)
    console.print(panel)


def main_menu():
    while True:
        reminder()
        console.print("\n[bold cyan]StandLog CLI[/bold cyan]", style="bold")
        console.print("[1] Log today's standup\n[2] View today's log\n[3] Stats/Export/Reminder\n[4] Quit")
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="1")
        if choice == "1":
            log_entry()
        elif choice == "2":
            view_entry()
        elif choice == "3":
            viewer_menu()
        elif choice == "4":
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break


def main():
    ensure_data_dir()
    main_menu()

if __name__ == "__main__":
    main()
