import asyncio
import json
import sys
from pathlib import Path

import discord

from app import read_token_from_credential_manager


APP_DIR = Path(__file__).resolve().parent
GUILD_ID = 1422980759433777194
ROLE_STRUCTURE_PATH = APP_DIR / "role_structure.json"
REPORT_PATH = APP_DIR / "role_channel_access_report.md"
JSON_PATH = APP_DIR / "role_channel_access_report.json"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


JOB_ROLE_NAMES = {
    "สุ่ยเมื่ง-nightwaker",
    "เถี่ยยี-ironclad",
    "ซือเหอ-bloodstorm",
    "ซู่เวิ่น-celestune",
    "เสิ่นเซียง-sylph",
    "จิ่วหลิง-numina",
    "ยังไม่เลือกอาชีพ",
    "NARAKA",
}

MEMBER_ROLE_NAMES = {
    "Golden spatura",
    "ศิษย์สายตรง",
    "ศิษย์สายใน",
    "ศิษย์สายนอก",
    "ทั่วไป",
    "สมาชิกกิลด์ 1",
    "Server Booster",
}


def load_role_structure():
    if not ROLE_STRUCTURE_PATH.exists():
        return {
            "management_roles": [],
            "bot_accounts": [],
            "bot_roles": [],
        }
    return json.loads(ROLE_STRUCTURE_PATH.read_text(encoding="utf-8"))


def role_type(role, structure):
    if role.is_default():
        return "default"
    if role.managed:
        return "bot_account_or_managed"
    if role.name in structure.get("management_roles", []):
        return "management"
    if role.name in structure.get("bot_accounts", []):
        return "bot_account"
    if role.name in structure.get("bot_roles", []):
        return "bot_role"
    if role.name in MEMBER_ROLE_NAMES:
        return "member_hierarchy"
    if role.name in JOB_ROLE_NAMES:
        return "job_or_game_class"
    return "other"


def names(channels, limit=10):
    if not channels:
        return "-"
    visible = ", ".join(f"#{channel.name}" for channel in channels[:limit])
    if len(channels) > limit:
        visible += f", ... +{len(channels) - limit}"
    return visible


async def main():
    token = read_token_from_credential_manager()
    if not token:
        raise RuntimeError("No bot token found in Windows Credential Manager.")

    structure = load_role_structure()
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        guild = client.get_guild(GUILD_ID)
        if guild is None:
            print(f"ERROR: Bot cannot see guild {GUILD_ID}.")
            await client.close()
            return

        text_channels = list(guild.text_channels)
        voice_channels = list(guild.voice_channels)
        category_channels = list(guild.categories)
        roles = sorted(guild.roles, key=lambda item: item.position, reverse=True)

        records = []
        for role in roles:
            text_view = []
            text_send = []
            voice_view = []
            voice_connect = []
            voice_speak = []
            category_view = []

            for channel in text_channels:
                permissions = channel.permissions_for(role)
                if permissions.view_channel:
                    text_view.append(channel)
                if permissions.view_channel and permissions.send_messages:
                    text_send.append(channel)

            for channel in voice_channels:
                permissions = channel.permissions_for(role)
                if permissions.view_channel:
                    voice_view.append(channel)
                if permissions.view_channel and permissions.connect:
                    voice_connect.append(channel)
                if permissions.view_channel and permissions.connect and permissions.speak:
                    voice_speak.append(channel)

            for channel in category_channels:
                permissions = channel.permissions_for(role)
                if permissions.view_channel:
                    category_view.append(channel)

            records.append(
                {
                    "role": role.name,
                    "id": role.id,
                    "type": role_type(role, structure),
                    "position": role.position,
                    "managed": role.managed,
                    "members": len(role.members),
                    "text_view_count": len(text_view),
                    "text_send_count": len(text_send),
                    "voice_view_count": len(voice_view),
                    "voice_connect_count": len(voice_connect),
                    "voice_speak_count": len(voice_speak),
                    "category_view_count": len(category_view),
                    "text_view_sample": [channel.name for channel in text_view[:20]],
                    "text_send_sample": [channel.name for channel in text_send[:20]],
                    "voice_connect_sample": [channel.name for channel in voice_connect[:20]],
                    "voice_speak_sample": [channel.name for channel in voice_speak[:20]],
                    "text_view_channels": [channel.name for channel in text_view],
                    "text_send_channels": [channel.name for channel in text_send],
                    "voice_connect_channels": [channel.name for channel in voice_connect],
                    "voice_speak_channels": [channel.name for channel in voice_speak],
                }
            )

        grouped = {}
        for record in records:
            grouped.setdefault(record["type"], []).append(record)

        lines = [
            f"# Role Channel Access Report",
            "",
            f"Server: `{guild.name}`",
            f"Server ID: `{guild.id}`",
            f"Text channels: `{len(text_channels)}`",
            f"Voice channels: `{len(voice_channels)}`",
            f"Categories: `{len(category_channels)}`",
            "",
            "Counts are effective permissions for each role by itself, including channel overwrites.",
            "",
        ]

        order = [
            "management",
            "member_hierarchy",
            "job_or_game_class",
            "bot_role",
            "bot_account",
            "bot_account_or_managed",
            "other",
            "default",
        ]
        labels = {
            "management": "Role จัดการ",
            "member_hierarchy": "Role สมาชิก/ลำดับชั้น",
            "job_or_game_class": "Role อาชีพ/เกม",
            "bot_role": "Role บอท",
            "bot_account": "Bot account",
            "bot_account_or_managed": "Managed/Bot role",
            "other": "อื่น ๆ",
            "default": "@everyone",
        }

        for group in order:
            group_records = grouped.get(group, [])
            if not group_records:
                continue

            lines.extend(
                [
                    f"## {labels[group]}",
                    "",
                    "| Role | Text view | Text send | Voice view | Voice connect | Voice speak | Members |",
                    "|---|---:|---:|---:|---:|---:|---:|",
                ]
            )

            for record in group_records:
                lines.append(
                    f"| `{record['role']}` | {record['text_view_count']} | {record['text_send_count']} | "
                    f"{record['voice_view_count']} | {record['voice_connect_count']} | "
                    f"{record['voice_speak_count']} | {record['members']} |"
                )
            lines.append("")

        lines.extend(["## Samples", ""])
        for record in records:
            if record["type"] == "default":
                continue
            lines.extend(
                [
                    f"### {record['role']}",
                    "",
                    f"- Type: `{labels.get(record['type'], record['type'])}`",
                    f"- Text channels visible: {', '.join(record['text_view_sample']) if record['text_view_sample'] else '-'}",
                    f"- Text channels can send: {', '.join(record['text_send_sample']) if record['text_send_sample'] else '-'}",
                    f"- Voice channels can connect: {', '.join(record['voice_connect_sample']) if record['voice_connect_sample'] else '-'}",
                    f"- Voice channels can speak: {', '.join(record['voice_speak_sample']) if record['voice_speak_sample'] else '-'}",
                    "",
                ]
            )

        payload = {
            "guild": {"name": guild.name, "id": guild.id},
            "channel_counts": {
                "text": len(text_channels),
                "voice": len(voice_channels),
                "categories": len(category_channels),
            },
            "roles": records,
        }

        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"Wrote {REPORT_PATH.name}")
        print(f"Wrote {JSON_PATH.name}")
        print()
        for group in order:
            group_records = grouped.get(group, [])
            if group_records:
                print(f"{labels[group]}: {len(group_records)} role(s)")

        await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
