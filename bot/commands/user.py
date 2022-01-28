import discord

from discord.ext import commands
from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig
from util import send_msg


class User(commands.Cog):
    def __init__(self, client: discord.user, state: ClientState, guild_config: RoleConfig):
        # Meta Information for the help command
        self.description = "All commands accessible by all users."

        self.state = state
        self.client = client
        self.guildConfig = guild_config

    @commands.command(name="slot",
                      usage="[Number]",
                      help="Registers the caller for the event in the desired slot, which is given by its number. "
                           "Leading zeros don't have to be given.",
                      brief="Register for the event.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def slot(self, ctx, slot_number: int):
        channel = ctx.message.channel
        author = ctx.message.author

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)

        game = channel.name.split("-")[-1].strip()

        if not self.guildConfig.has_game_role(author, game):
            await self.guildConfig.set_user_newbie(author, game)
            if not self.guildConfig.is_soft_locked(channel.guild, game):

                await send_msg(ctx, "You are missing a role to join this event!")
                await ctx.message.delete()
                return

        slotlist.slot(slot_number, author.display_name)

        await slotlist.write()

        await author.send(f"You slotted yourself for the event **{channel.name}** by **{channel.guild.name}**.")

        if self.client.user != slotlist.author:
            await slotlist.author.send(f"{author.display_name} ({author}) "
                                       f"slotted himself for the event {channel.name} "
                                       f"for position #{slot_number} in the guild {channel.guild.name}.")

        await ctx.message.delete()

    @commands.command(name="unslot",
                      usage="",
                      help="Withdraws the caller from the event.",
                      brief="Withdraw from the event.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def unslot(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.author

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(author.display_name)
        await slotlist.write()

        await author.send(f"You have withdrawn yourself from the event **{channel.name}** by **{channel.guild.name}**.")

        if self.client.user != slotlist.author:
            await slotlist.author.send(f"{author.display_name} ({author}) "
                                       f"have withdrawn himself from the event {channel.name} "
                                       f"in the guild {channel.guild.name}.")

        await ctx.message.delete()
