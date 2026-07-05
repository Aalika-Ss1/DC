import asyncio
import sys

import discord

from app import read_token_from_credential_manager


GUILD_ID = 1422980759433777194
ROLE_NAMES = {
    "ประมุขน้อย (ตัวแม่)",
    "รองประมุข (ตัวลูก)",
    "เลขานุการสำนัก",
    "ภูตสำนัก",
    "สายลับ",
    "ทั่วไป",
    "ศิษย์สายนอก",
    "ศิษย์สายใน",
    "ศิษย์สายตรง",
    "Golden spatura",
}

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def overwrite_value(overwrite, name):
    pair = getattr(overwrite, name)
    return "allow" if pair is True else "deny" if pair is False else "inherit"


async def main():
    token = read_token_from_credential_manager()
    if not token:
        raise RuntimeError("No bot token found in Windows Credential Manager.")

    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        guild = client.get_guild(GUILD_ID)
        if guild is None:
            print(f"ERROR: Bot cannot see guild {GUILD_ID}.")
            await client.close()
            return

        roles = {role.id: role for role in guild.roles if role.name in ROLE_NAMES}
        print(f"Guild: {guild.name} ({guild.id})")
        print("Checked channel overwrites for selected roles.")
        print()

        findings = []
        for channel in guild.channels:
            for target, overwrite in channel.overwrites.items():
                if not isinstance(target, discord.Role) or target.id not in roles:
                    continue

                values = {
                    "create_invite": overwrite_value(overwrite, "create_instant_invite"),
                    "view_channel": overwrite_value(overwrite, "view_channel"),
                    "send_messages": overwrite_value(overwrite, "send_messages"),
                    "connect": overwrite_value(overwrite, "connect"),
                    "speak": overwrite_value(overwrite, "speak"),
                }

                if any(value != "inherit" for value in values.values()):
                    findings.append((channel, target, values))

        if not findings:
            print("No explicit channel overwrites found for selected roles.")
        else:
            for channel, role, values in findings:
                print(f"- #{channel.name} [{channel.type}] role={role.name}")
                print(
                    "  "
                    + ", ".join(f"{key}={value}" for key, value in values.items())
                )

        await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
