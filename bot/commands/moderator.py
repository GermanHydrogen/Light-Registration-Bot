import discord
from discord import slash_command, Option
from discord.ext import commands

from bot.commands.objects.guildconfig import RoleConfig, is_moderator
from bot.commands.objects.state import ClientState


class Moderator(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, guild_config: RoleConfig):
        # Meta Information for the help command
        self.description = "All commands accessible with the defined moderator role or admin permission."

        self.client = client
        self.state = state

        self.guildConfig = guild_config

    @slash_command()
    @is_moderator
    async def create(self, ctx):  # makes the slotlist editable for the bot
        """Creates an event in the channel. Needs a prev. msg witch begins with >Slotlist<"""
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, ctx.author, self.client.user, True)
        await slotlist.write(channel, False)

        await ctx.respond(f"The event **{channel.name}** was successfully created!", delete_after=10)

    @slash_command()
    @is_moderator
    async def force_slot(self, ctx, slot_number: Option(int, "Slot number"), user_name: Option(str, "Username of the user to slot")):
        """Registers a username for the given slot."""
        author = ctx.author
        channel = ctx.channel

        print(type(user_name))

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.slot(slot_number, user_name)
        await slotlist.write()

        await ctx.respond(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

    @slash_command()
    @is_moderator
    async def force_unslot(self, ctx, user_name: Option(str, "Username of the user to unslot")):
        """Withdraws a given user from the event."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(user_name)
        await slotlist.write()

        await ctx.respond(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

    @slash_command()
    @is_moderator
    async def edit_slot(self, ctx, number: Option(str, "Slot number"), description: Option(str, "Slot description")):
        """Edits the description of a slot."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.edit_slot(number, description)
        await slotlist.write()

        await ctx.respond(f'The description of slot #{number} was changed to {description}.', delete_after=5)

    @slash_command()
    @is_moderator
    async def del_slot(self, ctx, number: Option(str, "Slot number")):
        """Deletes a slot."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.remove_slot(number)
        await slotlist.write()

        await ctx.respond(f'The slot #{number} was successfully removed.', delete_after=5)

    @slash_command()
    @is_moderator
    async def add_slot(self, ctx, number: Option(str, "Slot number"), group: Option(str, "Group title or index"), description: Option(str, "Slot description")):
        """Adds a new slot to a slot-group."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.new_slot(number, group, description)
        await slotlist.write()

        await ctx.respond(f'The slot #{number} {description} was successfully created.', delete_after=5)

    @slash_command()
    @is_moderator
    async def add_group(self, ctx, index: Option(int, "Group index"), description: Option(str, "Group description")):
        """Adds a group."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.new_group(index, description)
        await slotlist.write()

        await ctx.respond(f'Added group {description} successfully.', delete_after=5)

    @slash_command()
    @is_moderator
    async def edit_group(self, ctx, description: Option(str, "Old group description"), new_description: Option(str, "New group description")):
        """Edits a group."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        new_description = new_description.replace(r"\n", "\n")
        slotlist.edit_group(description, new_description)
        await slotlist.write()

        await ctx.respond(f'The group {description} was changed to {new_description}.', delete_after=5)

    @slash_command()
    @is_moderator
    async def del_group(self, ctx, description: Option(str, "Group description")):
        """Deletes a group."""
        author = ctx.author
        channel = ctx.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.remove_group(description)
        await slotlist.write()

        await ctx.respond(f'The group {description} was successfully deleted.', delete_after=5)
