# Voice Commands for StandLog CLI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress
from datetime import datetime, timedelta
import os
import json
import re
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write, read as wavread
import numpy as np
import threading
import time

# Try to import speech recognition library
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

console = Console()

# Path for data directory
DATA_DIR = os.path.expanduser("~/.standlog/entries")
VOICE_DIR = os.path.expanduser("~/.standlog/voice")
GOALS_PATH = os.path.expanduser("~/.standlog/goals.json")
VOICE_COMMANDS_CONFIG_PATH = os.path.expanduser("~/.standlog/voice_commands_config.json")

# Default voice commands configuration
DEFAULT_VOICE_COMMANDS_CONFIG = {
    "enabled": True,
    "recognition_engine": "google",  # Options: google, sphinx, azure, etc.
    "language": "en-US",
    "activation_phrase": "hey standlog",
    "command_timeout": 5,  # seconds
    "confidence_threshold": 0.6,
    "api_key": "",  # For services that require an API key
    "custom_commands": []
}

# Command patterns for natural language processing
COMMAND_PATTERNS = {
    "log_entry": [
        r"log (today|an entry|a standup)",
        r"create (a log|an entry|a standup)",
        r"start (logging|a log entry)"
    ],
    "view_entry": [
        r"show (today's log|today's entry|my log|my entry)",
        r"view (today's log|today's entry|my log|my entry)",
        r"display (today's log|today's entry|my log|my entry)"
    ],
    "search_logs": [
        r"search (for|logs|entries) (.*)",
        r"find (logs|entries) (.*)",
        r"look for (logs|entries) (.*)"
    ],
    "time_tracking": [
        r"show (time tracking|time stats|time statistics)",
        r"view (time tracking|time stats|time statistics)",
        r"how much time (did I spend|have I spent)"
    ],
    "set_goals": [
        r"set (goals|weekly goals)",
        r"create (goals|weekly goals)",
        r"add (goals|weekly goals)"
    ],
    "mark_goal": [
        r"mark goal (.*) (as done|as complete|complete|done)",
        r"complete goal (.*)",
        r"finish goal (.*)"
    ],
    "start_pomodoro": [
        r"start (a pomodoro|pomodoro|timer)",
        r"begin (a pomodoro|pomodoro|timer)",
        r"pomodoro (start|begin)"
    ],
    "log_mood": [
        r"log (my mood|mood)",
        r"set (my mood|mood)",
        r"record (my mood|mood)"
    ],
    "query_past": [
        r"what did I (do|work on) (on|last) (.*)",
        r"show me (what I did|my log|my entry) (on|for) (.*)",
        r"find (what I did|my log|my entry) (on|for) (.*)"
    ]
}

# Mapping of day names to date offsets for natural language processing
DAY_MAPPING = {
    "yesterday": 1,
    "today": 0,
    "monday": None,
    "tuesday": None,
    "wednesday": None,
    "thursday": None,
    "friday": None,
    "saturday": None,
    "sunday": None,
    "last monday": None,
    "last tuesday": None,
    "last wednesday": None,
    "last thursday": None,
    "last friday": None,
    "last saturday": None,
    "last sunday": None
}


def load_voice_commands_config():
    """Load voice commands configuration or create default if not exists"""
    if not os.path.exists(VOICE_COMMANDS_CONFIG_PATH):
        os.makedirs(os.path.dirname(VOICE_COMMANDS_CONFIG_PATH), exist_ok=True)
        with open(VOICE_COMMANDS_CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_VOICE_COMMANDS_CONFIG, f, indent=2)
        return DEFAULT_VOICE_COMMANDS_CONFIG
    
    try:
        with open(VOICE_COMMANDS_CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        console.print(f"[red]Error loading voice commands config: {e}[/red]")
        return DEFAULT_VOICE_COMMANDS_CONFIG


def save_voice_commands_config(config):
    """Save voice commands configuration"""
    try:
        with open(VOICE_COMMANDS_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        console.print(f"[red]Error saving voice commands config: {e}[/red]")
        return False


def check_speech_recognition():
    """Check if speech recognition is available"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        console.print("[yellow]Speech recognition library not found. Installing required package...[/yellow]")
        try:
            import pip
            pip.main(["install", "SpeechRecognition"])
            console.print("[green]Successfully installed SpeechRecognition![/green]")
            console.print("[yellow]Please restart the application to use voice commands.[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to install SpeechRecognition: {e}[/red]")
            console.print("[yellow]Please install it manually: pip install SpeechRecognition[/yellow]")
        return False
    return True


def get_date_from_day_name(day_name):
    """Convert day name to date"""
    day_name = day_name.lower()
    today = datetime.now()
    
    if day_name in ["yesterday", "today"]:
        offset = DAY_MAPPING[day_name]
        return (today - timedelta(days=offset)).strftime("%Y-%m-%d")
    
    # Handle day names (Monday, Tuesday, etc.)
    day_indices = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    if day_name in day_indices:
        # Find the most recent occurrence of this day
        target_idx = day_indices[day_name]
        today_idx = today.weekday()
        days_ago = (today_idx - target_idx) % 7
        if days_ago == 0:  # Today is the target day
            days_ago = 7  # Go back to previous week
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    if day_name.startswith("last "):
        # Handle "last Monday", "last Tuesday", etc.
        day_part = day_name.split("last ")[1]
        if day_part in day_indices:
            target_idx = day_indices[day_part]
            today_idx = today.weekday()
            days_ago = (today_idx - target_idx) % 7
            if days_ago == 0:  # Today is the target day
                days_ago = 7  # Go back to previous week
            return (today - timedelta(days=days_ago + 7)).strftime("%Y-%m-%d")
    
    # Try to parse as a date string (e.g., "2023-01-15")
    try:
        date_obj = datetime.strptime(day_name, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # If all else fails, return None
    return None


def record_audio(duration=5, fs=44100):
    """Record audio for a specified duration"""
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        if not input_devices:
            console.print("[yellow]No input device (microphone) found.[/yellow]")
            return None
    except Exception as e:
        console.print(f"[yellow]Could not query audio devices: {e}[/yellow]")
        return None
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Recording...[/cyan]", total=duration)
        
        # Start recording in a separate thread
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        
        # Update progress bar
        for _ in range(duration):
            time.sleep(1)
            progress.update(task, advance=1)
        
        sd.wait()  # Wait for recording to complete
    
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    write(tmpfile.name, fs, recording)
    tmpfile.close()
    return tmpfile.name


def transcribe_audio(audio_file, config=None):
    """Transcribe audio file to text using speech recognition"""
    if not check_speech_recognition():
        return None
    
    if config is None:
        config = load_voice_commands_config()
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
            # Use the configured recognition engine
            engine = config.get("recognition_engine", "google").lower()
            language = config.get("language", "en-US")
            
            if engine == "google":
                text = recognizer.recognize_google(audio_data, language=language)
            elif engine == "sphinx":
                text = recognizer.recognize_sphinx(audio_data, language=language)
            elif engine == "azure" and config.get("api_key"):
                text = recognizer.recognize_azure(audio_data, key=config.get("api_key"), language=language)
            else:
                # Default to Google if engine not supported
                text = recognizer.recognize_google(audio_data, language=language)
                
            return text.lower()
    except sr.UnknownValueError:
        console.print("[yellow]Speech recognition could not understand audio[/yellow]")
    except sr.RequestError as e:
        console.print(f"[red]Could not request results from speech recognition service: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error during speech recognition: {e}[/red]")
    
    return None


def parse_command(text):
    """Parse text to identify command and parameters"""
    if not text:
        return None, None
    
    text = text.lower()
    
    # Check each command pattern
    for command, patterns in COMMAND_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Extract parameters if any
                params = match.groups()[1:] if len(match.groups()) > 1 else None
                return command, params
    
    return None, None


def execute_command(command, params=None):
    """Execute the identified command with parameters"""
    if command == "log_entry":
        console.print("[green]Starting voice-to-text log entry...[/green]")
        voice_to_text_log()
    elif command == "view_entry":
        console.print("[green]Showing today's log...[/green]")
        from main import view_entry
        view_entry()
    elif command == "search_logs":
        if params and params[0]:
            search_term = params[0]
            console.print(f"[green]Searching logs for: {search_term}[/green]")
            from main import search_logs
            search_logs(search_term)
        else:
            console.print("[yellow]No search term provided.[/yellow]")
    elif command == "time_tracking":
        console.print("[green]Showing time tracking statistics...[/green]")
        from main import time_tracking_stats
        time_tracking_stats()
    elif command == "set_goals":
        console.print("[green]Starting voice-to-text goal setting...[/green]")
        voice_to_text_goals()
    elif command == "mark_goal":
        if params and params[0]:
            goal_number = params[0]
            console.print(f"[green]Marking goal {goal_number} as complete...[/green]")
            mark_goal_by_voice(goal_number)
        else:
            console.print("[yellow]No goal number provided.[/yellow]")
    elif command == "start_pomodoro":
        console.print("[green]Starting Pomodoro timer...[/green]")
        from ui.pomodoro import start_pomodoro_session
        start_pomodoro_session()
    elif command == "log_mood":
        console.print("[green]Starting voice mood logging...[/green]")
        voice_to_text_mood()
    elif command == "query_past":
        if params and params[0]:
            day_query = params[0]
            date = get_date_from_day_name(day_query)
            if date:
                console.print(f"[green]Showing log for {date}...[/green]")
                view_log_by_date(date)
            else:
                console.print(f"[yellow]Could not understand date: {day_query}[/yellow]")
        else:
            console.print("[yellow]No date provided.[/yellow]")
    else:
        console.print("[yellow]Command not recognized or not implemented yet.[/yellow]")


def voice_to_text_log():
    """Create a log entry using voice-to-text"""
    if not check_speech_recognition():
        return
    
    console.print(Panel("[bold cyan]Voice-to-Text Log Entry[/bold cyan]", expand=False))
    
    # What did you work on today?
    console.print("[cyan]What did you work on today? (Speak after the beep)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=15)
    did = transcribe_audio(audio_file) if audio_file else ""
    console.print(f"[dim]Transcribed: {did}[/dim]")
    os.unlink(audio_file)
    
    # What will you work on next?
    console.print("\n[cyan]What will you work on next? (Speak after the beep)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=15)
    will_do = transcribe_audio(audio_file) if audio_file else ""
    console.print(f"[dim]Transcribed: {will_do}[/dim]")
    os.unlink(audio_file)
    
    # Any blockers?
    console.print("\n[cyan]Any blockers? (Speak after the beep)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=10)
    blockers = transcribe_audio(audio_file) if audio_file else ""
    console.print(f"[dim]Transcribed: {blockers}[/dim]")
    os.unlink(audio_file)
    
    # Tags
    console.print("\n[cyan]Any tags? (Speak comma-separated tags after the beep)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=5)
    tags_text = transcribe_audio(audio_file) if audio_file else ""
    tags = [t.strip() for t in tags_text.split(",") if t.strip()]
    console.print(f"[dim]Transcribed tags: {', '.join(tags) if tags else 'None'}[/dim]")
    os.unlink(audio_file)
    
    # Time spent
    console.print("\n[cyan]How much time did you spend today in minutes? (Speak after the beep)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=5)
    time_text = transcribe_audio(audio_file) if audio_file else "0"
    os.unlink(audio_file)
    
    # Try to extract a number from the time text
    time_spent = 0
    time_match = re.search(r'\d+', time_text)
    if time_match:
        try:
            time_spent = int(time_match.group())
        except ValueError:
            time_spent = 0
    console.print(f"[dim]Time spent: {time_spent} minutes[/dim]")
    
    # Create the log entry
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "did": did,
        "will_do": will_do,
        "blockers": blockers,
        "tags": tags,
        "notes": "Created using voice commands",
        "voice_note": None,
        "time_spent": time_spent,
        "pomodoro_count": 0
    }
    
    # Save the entry
    path = os.path.join(DATA_DIR, datetime.now().strftime("%Y-%m-%d") + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(entry, f, indent=2)
    
    console.print("[bold green]Voice log entry saved![/bold green]")
    
    # Ask if user wants to add a mood
    console.print("\n[cyan]Would you like to log your mood? (Say yes or no)[/cyan]")
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=3)
    response = transcribe_audio(audio_file) if audio_file else ""
    os.unlink(audio_file)
    
    if response and ("yes" in response.lower() or "yeah" in response.lower()):
        voice_to_text_mood()


def voice_to_text_goals():
    """Set weekly goals using voice-to-text"""
    if not check_speech_recognition():
        return
    
    console.print(Panel("[bold yellow]Voice-to-Text Goal Setting[/bold yellow]", expand=False))
    console.print("[yellow]Speak your goals one by one. Say 'done' when finished.[/yellow]")
    
    goals = []
    while True:
        console.print(f"\n[cyan]Goal #{len(goals)+1} (or say 'done' to finish):[/cyan]")
        sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
        sd.wait()
        audio_file = record_audio(duration=10)
        goal_text = transcribe_audio(audio_file) if audio_file else ""
        os.unlink(audio_file)
        
        if not goal_text:
            console.print("[yellow]Could not understand. Please try again.[/yellow]")
            continue
        
        console.print(f"[dim]Transcribed: {goal_text}[/dim]")
        
        if "done" in goal_text.lower() or "finish" in goal_text.lower() or "end" in goal_text.lower():
            break
        
        goals.append({"goal": goal_text, "done": False})
    
    if goals:
        with open(GOALS_PATH, "w") as f:
            json.dump(goals, f, indent=2)
        console.print(f"[green]{len(goals)} goals saved![/green]")
    else:
        console.print("[yellow]No goals were set.[/yellow]")


def voice_to_text_mood():
    """Log mood using voice-to-text"""
    if not check_speech_recognition():
        return
    
    from ui.mood import MOOD_EMOJIS, MOOD_COLORS, log_mood
    
    console.print(Panel("[bold magenta]Voice Mood Logging[/bold magenta]", expand=False))
    console.print("[magenta]How are you feeling today on a scale of 1 to 5?[/magenta]")
    console.print("1: 😞 Very Bad, 2: 😟 Bad, 3: 😐 Neutral, 4: 😊 Good, 5: 😄 Very Good")
    
    sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
    sd.wait()
    audio_file = record_audio(duration=3)
    mood_text = transcribe_audio(audio_file) if audio_file else ""
    os.unlink(audio_file)
    
    # Try to extract a number from the mood text
    mood = None
    mood_match = re.search(r'\d+', mood_text)
    if mood_match:
        try:
            mood_num = int(mood_match.group())
            if 1 <= mood_num <= 5:
                mood = str(mood_num)
        except ValueError:
            pass
    
    # If no number found, try to match mood words
    if not mood:
        mood_words = {
            "1": ["very bad", "terrible", "awful", "horrible"],
            "2": ["bad", "poor", "not good", "sad"],
            "3": ["neutral", "okay", "ok", "fine", "alright"],
            "4": ["good", "well", "happy", "positive"],
            "5": ["very good", "excellent", "great", "amazing", "fantastic"]
        }
        
        for mood_level, words in mood_words.items():
            if any(word in mood_text.lower() for word in words):
                mood = mood_level
                break
    
    if mood:
        log_mood(mood)
        emoji = MOOD_EMOJIS.get(mood, "")
        color = MOOD_COLORS.get(mood, "white")
        console.print(f"[{color}]Mood logged: {emoji}[/{color}]")
    else:
        console.print("[yellow]Could not understand mood level. Please try again or use manual input.[/yellow]")


def mark_goal_by_voice(goal_identifier):
    """Mark a goal as complete using voice input"""
    if not os.path.exists(GOALS_PATH):
        console.print("[yellow]No goals set for this week.[/yellow]")
        return
    
    with open(GOALS_PATH) as f:
        goals = json.load(f)
    
    if not goals:
        console.print("[yellow]No goals set for this week.[/yellow]")
        return
    
    # Try to interpret goal_identifier as a number
    goal_idx = None
    try:
        # Check if it's a direct number
        goal_idx = int(goal_identifier) - 1
    except ValueError:
        # Check if it contains a number
        match = re.search(r'\d+', goal_identifier)
        if match:
            try:
                goal_idx = int(match.group()) - 1
            except ValueError:
                pass
    
    if goal_idx is not None and 0 <= goal_idx < len(goals):
        goals[goal_idx]["done"] = True
        with open(GOALS_PATH, "w") as f:
            json.dump(goals, f, indent=2)
        console.print(f"[green]Goal #{goal_idx+1} marked as complete![/green]")
    else:
        # If not a number, try to match by goal text
        console.print("[yellow]Could not identify goal by number. Showing all goals:[/yellow]")
        for idx, g in enumerate(goals):
            status = "[green]✔[/green]" if g["done"] else "[red]✗[/red]"
            console.print(f"[{idx+1}] {g['goal']} {status}")
        
        console.print("\n[cyan]Say the number of the goal to mark as complete:[/cyan]")
        sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
        sd.wait()
        audio_file = record_audio(duration=3)
        response = transcribe_audio(audio_file) if audio_file else ""
        os.unlink(audio_file)
        
        # Try to extract a number from the response
        match = re.search(r'\d+', response)
        if match:
            try:
                goal_idx = int(match.group()) - 1
                if 0 <= goal_idx < len(goals):
                    goals[goal_idx]["done"] = True
                    with open(GOALS_PATH, "w") as f:
                        json.dump(goals, f, indent=2)
                    console.print(f"[green]Goal #{goal_idx+1} marked as complete![/green]")
                else:
                    console.print("[red]Invalid goal number.[/red]")
            except ValueError:
                console.print("[red]Could not understand goal number.[/red]")
        else:
            console.print("[red]Could not understand goal number.[/red]")


def view_log_by_date(date_str):
    """View log entry for a specific date"""
    path = os.path.join(DATA_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        console.print(f"[red]No log entry found for {date_str}.[/red]")
        return
    
    with open(path) as f:
        entry = json.load(f)
    
    pomodoro_info = f"\n[b]Pomodoros completed:[/b] {entry.get('pomodoro_count', 0)}" if entry.get('pomodoro_count', 0) > 0 else ""
    
    # Display mood if available
    mood_info = ""
    if entry.get('mood'):
        from ui.mood import MOOD_EMOJIS, MOOD_COLORS
        mood = entry.get('mood')
        mood_text = MOOD_EMOJIS.get(mood, "Unknown")
        mood_color = MOOD_COLORS.get(mood, "white")
        mood_info = f"\n[b]Mood:[/b] [{mood_color}]{mood_text}[/{mood_color}]"
    
    panel = Panel(
        f"[b]What I did:[/b] {entry['did']}\n"
        f"[b]What I'll do:[/b] {entry['will_do']}\n"
        f"[b]Blockers:[/b] {entry['blockers']}\n"
        f"[b]Tags:[/b] {', '.join(entry['tags']) if entry['tags'] else '-'}\n"
        f"[b]Notes:[/b] {entry.get('notes','-')}\n"
        f"[b]Time spent:[/b] {entry.get('time_spent', 0)} min{pomodoro_info}{mood_info}\n"
        f"[b]Date:[/b] {entry['date']}", 
        title=f"Log for {date_str}", 
        expand=False
    )
    console.print(panel)
    
    if entry.get("voice_note") or os.path.exists(os.path.join(VOICE_DIR, os.path.basename(path).replace('.json', '.wav'))):
        play = Prompt.ask("Play attached voice note? (y/n)", choices=["y","n"], default="n")
        if play == "y":
            from main import play_voice_note
            play_voice_note(path)


def listen_for_commands():
    """Listen for voice commands in the background"""
    if not check_speech_recognition():
        return
    
    config = load_voice_commands_config()
    if not config.get("enabled", True):
        console.print("[yellow]Voice commands are disabled in settings.[/yellow]")
        return
    
    activation_phrase = config.get("activation_phrase", "hey standlog").lower()
    
    console.print(Panel(f"[bold green]Listening for voice commands...[/bold green]\n\nSay '{activation_phrase}' followed by your command.", expand=False))
    
    while True:
        console.print("[dim]Listening for activation phrase...[/dim]")
        audio_file = record_audio(duration=3)
        text = transcribe_audio(audio_file, config) if audio_file else ""
        os.unlink(audio_file)
        
        if text and activation_phrase in text.lower():
            console.print(f"[green]Activation phrase detected! What would you like to do?[/green]")
            sd.play(np.sin(2 * np.pi * 880 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
            sd.wait()
            
            command_audio = record_audio(duration=config.get("command_timeout", 5))
            command_text = transcribe_audio(command_audio, config) if command_audio else ""
            os.unlink(command_audio)
            
            if command_text:
                console.print(f"[dim]Heard: {command_text}[/dim]")
                command, params = parse_command(command_text)
                
                if command:
                    console.print(f"[green]Recognized command: {command}[/green]")
                    execute_command(command, params)
                else:
                    console.print("[yellow]Command not recognized. Please try again.[/yellow]")
            else:
                console.print("[yellow]Could not understand command. Please try again.[/yellow]")
        
        # Check if user wants to exit
        if Prompt.ask("Press Enter to continue listening or 'q' to quit", default="") == "q":
            break


def start_voice_command_listener():
    """Start the voice command listener in a separate thread"""
    if not check_speech_recognition():
        return
    
    thread = threading.Thread(target=listen_for_commands)
    thread.daemon = True  # Thread will exit when main program exits
    thread.start()
    return thread


def configure_voice_commands():
    """Configure voice commands settings"""
    config = load_voice_commands_config()
    
    console.print(Panel("[bold cyan]Voice Commands Configuration[/bold cyan]", expand=False))
    
    # Check if speech recognition is available
    if not check_speech_recognition():
        console.print("[yellow]Please restart the application after installing the required packages.[/yellow]")
        return
    
    # Show current configuration
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in config.items():
        if key != "custom_commands":  # Handle custom commands separately
            table.add_row(key, str(value))
    
    console.print(table)
    
    # Configuration options
    console.print("\n[bold cyan]Configuration Options:[/bold cyan]")
    console.print("[1] Enable/Disable Voice Commands")
    console.print("[2] Change Recognition Engine")
    console.print("[3] Change Language")
    console.print("[4] Change Activation Phrase")
    console.print("[5] Set Command Timeout")
    console.print("[6] Set API Key (for services that require it)")
    console.print("[7] Back")
    
    choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
    
    if choice == "1":
        enabled = Prompt.ask("Enable voice commands?", choices=["y", "n"], default="y" if config.get("enabled", True) else "n")
        config["enabled"] = (enabled.lower() == "y")
    elif choice == "2":
        console.print("\n[bold cyan]Available Recognition Engines:[/bold cyan]")
        console.print("[1] Google (default, requires internet)")
        console.print("[2] Sphinx (offline, less accurate)")
        console.print("[3] Azure (requires API key)")
        
        engine_choice = Prompt.ask("Choose an engine", choices=["1", "2", "3"], default="1")
        if engine_choice == "1":
            config["recognition_engine"] = "google"
        elif engine_choice == "2":
            config["recognition_engine"] = "sphinx"
            # Check if pocketsphinx is installed
            try:
                import pocketsphinx
            except ImportError:
                console.print("[yellow]Pocketsphinx not found. Installing required package...[/yellow]")
                try:
                    import pip
                    pip.main(["install", "pocketsphinx"])
                    console.print("[green]Successfully installed pocketsphinx![/green]")
                except Exception as e:
                    console.print(f"[red]Failed to install pocketsphinx: {e}[/red]")
                    console.print("[yellow]Please install it manually: pip install pocketsphinx[/yellow]")
        elif engine_choice == "3":
            config["recognition_engine"] = "azure"
            api_key = Prompt.ask("Enter your Azure Speech API key", password=True)
            config["api_key"] = api_key
    elif choice == "3":
        console.print("\n[bold cyan]Common Languages:[/bold cyan]")
        console.print("[1] English (US) - en-US")
        console.print("[2] English (UK) - en-GB")
        console.print("[3] Spanish - es-ES")
        console.print("[4] French - fr-FR")
        console.print("[5] German - de-DE")
        console.print("[6] Japanese - ja-JP")
        console.print("[7] Chinese - zh-CN")
        console.print("[8] Other (specify)")
        
        lang_choice = Prompt.ask("Choose a language", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")
        lang_map = {
            "1": "en-US",
            "2": "en-GB",
            "3": "es-ES",
            "4": "fr-FR",
            "5": "de-DE",
            "6": "ja-JP",
            "7": "zh-CN"
        }
        
        if lang_choice in lang_map:
            config["language"] = lang_map[lang_choice]
        else:
            custom_lang = Prompt.ask("Enter language code (e.g., it-IT for Italian)")
            config["language"] = custom_lang
    elif choice == "4":
        activation = Prompt.ask("Enter activation phrase", default=config.get("activation_phrase", "hey standlog"))
        config["activation_phrase"] = activation
    elif choice == "5":
        timeout = Prompt.ask("Command timeout in seconds", default=str(config.get("command_timeout", 5)))
        try:
            config["command_timeout"] = int(timeout)
        except ValueError:
            console.print("[red]Invalid timeout value. Using default (5 seconds).[/red]")
            config["command_timeout"] = 5
    elif choice == "6":
        api_key = Prompt.ask("Enter API key (for services that require it)", password=True)
        config["api_key"] = api_key
    elif choice == "7":
        return
    
    save_voice_commands_config(config)
    console.print("[green]Configuration saved![/green]")


def voice_commands_menu():
    """Main voice commands menu"""
    while True:
        console.print(Panel("[bold cyan]Voice Commands Menu[/bold cyan]", expand=False))
        console.print("[1] Test Voice Recognition")
        console.print("[2] Start Voice Command Listener")
        console.print("[3] Voice-to-Text Log Entry")
        console.print("[4] Voice-to-Text Goal Setting")
        console.print("[5] Voice Mood Logging")
        console.print("[6] Configure Voice Commands")
        console.print("[7] Back to Main Menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
        
        if choice == "1":
            if check_speech_recognition():
                console.print("[cyan]Speak after the beep to test voice recognition...[/cyan]")
                sd.play(np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)[:4410].astype(np.float32), 44100)
                sd.wait()
                audio_file = record_audio(duration=5)
                text = transcribe_audio(audio_file) if audio_file else ""
                os.unlink(audio_file)
                
                if text:
                    console.print(f"[green]Recognized: {text}[/green]")
                else:
                    console.print("[yellow]Could not recognize speech. Please try again.[/yellow]")
        elif choice == "2":
            listen_for_commands()
        elif choice == "3":
            voice_to_text_log()
        elif choice == "4":
            voice_to_text_goals()
        elif choice == "5":
            voice_to_text_mood()
        elif choice == "6":
            configure_voice_commands()
        elif choice == "7":
            break