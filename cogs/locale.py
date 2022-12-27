from discord.ext import commands
from utils import locale

class Locale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='locale')
    async def locale(self, ctx: commands.Context, locale_name: str=None):
        """locale [locale_name]"""
        if locale_name is None:
            locale_message = locale.get_bot_locale()['MESSAGE']['GET_LOCALE']
            await ctx.reply(locale_message)
            return
        if locale_name in locale.get_all_locale_names():
            locale.set_bot_locale(locale_name)
            await ctx.reply(locale.get_bot_locale()['MESSAGE']['SET_LOCALE'])
        else:
            await ctx.reply(locale.get_bot_locale()['ERROR']['INVALID_LOCALE'])
    
    @commands.command(name='locales')
    async def get_locales(self, ctx: commands.Context):
        """get locales"""
        locale_message = locale.get_bot_locale()['MESSAGE']['GET_LOCALES'] + '\n'
        for locale_name in locale.get_all_locale_names():
            locale_message += f'- {locale_name}\n'
        await ctx.reply(locale_message)

async def setup(bot):
    await bot.add_cog(Locale(bot))