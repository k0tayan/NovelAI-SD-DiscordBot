from config.load_config import config
import aiohttp


async def generate_image(
    prompt: str,
    resolution: tuple,
    negative_prompt: str,
    seed: int = -1,
    steps: int = 20,
    scale: int = 12,
    batch_size: int = 1,
) -> dict:
    """Generate an image from a prompt."""
    uri = config["WEBUI_URI"] + "/sdapi/v1"
    endpoint = "/txt2img"
    payload = {
        "prompt": prompt,
        "seed": seed,
        "steps": steps,
        "cfg_scale": scale,
        "width": resolution[0],
        "height": resolution[1],
        "negative_prompt": negative_prompt,
        "sampler_name": "Euler a",
        "batch_size": batch_size,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(uri + endpoint, json=payload) as resp:
            return await resp.json()
