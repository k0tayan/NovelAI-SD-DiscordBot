import logging
import uuid

from discord.ext import commands

from config.load_config import config


class MyLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s : %(levelname)s : %(name)s : %(message)s"
        )
        handler.setFormatter(formatter)
        self.addHandler(handler)
        self.propagate = False

    def save_image(self, image_data: bytes) -> str:
        dir = config["GENERATED_IMAGE_OUTDIR"]
        image_filename = str(uuid.uuid4())
        with open(f"{dir}/{image_filename}.jpg", "wb") as f:
            f.write(image_data)
        self.info(f"Saved image: {image_filename}.jpg")
        return image_filename

    @classmethod
    def log_command(cls, func):
        async def decorator(cls, *args, **kwargs):
            ctx: commands.Context = args[0]
            content = ctx.message.content.split(" ")
            command_name = content[0]
            command_args = content[1:]
            cls.logger.info(f"Command {command_name} start")
            cls.logger.info(f"Args: {command_args}")
            if ctx.guild is None:
                cls.logger.info(f"{ctx.author}({ctx.author.id}) {ctx.command}")
            else:
                cls.logger.info(
                    f"{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id})"
                )
            try:
                result = await func(cls, *args, **kwargs)
            except Exception as e:
                cls.logger.error(e)
            cls.logger.info(f"Command {command_name} end")
            return result

        return decorator
