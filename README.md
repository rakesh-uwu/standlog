# StandLog -command line journal

A beautiful, developer-centric terminal journal and standup logger.
**Cross-platform:** Works on Linux, macOS, and Windows.

---

# StandLog -command line journal

## ✨ Features

- 📝 **Daily Standup Logging**: Log what you did, what you'll do, blockers, and tags.
- 😊 **Mood Tracking**: Track your daily mood with emoji selection and visualize trends over time.
- 📊 **Weekly Stats & Streaks**: Visualize your progress and blockers.
- 🔥 **Activity Heatmap**: See your logging streaks and activity by month.
- 📤 **Export**: Save your logs as Markdown or JSON.
- ⏰ **Reminders**: Get context-aware reminders (calendar, git, uptime) if you forget to log.
- 💬 **Feedback**: Leave and view feedback/encouragement on entries.
- 🔒 **Encryption**: Secure your logs with a passphrase.
- 🏅 **Badges**: Earn achievements for feedback, streaks, and more.
- ⏱️ **Pomodoro Timer**: Built-in timer for focused work sessions with productivity tracking.
- 🎛️ **Customizable Dashboard**: Configure your home screen with widgets, personal KPIs, and custom themes.
- 💻 **Cross-platform**: No reliance on pre-installed tools; all features work on Windows, macOS, and Linux.

---

## 📸 Screenshots / video Demos

- ![Main Menu](https://github.com/rakesh-uwu/standlog/blob/main/asset/home.png)

### video link: https://youtu.be/8AKgYASbgck

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/standlog.git
cd standlog
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

## For linux/mac os

```bash
python3 main.py
```

## For windows

```bash
python main.py
```

---

## 🛠️ Tools & Libraries Used

- [Rich](https://github.com/Textualize/rich) — Beautiful terminal formatting and widgets
- [Cryptography](https://cryptography.io/) — Secure encryption for your logs
- [Yagmail](https://github.com/kootenpv/yagmail) — Email integration (optional)
- [SoundDevice](https://python-sounddevice.readthedocs.io/) — Sound effects (optional)
- [Scipy](https://scipy.org/) — Audio processing (optional)
- [ICS](https://github.com/C4ptainCrunch/ics.py) — Calendar integration (optional)

All dependencies are listed in `requirements.txt`. No system tools are required for core features.
Optional features (like git/uptime reminders) are only shown if available.

---

## 🖥️ Platform Support

- **Linux, macOS, Windows** — All features work cross-platform.
- No reliance on pre-installed system tools.
- If a feature (like git or uptime) is not available, it is skipped gracefully.

---

## 📚 Features & How to Use

### Main Menu

- **Show weekly stats**: View your last 7 logs and most common blockers.
- **Export as Markdown/JSON**: Save your logs for backup or sharing.
- **Reminder**: Get a context-aware nudge if you forget to log.
- **Leave/View feedback**: Add or read encouragement on any entry.
- **Enable/Disable encryption**: Secure your logs with a passphrase.
- **Visualize journal (heatmap)**: See your activity and streaks.
- **ASCII Animation & Quote**: Enjoy a random ASCII animation and motivational quote.
- **Back**: Return to the previous menu or exit.

### Logging a Standup

1. Run the app.
2. Enter your daily standup details when prompted.
3. Use the viewer menu to explore stats, export, or view feedback.

### Pomodoro Timer

- Start a Pomodoro session with customizable work and break durations.
- Automatically track completed Pomodoros with your daily entries.
- View productivity statistics and patterns over time.
- Integrate your focus sessions with your daily logs.

### Mood Tracking

- Track your daily mood using a 1-5 scale with emoji representation.
- Visualize mood trends over time with colorful charts.
- Correlate your mood with productivity metrics and blockers.
- Gain insights into how your mood affects your work and vice versa.

### Customizable Dashboard

- Configure your home screen with a selection of widgets including:
  - Weekly Goal Progress
  - Recent Logs
  - Time Tracking Stats
  - Mood Summary
  - Pomodoro Statistics
  - Tag Cloud
  - Logging Streak
  - Personal KPIs
- Choose from different layout options (2x2 grid, 1x4 row, 4x1 column, or custom)
- Select from pre-defined themes or create your own custom themes
- Set up personal KPIs with progress tracking
- Add custom ASCII art to personalize your dashboard

### Encryption

- Enable encryption to protect your logs with a passphrase.
- Disable encryption to store logs in plain text.

### Feedback & Badges

- Leave feedback on any entry.
- Earn badges for activity, streaks, and feedback.

---

## 📝 Contributing

Pull requests and suggestions are welcome!

---

# StandLog -command line journal

## 📦 Project Structure

- `main.py`: Main entry point and splash/menu UI
- `ui/viewer.py`: Viewer menu, stats, export, reminders, feedback, heatmap, animation
- `ui/pomodoro.py`: Pomodoro timer functionality, session tracking, and productivity stats
- `ui/mood.py`: Mood tracking functionality, trend visualization, and productivity correlation
- `ui/dashboard.py`: Customizable dashboard with widgets, personal KPIs, and theme management
- `requirements.txt`: All dependencies
- `data/entries/`: Log storage (created automatically)

---
