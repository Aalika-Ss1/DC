import asyncio
import sys
from pathlib import Path

import discord

from app import read_token_from_credential_manager


GUILD_ID = 1422980759433777194
BOT_ROLE_NAME = "รองประมุข (ตัวลูก)"
REPORT_PATH = Path(__file__).resolve().parent / "assign_bot_role_report.txt"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def line(report, message):
    print(message)
    report.append(message)


async def main():
    token = read_token_from_credential_manager()
    if not token:
        raise RuntimeError("No bot token found in Windows Credential Manager.")

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    report = []

    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(GUILD_ID)
            if guild is None:
                line(report, f"ERROR: Bot cannot see guild {GUILD_ID}.")
                return

            bot_member = guild.me
            target_role = discord.utils.get(guild.roles, name=BOT_ROLE_NAME)
            line(report, f"Connected as {client.user}.")
            line(report, f"Guild: {guild.name} ({guild.id})")
            line(report, f"Bot current top role: {bot_member.top_role.name} position={bot_member.top_role.position}")

            if target_role is None:
                line(report, f"ERROR: Role not found: {BOT_ROLE_NAME}")
                return

            line(report, f"Target role: {target_role.name} position={target_role.position}")
            if target_role in bot_member.roles:
                line(report, f"Already has role: {BOT_ROLE_NAME}")
                return

            await bot_member.add_roles(target_role, reason="Grant Hilarious Manager management role per owner request")
            line(report, f"Assigned role to bot: {BOT_ROLE_NAME}")
        except discord.Forbidden as exc:
            line(report, f"ERROR: Discord denied permission: {exc}")
            line(report, "Manual action needed: assign this role to Hilarious Manager in Discord, or move the bot role above it.")
        except Exception as exc:
            line(report, f"ERROR: {type(exc).__name__}: {exc}")
        finally:
            REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
