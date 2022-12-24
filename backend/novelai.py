from .boilerplate import API
from novelai_api.ImagePreset import ImageModel, ImagePreset, ImageResolution, UCPreset

class NovelAI:
    def __init__(self) -> None:
        pass
    async def generate(self, prompt: str, resolution: tuple, negative_prompt: str, is_safe:bool=True) -> bytes:
        async with API() as api_handler:
            api = api_handler.api
            preset = ImagePreset()
            preset["n_samples"] = 1
            preset["resolution"] = resolution
            preset["quality_toggle"] = True
            preset["uc"] = negative_prompt
            images = []
            model = ImageModel.Anime_Curated if is_safe else ImageModel.Anime_Full
            async for img in api.high_level.generate_image(prompt, model, preset):
                images.append(img)
            image = images[0]
            return image
