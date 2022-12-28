from config.load_config import config
import discord
from discord.ext import commands
from utils import locale, checks
import logging

from backend import webui
import base64
import uuid
import random
import io

class LinkExpand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def save_image(self, image_data:bytes, image_filename:str):
        dir = config['GENERATED_IMAGE_OUTDIR']
        with open(f'{dir}/{image_filename}.jpg', 'wb') as f:
            f.write(image_data)
    
    @checks.is_allowed_guild()
    @checks.is_nsfw()
    @commands.command(name='link')
    async def link_expand(self, ctx: commands.Context, link: str):
        """link [link]"""

        self.logger.info(f'Start link command')
        if not config['USE_WEBUI']:
            self.logger.info(f'WebUI is not enabled')
            return
        user_locale = locale.get_user_locale(ctx.author.id)
        if(ctx.guild is None):
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command}')
        else:
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id})')
        try:
            if link.startswith('https://discord.com/channels/') or \
                link.startswith('https://discordapp.com/channels/') or \
                link.startswith('https://canary.discord.com/channels/') or \
                link.startswith('https://ptb.discord.com/channels/'):
                server_id, channel_id, message_id = link.split('/')[-3:]
                if server_id is None or channel_id is None or message_id is None:
                    return
                if not server_id.isdigit() or not channel_id.isdigit() or not message_id.isdigit():
                    return
                server = self.bot.get_guild(int(server_id))
                if server is None:
                    return
                channel = server.get_channel(int(channel_id))
                if channel is None:
                    return
                linked_message = await channel.fetch_message(int(message_id))
                if ctx.author != self.bot.user and linked_message.content != "":
                    self.logger.info(f"Prompt from {ctx.author}: {linked_message.content}")
                    message_text = random.choice(user_locale['MESSAGE']['LINK']) + '\n' + linked_message.content
                    await ctx.reply(message_text)
                    response = await webui.generate_image(
                        linked_message.content, (512, 768), config['DEFAULT_NEGATIVE_PROMPT'], steps=config['STEPS'][2], scale=config['SCALE'][2])
                    b64_image = response["images"][0]
                    image_data = base64.b64decode(b64_image)
                    image_filename = str(uuid.uuid4())
                    file = discord.File(io.BytesIO(image_data), filename=f'{image_filename}.jpg')
                    sent_message = await ctx.reply(file=file)
                    await sent_message.add_reaction(config['REACTION']["DELETE"])
                    self.save_image(image_data, image_filename)
                    self.logger.info(f'Saved image: {image_filename}.jpg')
        except Exception as e:
            self.logger.error(e)

async def setup(bot):
    await bot.add_cog(LinkExpand(bot))