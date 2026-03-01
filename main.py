import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, REDIS_URL, PG_DSN, USE_REDIS, USE_POSTGRES
from handlers import search_router
from middlewares import ThrottlingMiddleware
from database import init_db, close_db
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

bot: Bot = None
dp: Dispatcher = None
rate_limiter = None
shutdown_event = asyncio.Event()


async def init_rate_limiter():
    from utils.rate_limiter import RateLimiter
    limiter = RateLimiter(REDIS_URL)
    await limiter.init()
    return limiter


async def on_startup():
    global rate_limiter

    logger.info("Starting bot initialization...")
    logger.info(f"Configuration: USE_REDIS={USE_REDIS}, USE_POSTGRES={USE_POSTGRES}")

    try:
        await init_db(PG_DSN, REDIS_URL)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.info("Continuing with in-memory storage only")

    try:
        rate_limiter = await init_rate_limiter()
        logger.info("RateLimiter initialized")
    except Exception as e:
        logger.error(f"RateLimiter initialization failed: {e}")
        from types import SimpleNamespace
        rate_limiter = SimpleNamespace(
            check=lambda user_id: True,
            get_remaining=lambda user_id: 999,
            close=lambda: None
        )

    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="phone", description="Поиск по номеру телефона"),
        BotCommand(command="email", description="Поиск по email"),
        BotCommand(command="username", description="Поиск по username"),
        BotCommand(command="ip", description="Поиск по IP"),
        BotCommand(command="history", description="История поиска"),
        BotCommand(command="help", description="Помощь")
    ]
    await bot.set_my_commands(commands)

    logger.info("Bot started successfully")


async def on_shutdown():
    logger.info("Shutting down bot...")

    if rate_limiter and hasattr(rate_limiter, 'close'):
        await rate_limiter.close()

    await close_db()

    if bot:
        await bot.session.close()

    logger.info("Bot stopped")
    shutdown_event.set()


async def main():
    global bot, dp

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logger.error("BOT_TOKEN not set in config.py")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(search_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)