from config.load_config import config
from discord.ext import commands
from utils import locale


def bypass_admin(func):
    def predicate(ctx):
        if ctx.author.id in config['ADMIN_IDS']:
            return True
        return func(ctx)
    return predicate


def is_allowed_guild():
    @bypass_admin
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.reply(locale.get_bot_locale()['ERROR']['SERVER_ONLY'])
            return False
        if ctx.guild.id in config['ALLOWED_GUILD_IDS']:
            return True
        await ctx.reply(locale.get_bot_locale()['ERROR']['UNAUTHORIZED_SERVER'])
        return False
    return commands.check(predicate)


def is_nsfw():
    @bypass_admin
    async def predicate(ctx):
        if ctx.guild is not None and ctx.channel.is_nsfw():
            return True
        await ctx.reply(locale.get_bot_locale()['ERROR']['NSFW_ONLY'])
        return False
    return commands.check(predicate)
