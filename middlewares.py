from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from utils.rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        if await self.rate_limiter.check(user_id):
            return await handler(event, data)
        else:
            await event.answer("⏳ Слишком много запросов. Подождите минуту.")
            return

class ProxyRotationMiddleware(BaseMiddleware):
    def __init__(self, proxy_list: list):
        self.proxy_list = proxy_list
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        return await handler(event, data)