import aiohttp
from typing import Dict, Any, List
from config import USER_AGENTS, PROXY_LIST
from utils.proxy_rotator import get_random_proxy
from utils.user_agent import get_random_ua
import asyncio


async def search_username(username: str) -> Dict[str, Any]:
    platforms = [
        ("github", "https://github.com/{}"),
        ("twitter", "https://twitter.com/{}"),
        ("instagram", "https://instagram.com/{}"),
        ("reddit", "https://reddit.com/user/{}"),
        ("tiktok", "https://tiktok.com/@{}"),
        ("youtube", "https://youtube.com/@{}"),
        ("twitch", "https://twitch.tv/{}"),
        ("steam", "https://steamcommunity.com/id/{}"),
        ("pinterest", "https://pinterest.com/{}"),
        ("tumblr", "https://{}.tumblr.com"),
        ("telegram", "https://t.me/{}"),
        ("vkontakte", "https://vk.com/{}"),
        ("facebook", "https://facebook.com/{}"),
        ("linkedin", "https://linkedin.com/in/{}"),
        ("snapchat", "https://snapchat.com/add/{}"),
        ("discord", "https://discord.com/users/{}"),
        ("roblox", "https://roblox.com/user.aspx?username={}"),
        ("chess", "https://chess.com/member/{}"),
        ("pastebin", "https://pastebin.com/u/{}"),
        ("hackernews", "https://news.ycombinator.com/user?id={}"),
        ("keybase", "https://keybase.io/{}"),
        ("aboutme", "https://about.me/{}"),
        ("flickr", "https://flickr.com/people/{}"),
        ("dribbble", "https://dribbble.com/{}"),
        ("behance", "https://behance.net/{}"),
        ("medium", "https://medium.com/@{}"),
        ("devto", "https://dev.to/{}"),
        ("gitlab", "https://gitlab.com/{}"),
        ("bitbucket", "https://bitbucket.org/{}"),
        ("habr", "https://habr.com/ru/users/{}"),
        ("pikabu", "https://pikabu.ru/@{}"),
        ("drive2", "https://drive2.ru/users/{}"),
        ("spark", "https://spark.ru/user/{}"),
        ("fl", "https://fl.ru/users/{}"),
        ("kwork", "https://kwork.ru/user/{}")
    ]

    tasks = [check_platform(name, url_template.format(username), username)
             for name, url_template in platforms]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    found = []
    for res in results:
        if isinstance(res, Exception) or not res:
            continue
        if res.get("exists"):
            found.append(res)

    return {
        "source": "username_search",
        "query": username,
        "total_checked": len(platforms),
        "found_count": len(found),
        "results": found
    }


async def check_platform(name: str, url: str, username: str) -> Dict[str, Any]:
    try:
        proxy = get_random_proxy()
        ua = get_random_ua()

        async with aiohttp.ClientSession() as session:
            async with session.head(url, headers={"User-Agent": ua},
                                    proxy=proxy, allow_redirects=False, timeout=3) as resp:
                if resp.status == 200:
                    return {
                        "platform": name,
                        "exists": True,
                        "url": url,
                        "status": resp.status
                    }
                elif resp.status in [301, 302, 303]:
                    location = resp.headers.get("Location", "")
                    if "login" not in location and "signup" not in location:
                        return {
                            "platform": name,
                            "exists": True,
                            "url": url,
                            "redirect": location
                        }
                return {"platform": name, "exists": False, "status": resp.status}
    except asyncio.TimeoutError:
        return {"platform": name, "exists": False, "error": "timeout"}
    except Exception as e:
        return {"platform": name, "exists": False, "error": str(e)}