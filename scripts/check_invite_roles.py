import asyncio
import sys

import discord

from app import read_token_from_credential_manager


GUILD_ID = 1422980759433777194

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


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

        print(f"Guild: {guild.name} ({guild.id})")
        print("Roles with Create Invite permission:")
        roles = [role for role in guild.roles if role.permissions.create_instant_invite]
        roles.sort(key=lambda role: role.position, reverse=True)
        if not roles:
            print("- none")
        for role in roles:
            print(f"- {role.name} | position={role.position} | managed={role.managed} | members={len(role.members)}")
        await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
