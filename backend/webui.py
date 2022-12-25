from io import BytesIO
import aiohttp

class WebUI:
    def __init__(self, uri:str, api_version: str) -> None:
        self.uri = f"{uri}/sdapi/{api_version}"

    async def generate_image(self, prompt: str, resolution: tuple, negative_prompt: str, seed:int = -1, steps:int = 20, scale:int = 12) -> dict:
        """Generate an image from a prompt."""
        endpoint = '/txt2img'
        payload = {
            "prompt": prompt,
            "seed": seed,
            "steps": steps,
            "cfg_scale": scale,
            "width": resolution[0],
            "height": resolution[1],
            "negative_prompt": negative_prompt,
            "sampler_name": "Euler a",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.uri + endpoint, json=payload) as resp:
                return await resp.json()