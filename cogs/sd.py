from config.load_config import config
import discord
from discord.ext import commands
from utils import locale, checks
from utils.logger import MyLogger

from utils.prompt import parse_prompt, translate_prompt, StableDiffusionPrompt
from backend import webui
import base64
import random
import io
import json
import os


class StableDiffusionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        elemental_code_jsons = [config['ELEMENTAL_CODE_JSON_PATH'] + '/' + i for i in os.listdir(config['ELEMENTAL_CODE_JSON_PATH'])]
        self.elemental_code = []
        for json_path in elemental_code_jsons:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                self.elemental_code.append(json_data)

        self.logger = MyLogger(__name__)

    @checks.is_allowed_guild()
    @checks.is_nsfw()
    @commands.command(name='sd')
    async def generate_with_sd(self, ctx: commands.Context, *args):
        """sd [positive_prompt] -u [negative_prompt] -s [steps] -c [scale] -w [width] -h [height] -b [batch_size] -t(translate prompt)"""

        self.logger.info('Start sd command')
        if not config['USE_WEBUI']:
            self.logger.info('WebUI is not enabled')
            return
        user_locale = locale.get_user_locale(ctx.author.id)
        if ctx.guild is None:
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command}')
        else:
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id})')
        try:
            try:
                prompt: StableDiffusionPrompt = parse_prompt(list(args))
            except ValueError as e:
                error = e.args[0]
                error_message = error['message']
                if error_message == 'INVALID_OPTION':
                    await ctx.reply(user_locale['ERROR']['INVALID_OPTION'].replace('<option>', error['args']['option']))
                elif error_message == 'INVALID_OPTION_RANGE':
                    await ctx.reply(
                        user_locale['ERROR']['INVALID_OPTION_RANGE'].
                        replace('<option>', error['args']['option']).
                        replace('<min>', str(error['args']['min'])).
                        replace('<max>', str(error['args']['max']))
                    )
                elif error_message == 'WIDTH_NOT_MULTIPLE_OF_64':
                    await ctx.reply(user_locale['ERROR']['WIDTH_NOT_MULTIPLE_OF_64'])
                elif error_message == 'HEIGHT_NOT_MULTIPLE_OF_64':
                    await ctx.reply(user_locale['ERROR']['HEIGHT_NOT_MULTIPLE_OF_64'])
                elif error_message == 'INVALID_NEGATIVE_PROMPT':
                    await ctx.reply(user_locale['ERROR']['INVALID_NEGATIVE_PROMPT'])
                else:
                    await ctx.reply(error_message)
                return
            self.logger.info(prompt)
            reply_message = random.choice(user_locale['MESSAGE']['RESPONSE'])
            if prompt.steps != config['STEPS'][2]:
                reply_message += '\n' + random.choice(user_locale['MESSAGE']['STEPS']).replace('<0>', str(prompt.steps))
            if prompt.translate:
                reply_message += '\n' + user_locale['MESSAGE']['TRANSLATE']
            if any(['{' in arg or '}' in arg for arg in args]):
                reply_message += '\n' + random.choice(user_locale['MESSAGE']['BRACKET'])
            if prompt.batch_size == 1:
                await ctx.reply(reply_message)
                response = await webui.generate_image(
                    prompt=prompt.prompt,
                    resolution=(prompt.width, prompt.height),
                    negative_prompt=config['DEFAULT_NEGATIVE_PROMPT']+prompt.prompt,
                    steps=prompt.steps,
                    scale=prompt.scale,
                )
                image_data = base64.b64decode(response['images'][0])
                image_filename = self.logger.save_image(image_data)
                file = discord.File(io.BytesIO(image_data), filename=f'{image_filename}.jpg')
                message = await ctx.reply(file=file)
                await message.add_reaction(config['REACTION']['DELETE'])
            else:
                if type(ctx.message.channel) is discord.channel.TextChannel:
                    thread = await ctx.message.create_thread(name=positive_prompt[:100])
                    await thread.send(reply_message)
                else:
                    await ctx.reply(reply_message)
                response = await webui.generate_image(
                    prompt=positive_prompt,
                    resolution=(prompt.width, prompt.height),
                    negative_prompt=config['DEFAULT_NEGATIVE_PROMPT']+negative_prompt,
                    steps=prompt.steps,
                    scale=prompt.scale,
                    batch_size=prompt.batch_size,
                )
                for b64_image in response['images']:
                    image_data = base64.b64decode(b64_image)
                    image_filename = self.logger.save_image(image_data)
                    file = discord.File(io.BytesIO(image_data), filename=f'{image_filename}.jpg')
                    if type(ctx.message.channel) is discord.channel.TextChannel:
                        message = await thread.send(file=file)
                        await message.add_reaction(config['REACTION']["DELETE"])
                    else:
                        message = await ctx.reply(file=file)
                        await message.add_reaction(config['REACTION']["DELETE"])
        except Exception as e:
            self.logger.error(e)
        self.logger.info('End sd command')

    @checks.is_allowed_guild()
    @checks.is_nsfw()
    @commands.command(name='ele')
    async def generate_with_ele(self, ctx: commands.Context):
        """Generate an image with an elemental code prompt."""

        self.logger.info('Start ele command')
        if not config['USE_WEBUI']:
            self.logger.info('WebUI is not enabled')
            return
        user_locale = locale.get_user_locale(ctx.author.id)
        try:
            element = random.choice(self.elemental_code)
            positive_prompt = element['prompt'].replace('{', '(').replace('}', ')')
            negative_prompt = element['negative_prompt'].replace('{', '(').replace('}', ')')
            reply_message = random.choice(user_locale['MESSAGE']['ELEMENTAL_CODE'])
            reply_message += '\n sd ' + positive_prompt + '\n -u ' + negative_prompt
            await ctx.reply(reply_message)
            if 'width' not in element:
                element['width'] = config['WIDTH'][2]
            if 'height' not in element:
                element['height'] = config['HEIGHT'][2]
            if 'steps' not in element:
                element['steps'] = config['STEPS'][2]
            if 'cfg_scale' not in element:
                element['cfg_scale'] = config['SCALE'][2]
            response = await webui.generate_image(
                prompt=positive_prompt,
                resolution=(element['width'][0], element['height'][0]),
                negative_prompt=negative_prompt,
                steps=element['steps'][0],
                scale=element['cfg_scale'][0],
                batch_size=1
            )
            image_data = base64.b64decode(response['images'][0])
            image_filename = self.logger.save_image(image_data)
            file = discord.File(io.BytesIO(image_data), filename=f'{image_filename}.jpg')
            message = await ctx.reply(file=file)
            await message.add_reaction(config['REACTION']['DELETE'])
        except Exception as e:
            self.logger.error(e)


async def setup(bot):
    await bot.add_cog(StableDiffusionCog(bot))
