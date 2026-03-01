import asyncio
import aiohttp
from typing import Dict, Any, List
from config import USER_AGENTS, PROXY_LIST, API_KEYS
from utils.proxy_rotator import get_random_proxy
from utils.user_agent import get_random_ua
import hashlib
import re


async def search_email(email: str) -> Dict[str, Any]:

    results = await asyncio.gather(
        search_email_gravatar(email),
        search_email_haveibeenpwned(email),
        search_email_emailrep(email),
        search_email_abstractapi(email),
        search_email_google(email),
        search_email_yandex(email),
        search_email_github(email),
        search_email_leakcheck(email),
        return_exceptions=True
    )

    combined = {
        "source": "email_search",
        "query": email,
        "results": [],
        "summary": {
            "total_sources": 8,
            "successful": 0,
            "gravatar": False,
            "breaches": 0,
            "reputation": None
        }
    }

    for res in results:
        if isinstance(res, Exception):
            print(f"Error in email search: {res}")
            continue
        if not res:
            continue

        combined["results"].append(res)
        combined["summary"]["successful"] += 1

        if res.get("source") == "gravatar" and res.get("found"):
            combined["summary"]["gravatar"] = True
        if res.get("breaches"):
            combined["summary"]["breaches"] += len(res["breaches"]) if isinstance(res["breaches"], list) else 0
        if res.get("reputation"):
            combined["summary"]["reputation"] = res["reputation"]

    return combined


async def search_email_gravatar(email: str) -> Dict[str, Any]:
    try:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"

        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=False, timeout=5) as resp:
                if resp.status == 200:
                    profile_url = f"https://www.gravatar.com/{email_hash}"
                    return {
                        "source": "gravatar",
                        "found": True,
                        "profile_url": profile_url,
                        "avatar_url": f"https://www.gravatar.com/avatar/{email_hash}?s=500"
                    }
                return {"source": "gravatar", "found": False}
    except Exception as e:
        return {"source": "gravatar", "error": str(e), "found": False}


async def search_email_haveibeenpwned(email: str) -> Dict[str, Any]:
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"hibp-api-key": API_KEYS.get("hibp", ""), "User-Agent": get_random_ua()}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "haveibeenpwned",
                        "breaches": data,
                        "count": len(data)
                    }
                elif resp.status == 404:
                    return {"source": "haveibeenpwned", "breaches": [], "count": 0}
                else:
                    return {"source": "haveibeenpwned", "error": f"HTTP {resp.status}", "breaches": []}
    except Exception as e:
        return {"source": "haveibeenpwned", "error": str(e), "breaches": []}


async def search_email_emailrep(email: str) -> Dict[str, Any]:
    try:
        url = f"https://emailrep.io/{email}"
        headers = {"User-Agent": get_random_ua()}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "emailrep",
                        "reputation": data.get("reputation"),
                        "suspicious": data.get("suspicious"),
                        "details": data.get("details", {}),
                        "breaches": data.get("breaches", [])
                    }
                return {"source": "emailrep", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "emailrep", "error": str(e)}


async def search_email_abstractapi(email: str) -> Dict[str, Any]:
    try:
        if not API_KEYS.get("abstractapi"):
            return {"source": "abstractapi", "note": "no API key", "valid_format": "unknown"}

        url = f"https://emailvalidation.abstractapi.com/v1/?api_key={API_KEYS['abstractapi']}&email={email}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "abstractapi",
                        "valid_format": data.get("is_valid_format", {}).get("value"),
                        "free": data.get("is_free_email", {}).get("value"),
                        "disposable": data.get("is_disposable_email", {}).get("value"),
                        "role": data.get("is_role_email", {}).get("value"),
                        "domain": data.get("domain"),
                        "quality_score": data.get("quality_score")
                    }
                return {"source": "abstractapi", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "abstractapi", "error": str(e)}


async def search_email_google(email: str) -> Dict[str, Any]:
    try:
        url = "https://www.google.com/search"
        params = {"q": f'"{email}"'}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy, timeout=5) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'About ([0-9,]+) results', html)
                    count = match.group(1).replace(',', '') if match else "0"
                    return {
                        "source": "google",
                        "results_count": int(count) if count.isdigit() else 0,
                        "url": f"https://www.google.com/search?q=%22{email}%22"
                    }
                return {"source": "google", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "google", "error": str(e)}


async def search_email_yandex(email: str) -> Dict[str, Any]:
    try:
        url = "https://yandex.ru/search/"
        params = {"text": f'"{email}"', "lr": "213"}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy, timeout=5) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'Нашлось ([0-9 ]+) ответов', html)
                    count = match.group(1).replace(' ', '') if match else "0"
                    return {
                        "source": "yandex",
                        "results_count": int(count) if count.isdigit() else 0,
                        "url": f"https://yandex.ru/search/?text=%22{email}%22"
                    }
                return {"source": "yandex", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "yandex", "error": str(e)}


async def search_email_github(email: str) -> Dict[str, Any]:
    try:
        url = "https://api.github.com/search/commits"
        params = {"q": f"author-email:{email}"}
        headers = {
            "User-Agent": get_random_ua(),
            "Accept": "application/vnd.github.cloak-preview"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "github",
                        "total_count": data.get("total_count", 0),
                        "items": data.get("items", [])[:3]
                    }
                return {"source": "github", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "github", "error": str(e)}


async def search_email_leakcheck(email: str) -> Dict[str, Any]:
    return {"source": "leakcheck", "found": False, "note": "requires auth"}