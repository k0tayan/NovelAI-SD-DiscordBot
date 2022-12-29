from discord.ext import commands
from utils import locale
from utils.logger import MyLogger


class Locale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='locale')
    @MyLogger.log_command
    async def locale(self, ctx: commands.Context, locale_name: str = None):
        """locale [locale_name]"""
        user_locale = locale.get_user_locale(ctx.author.id)
        if locale_name is None:
            locale_message = user_locale['MESSAGE']['GET_LOCALE']
            await ctx.reply(locale_message)
            return
        if locale_name in locale.get_all_locale_names():
            locale.set_user_locale(ctx.author.id, locale_name)
            user_locale = locale.get_user_locale(ctx.author.id)
            await ctx.reply(user_locale['MESSAGE']['SET_LOCALE'])
        else:
            await ctx.reply(user_locale['ERROR']['INVALID_LOCALE'])

    @commands.command(name='locales')
    @MyLogger.log_command
    async def get_locales(self, ctx: commands.Context):
        """get locales"""
        user_locale = locale.get_user_locale(ctx.author.id)
        locale_message = user_locale['MESSAGE']['GET_LOCALES'] + '\n'
        for locale_name in locale.get_all_locale_names():
            locale_message += f'- {locale_name}\n'
        await ctx.reply(locale_message)


async def setup(bot):
    await bot.add_cog(Locale(bot))
