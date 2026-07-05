# Hilarious Manager

This is a small Discord management bot starter with a Windows-friendly token window.

## Setup

1. Install Python 3.10 or newer.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

You can also double-click `run_discord_bot.bat`.

4. Paste your Discord bot token, click **Save token**, then **Start bot**.

The token is saved in Windows Credential Manager as `HilariousManager.Token`.

## Notes

- The bot currently only connects and reports when it is online.
- Current commands:
  - `/ping` checks bot latency.
  - `/status` checks online status, server count, latency, and uptime.
  - `/roles` reads and summarizes server roles.
  - `/helpbot` shows the command list.
- More commands and features can be added later in `app.py`.
- Keep your token private. Do not upload it to GitHub or share it.
