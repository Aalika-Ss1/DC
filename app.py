import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

try:
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies: please run 'pip install -r requirements.txt'")
    exit(1)

# Load environment variables from .env file if present
load_dotenv()

APP_DIR = Path(__file__).resolve().parent
LOG_PATH = APP_DIR / "bot.log"
ROLES_REPORT_PATH = APP_DIR / "roles_report.txt"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

def format_role_report(guild):
    roles = [role for role in guild.roles if not role.is_default()]
    roles.sort(key=lambda role: role.position, reverse=True)

    lines = [
        f"Role report for {guild.name}",
        f"Server ID: {guild.id}",
        f"Role count: {len(roles)}",
        "",
    ]

    if not roles:
        lines.append("No custom roles found.")
        return "\n".join(lines)

    for index, role in enumerate(roles, start=1):
        permissions = []
        if role.permissions.administrator:
            permissions.append("ADMIN")
        if role.permissions.manage_guild:
            permissions.append("Manage Server")
        if role.permissions.manage_roles:
            permissions.append("Manage Roles")
        if role.permissions.manage_channels:
            permissions.append("Manage Channels")
        if role.permissions.ban_members:
            permissions.append("Ban")
        if role.permissions.kick_members:
            permissions.append("Kick")
        if role.permissions.moderate_members:
            permissions.append("Timeout")

        permission_text = ", ".join(permissions) if permissions else "standard"
        color = str(role.color) if str(role.color) != "#000000" else "default"
        lines.extend(
            [
                f"{index}. {role.name}",
                f"   ID: {role.id}",
                f"   Position: {role.position}",
                f"   Members: {len(role.members)}",
                f"   Color: {color}",
                f"   Mentionable: {role.mentionable}",
                f"   Hoisted: {role.hoist}",
                f"   Key permissions: {permission_text}",
            ]
        )

    return "\n".join(lines)

class HilariousManagerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.started_at = None
        self.synced_guilds = set()

    async def setup_hook(self):
        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} global slash command(s).")
        self.started_at = datetime.now(timezone.utc)

    async def on_ready(self):
        name = f"{self.user} ({self.user.id})" if self.user else "Unknown bot"
        logger.info(f"Online: {name}")
        logger.info(f"Connected to {len(self.guilds)} server(s).")
        
        for guild in self.guilds:
            if guild.id in self.synced_guilds:
                continue
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            self.synced_guilds.add(guild.id)
            logger.info(f"Synced {len(synced)} command(s) to server: {guild.name} ({guild.id})")
            
            report = format_role_report(guild)
            ROLES_REPORT_PATH.write_text(report, encoding="utf-8")
            logger.info(f"Saved role report for server: {guild.name}")

    async def on_interaction(self, interaction: discord.Interaction):
        logger.info(
            f"Interaction received: type={interaction.type} "
            f"command={getattr(interaction.command, 'name', None)} "
            f"user={interaction.user} guild={interaction.guild}"
        )

bot = HilariousManagerBot()

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    logger.info(f"Received /ping from {interaction.user} in {interaction.guild}")
    await interaction.response.defer(thinking=True)
    latency_ms = round(bot.latency * 1000)
    await interaction.followup.send(f"Pong! `{latency_ms} ms`")

@bot.tree.command(name="status", description="Check bot status")
async def status(interaction: discord.Interaction):
    logger.info(f"Received /status from {interaction.user} in {interaction.guild}")
    await interaction.response.defer(thinking=True)
    server_count = len(bot.guilds)
    latency_ms = round(bot.latency * 1000)
    uptime = "unknown"
    if bot.started_at:
        total_seconds = int((datetime.now(timezone.utc) - bot.started_at).total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"

    await interaction.followup.send(
        "Bot status\n"
        f"- Online: yes\n"
        f"- Servers: {server_count}\n"
        f"- Latency: {latency_ms} ms\n"
        f"- Uptime: {uptime}"
    )

@bot.tree.command(name="helpbot", description="Show available bot commands")
async def helpbot(interaction: discord.Interaction):
    logger.info(f"Received /helpbot from {interaction.user} in {interaction.guild}")
    await interaction.response.defer(thinking=True)
    await interaction.followup.send(
        "Available commands\n"
        "`/ping` - Check bot latency\n"
        "`/status` - Check bot status\n"
        "`/roles` - Read and summarize server roles\n"
        "`/helpbot` - Show this command list"
    )

@bot.tree.command(name="roles", description="Read and summarize server roles")
async def roles(interaction: discord.Interaction):
    logger.info(f"Received /roles from {interaction.user} in {interaction.guild}")
    await interaction.response.defer(thinking=True)
    if interaction.guild is None:
        await interaction.followup.send("Use this command inside a server.")
        return

    report = format_role_report(interaction.guild)
    ROLES_REPORT_PATH.write_text(report, encoding="utf-8")

    preview_lines = report.splitlines()
    preview = "\n".join(preview_lines[:35])
    if len(preview) > 1800:
        preview = preview[:1800] + "\n..."

    await interaction.followup.send(
        "Read server roles successfully.\n"
        f"Saved full report to `{ROLES_REPORT_PATH.name}`.\n\n"
        f"```text\n{preview}\n```"
    )

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    logger.error(f"Slash command error: {error}")
    try:
        if interaction.response.is_done():
            await interaction.followup.send("Command failed. Check the bot logs.")
        else:
            await interaction.response.send_message("Command failed. Check the bot logs.")
    except Exception as exc:
        logger.error(f"Could not send error response: {exc}")

def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.error("No token found. Please set DISCORD_TOKEN in the .env file or environment variables.")
        return

    try:
        logger.info("Connecting to Discord...")
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        logger.error("Login failed: invalid bot token.")
    except Exception as exc:
        logger.error(f"Bot error: {exc}")

if __name__ == "__main__":
    main()
