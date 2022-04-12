import discord
from discord.ext import commands
from discord import slash_command, Option
from discord.types.role import Role

from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig, is_administrator


class Admin(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, guild_config: RoleConfig):
        # Meta Information for the help command
        self.description = "All commands accessible with the defined admin role or admin permission."

        self.client = client
        self.state = state

        self.guildConfig = guild_config

    @slash_command()
    @is_administrator
    async def set_moderator_role(self, ctx, role: Option(Role, "Role", default=None)):
        """Defines the role, which has access to the moderator commands."""
        guild = ctx.guild

        self.guildConfig.set_moderator_role(self.client, guild, role)

        if role is None:
            await ctx.respond(f"Successfully reset the moderator role.", delete_after=5)
        else:
            await ctx.respond(f"Successfully set {role.name} as the moderator role.", delete_after=5)

    @slash_command()
    @is_administrator
    async def set_admin_role(self, ctx, *, role: Option(Role, "Role", default=None)):
        """Defines the role, which has access to the admin commands."""
        guild = ctx.guild

        self.guildConfig.set_admin_role(self.client, guild, role)

        if role is None:
            await ctx.respond(f"Successfully reset the admin role.", delete_after=5)
        else:
            await ctx.respond(f"Successfully set {role.name} as the admin role.", delete_after=5)

    @slash_command()
    @is_administrator
    async def set_type_config(self, ctx, game_name: str, required_role: Option(Role, "Role"), newbie_role: Option(Role, "Role", default=None), soft=False):
        """Sets a event type config"""
        self.guildConfig.set_game(self.client, ctx.guild, game_name.lower(), required_role, newbie_role, bool(soft))

        await ctx.respond(f"The game {game_name} was successfully added to the config.", delete_after=5)

    @slash_command()
    @is_administrator
    async def view_config(self, ctx):
        """Displays the bot config of this guild."""
        await ctx.respond(self.guildConfig.print_config(ctx.guild))