import os
import datetime
import logging

import discord
from discord.ext import commands
from discord.ext.commands import errors as derrors


async def send_msg(ctx: discord.ApplicationContext, error_msg: str) -> None:
    """
    Sends an error msg to the author and in the channel of the message
    :param ctx: Message to reply to
    :param error_msg: Error message
    :return:
    """
    await ctx.respond(f'{ctx.message.author.mention} {error_msg}', delete_after=5)


def init_logger(path: str) -> logging.Logger:
    """
    Init the custom logger and the general discord logging
    :param path: Path to the log dir
    :return:
    """
    today = datetime.date.today()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename=os.path.join(path, 'logs', f'{today}.log'), encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
    logger.addHandler(handler)

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_handler = logging.FileHandler(filename=os.path.join(path, 'logs', 'discord.log'), encoding='utf-8', mode='w')
    discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discord_logger.addHandler(discord_handler)

    return logger


class CustomParentException(Exception):
    def __init__(self):
        self.message = ""
        self.author_message = ""
        self.custom = True
        super().__init__()

    def __str__(self):
        return self.message


class Util(commands.Cog):
    def __init__(self, client, cfg, logger):
        self.logger = logger
        self.client = client
        self.cfg = cfg

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(str(error), delete_after=error.retry_after + 1)
        elif isinstance(error, derrors.CommandNotFound):
            await ctx.respond("Command not found! Check **!help** for all commands", delete_after=5)
        elif isinstance(error, derrors.MissingRequiredArgument):
            await ctx.respond(f"Arguments are missing! Check **!help {ctx.command}** for correct usage", delete_after=5)
        elif isinstance(error, derrors.BadBoolArgument):
            await ctx.respond(f"The given boolean is argument is faulty! Check **!help {ctx.command}** for correct "
                                f"usage ", delete_after=5)

        elif isinstance(error.original, discord.errors.Forbidden):
            await ctx.respond("The Bot is missing a permission. Please contact your local admin.", delete_after=5)
        elif isinstance(error.original, derrors.MissingRole):
            await ctx.respond(f"You are missing a role to execute this command!", delete_after=5)

        elif hasattr(error, 'original') and hasattr(error.original, 'custom'):
            await ctx.respond(error.original.message, delete_after=5)

            if error.original.author_message != "":
                await ctx.author.send(error.original.author_message, delete_after=5)
        else:
            await ctx.respond("Unexpected error. Please contact your local admin.", delete_after=5)

        log = "User: " + str(ctx.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.command).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error

    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game(name=f"Use: /help")
        await self.client.change_presence(activity=game)

        self.logger.info("Server Started")
        print("Server started.")