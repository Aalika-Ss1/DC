import asyncio
import sys
from pathlib import Path

import discord

from app import read_token_from_credential_manager


GUILD_ID = 1422980759433777194
DELETE_ROLE_NAME = "แม่ทัพ"
INVITE_ALLOWED_ROLE_NAMES = {
    "ประมุขน้อย (ตัวแม่)",
    "รองประมุข (ตัวลูก)",
    "เลขานุการสำนัก",
}
REPORT_PATH = Path(__file__).resolve().parent / "role_policy_apply_report.txt"

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
            line(report, f"Connected as {client.user}.")
            line(report, f"Guild: {guild.name} ({guild.id})")
            line(report, f"Bot top role: {bot_member.top_role.name} position={bot_member.top_role.position}")

            target_role = discord.utils.get(guild.roles, name=DELETE_ROLE_NAME)
            if target_role is None:
                line(report, f"Delete role: {DELETE_ROLE_NAME} not found, already removed.")
            elif target_role >= bot_member.top_role:
                line(
                    report,
                    f"Delete role blocked: {target_role.name} position={target_role.position} "
                    f"is not below bot top role position={bot_member.top_role.position}.",
                )
            else:
                await target_role.delete(reason="Role policy update: remove แม่ทัพ")
                line(report, f"Deleted role: {DELETE_ROLE_NAME}")

            edited = 0
            skipped = 0
            blocked = 0
            for role in guild.roles:
                if role.is_default():
                    allow_invite = False
                else:
                    allow_invite = role.name in INVITE_ALLOWED_ROLE_NAMES

                if role.managed:
                    skipped += 1
                    line(report, f"Skipped managed role: {role.name}")
                    continue

                if not role.is_default() and role >= bot_member.top_role:
                    blocked += 1
                    line(report, f"Blocked by hierarchy: {role.name} position={role.position}")
                    continue

                permissions = role.permissions
                if permissions.create_instant_invite == allow_invite:
                    continue

                permissions.create_instant_invite = allow_invite
                await role.edit(
                    permissions=permissions,
                    reason="Role policy update: restrict invite creation",
                )
                edited += 1
                state = "allowed" if allow_invite else "denied"
                line(report, f"Invite permission {state}: {role.name}")

            line(report, f"Done. Edited={edited}, skipped_managed={skipped}, blocked_hierarchy={blocked}")
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
