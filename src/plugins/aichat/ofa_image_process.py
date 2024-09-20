import contextlib
import io
import ssl

import aiohttp
import torch
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from nonebot import logger
from PIL import Image


class ImageCaptioningPipeline:
    _model = None

    @classmethod
    def load_model(cls, model_path):
        device = torch.device("cpu")
        logger.info("[ofa_image_process]: 加载模型中...")
        logger.info(f"[ofa_image_process]: 使用设备: {device}")
        cls._model = pipeline(Tasks.image_captioning, model=model_path)
        logger.info("[ofa_image_process]: 模型加载完成！")

    @classmethod
    def unload_model(cls):
        if cls._model is not None:
            del cls._model
            cls._model = None
            torch.cuda.empty_cache()  # 释放显存
            logger.info("[ofa_image_process]: 模型已卸载，显存已释放！")
        else:
            logger.info("[ofa_image_process]: 没有模型需要卸载。")

    async def generate_caption(self, url):
        if self._model is None:
            raise NotImplementedError("模型未加载！")
        with contextlib.suppress(Exception):
            url = url.replace("&amp;", "&")
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=ssl_context) as response:
                image_bytes = await response.read()
                image = Image.open(io.BytesIO(image_bytes))
        result = self._model(image)
        caption: list[str] = result[OutputKeys.CAPTION]  # type: ignore
        logger.info(f"[ofa_image_process]: 生成的图片描述: {caption}")
        return caption[0]
