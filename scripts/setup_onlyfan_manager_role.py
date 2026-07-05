import asyncio
import sys
from pathlib import Path

import discord

from app import read_token_from_credential_manager


GUILD_ID = 1422980759433777194
MANAGER_ROLE_NAME = "Hilarious Manager"
ANCHOR_ROLE_NAME = "รองประมุข (ตัวลูก)"
HUMAN_ROLE_TO_REMOVE = "รองประมุข (ตัวลูก)"
REPORT_PATH = Path(__file__).resolve().parent / "setup_onlyfan_manager_role_report.txt"

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

    client = discord.Client(intents=discord.Intents.default())
    report = []

    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(GUILD_ID)
            if guild is None:
                line(report, f"ERROR: Bot cannot see guild {GUILD_ID}.")
                return

            bot_member = guild.me
            line(report, f"Connected as {client.user}.")
            line(report, f"Guild: {guild.name} ({guild.id})")
            line(report, f"Bot current top role: {bot_member.top_role.name} position={bot_member.top_role.position}")

            manager_role = discord.utils.get(guild.roles, name=MANAGER_ROLE_NAME)
            permissions = discord.Permissions.none()
            permissions.view_channel = True
            permissions.send_messages = True
            permissions.read_message_history = True
            permissions.connect = True
            permissions.speak = True
            permissions.manage_roles = True
            permissions.manage_channels = True
            permissions.create_instant_invite = True

            if manager_role is None:
                manager_role = await guild.create_role(
                    name=MANAGER_ROLE_NAME,
                    permissions=permissions,
                    color=discord.Color.blurple(),
                    hoist=False,
                    mentionable=False,
                    reason="Create separate bot manager role for Hilarious Manager",
                )
                line(report, f"Created role: {MANAGER_ROLE_NAME}")
            else:
                await manager_role.edit(
                    permissions=permissions,
                    color=discord.Color.blurple(),
                    hoist=False,
                    mentionable=False,
                    reason="Update Hilarious Manager role permissions",
                )
                line(report, f"Updated role: {MANAGER_ROLE_NAME}")

            anchor_role = discord.utils.get(guild.roles, name=ANCHOR_ROLE_NAME)
            if anchor_role is None:
                line(report, f"ERROR: Anchor role not found: {ANCHOR_ROLE_NAME}")
            elif anchor_role >= bot_member.top_role and anchor_role != bot_member.top_role:
                line(report, f"Cannot place under {ANCHOR_ROLE_NAME}: anchor is above bot top role.")
            else:
                await manager_role.edit(
                    position=max(anchor_role.position - 1, 1),
                    reason="Place Hilarious Manager role below รองประมุข",
                )
                line(report, f"Placed {MANAGER_ROLE_NAME} below {ANCHOR_ROLE_NAME}.")

            bot_member = guild.me
            if manager_role not in bot_member.roles:
                await bot_member.add_roles(manager_role, reason="Assign Hilarious Manager role to bot")
                line(report, f"Assigned role to bot: {MANAGER_ROLE_NAME}")
            else:
                line(report, f"Bot already has role: {MANAGER_ROLE_NAME}")

            bot_member = guild.me
            human_role = discord.utils.get(guild.roles, name=HUMAN_ROLE_TO_REMOVE)
            if human_role and human_role in bot_member.roles:
                try:
                    await bot_member.remove_roles(human_role, reason="Move bot off human management role")
                    line(report, f"Removed human role from bot: {HUMAN_ROLE_TO_REMOVE}")
                except discord.Forbidden:
                    line(
                        report,
                        f"Could not remove {HUMAN_ROLE_TO_REMOVE} from bot due to Discord hierarchy. "
                        "Remove it manually after confirming Hilarious Manager is assigned.",
                    )

            bot_member = guild.me
            line(report, f"Bot final top role: {bot_member.top_role.name} position={bot_member.top_role.position}")
        except discord.Forbidden as exc:
            line(report, f"ERROR: Discord denied permission: {exc}")
        except Exception as exc:
            line(report, f"ERROR: {type(exc).__name__}: {exc}")
        finally:
            REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
