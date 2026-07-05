import asyncio
import json
import sys
from pathlib import Path

import aiohttp
import discord

from app import read_saved_token


GUILD_ID = 1422980759433777194
REPORT_PATH = Path(__file__).resolve().parent / "invite_onboarding_report.txt"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def line(report, message):
    print(message)
    report.append(message)


async def discord_get(token, path):
    url = f"https://discord.com/api/v10{path}"
    headers = {"Authorization": f"Bot {token}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            text = await response.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return response.status, data


async def main():
    token = read_saved_token()
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

            line(report, f"Guild: {guild.name} ({guild.id})")
            line(report, f"Features: {', '.join(sorted(guild.features)) if guild.features else '-'}")
            line(report, f"Rules channel: {guild.rules_channel.name if guild.rules_channel else '-'}")
            line(report, f"Public updates channel: {guild.public_updates_channel.name if guild.public_updates_channel else '-'}")
            line(report, "")

            line(report, "Invite permission roles:")
            roles = [role for role in guild.roles if role.permissions.create_instant_invite]
            roles.sort(key=lambda role: role.position, reverse=True)
            if not roles:
                line(report, "- none")
            for role in roles:
                line(report, f"- {role.name} | position={role.position} | managed={role.managed}")
            line(report, "")

            onboarding_status, onboarding = await discord_get(token, f"/guilds/{guild.id}/onboarding")
            line(report, f"Onboarding endpoint status: {onboarding_status}")
            if isinstance(onboarding, dict):
                line(report, f"Onboarding enabled: {onboarding.get('enabled')}")
                prompts = onboarding.get("prompts") or []
                line(report, f"Onboarding prompt count: {len(prompts)}")
                for prompt in prompts:
                    title = prompt.get("title") or prompt.get("id")
                    required = prompt.get("required")
                    in_onboarding = prompt.get("in_onboarding")
                    options = prompt.get("options") or []
                    line(
                        report,
                        f"- Prompt: {title} | required={required} | in_onboarding={in_onboarding} | options={len(options)}",
                    )
            else:
                line(report, f"Onboarding response: {onboarding}")
            line(report, "")

            verification_status, verification = await discord_get(token, f"/guilds/{guild.id}/member-verification")
            line(report, f"Member verification endpoint status: {verification_status}")
            if isinstance(verification, dict):
                form_fields = verification.get("form_fields") or []
                line(report, f"Verification form field count: {len(form_fields)}")
                for field in form_fields:
                    label = field.get("label") or field.get("field_type")
                    required = field.get("required")
                    line(report, f"- Field: {label} | required={required}")
            else:
                line(report, f"Verification response: {verification}")
        finally:
            REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
