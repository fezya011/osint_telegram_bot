import asyncio
import aiohttp
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from config import USER_AGENTS, PROXY_LIST, API_KEYS
from utils.proxy_rotator import get_random_proxy
from utils.user_agent import get_random_ua
import json
import re


async def search_phone(phone: str) -> Dict[str, Any]:
    tasks = [
        search_phone_telegram(phone),
        search_phone_getcontact(phone),
        search_phone_numverify(phone),
        search_phone_abstractapi(phone),
        search_phone_sypex(phone),
        search_phone_avito(phone),
        search_phone_youla(phone),
        search_phone_vk(phone),
        search_phone_ok(phone),
        search_phone_google(phone),
        search_phone_yandex(phone),
        search_phone_phndb(phone),
        search_phone_phonelookup(phone),
        search_phone_syncme(phone)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined = {
        "source": "phone_search",
        "query": phone,
        "results": [],
        "summary": {
            "total_sources": len(results),
            "successful": 0,
            "carrier": None,
            "region": None,
            "scam_detected": False
        }
    }

    for res in results:
        if isinstance(res, Exception) or not res:
            continue
        combined["results"].append(res)
        combined["summary"]["successful"] += 1
        if res.get("carrier") and not combined["summary"]["carrier"]:
            combined["summary"]["carrier"] = res["carrier"]
        if res.get("region") and not combined["summary"]["region"]:
            combined["summary"]["region"] = res["region"]
        if res.get("scam"):
            combined["summary"]["scam_detected"] = True

    return combined


async def search_phone_telegram(phone: str) -> Dict[str, Any]:
    try:
        proxy = get_random_proxy()
        ua = get_random_ua()

        session = curl_requests.AsyncSession(impersonate="chrome120", proxy=proxy)

        url = f"https://t.me/username?phone={phone.replace('+', '')}"
        resp = await session.get(url, headers={"User-Agent": ua})

        if resp.status_code == 200:
            if "If you have Telegram" in resp.text:
                return {"source": "telegram", "found": False}

            soup = BeautifulSoup(resp.text, 'html.parser')
            meta = soup.find("meta", property="og:title")
            if meta:
                username = meta.get("content", "").replace("Telegram: Contact @", "")
                return {
                    "source": "telegram",
                    "found": True,
                    "username": username,
                    "profile_url": f"https://t.me/{username}",
                    "avatar": soup.find("meta", property="og:image")["content"] if soup.find("meta",
                                                                                             property="og:image") else None
                }

        await session.close()
        return {"source": "telegram", "found": False}
    except Exception as e:
        return {"source": "telegram", "error": str(e), "found": False}


async def search_phone_getcontact(phone: str) -> Dict[str, Any]:
    try:
        url = "https://api.getcontact.com/api/v2/search/phone"
        payload = {"phone": phone.replace("+", "")}
        headers = {
            "User-Agent": get_random_ua(),
            "Authorization": "Bearer YOUR_GETCONTACT_TOKEN",  # нужен реальный токен
            "Content-Type": "application/json"
        }
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "getcontact",
                        "tags": data.get("tags", []),
                        "spam_count": data.get("spamCount", 0),
                        "rating": data.get("rating", 0)
                    }
                return {"source": "getcontact", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "getcontact", "error": str(e)}


async def search_phone_numverify(phone: str) -> Dict[str, Any]:
    if not API_KEYS.get("numverify"):
        return {"source": "numverify", "error": "no_api_key"}

    try:
        url = f"http://apilayer.net/api/validate?access_key={API_KEYS['numverify']}&number={phone}&country_code=&format=1"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "numverify",
                        "valid": data.get("valid", False),
                        "line_type": data.get("line_type"),
                        "carrier": data.get("carrier"),
                        "location": data.get("location"),
                        "country_code": data.get("country_code"),
                        "country_name": data.get("country_name")
                    }
                return {"source": "numverify", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "numverify", "error": str(e)}


async def search_phone_abstractapi(phone: str) -> Dict[str, Any]:
    if not API_KEYS.get("abstractapi"):
        return {"source": "abstractapi", "error": "no_api_key"}

    try:
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key={API_KEYS['abstractapi']}&phone={phone}"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "abstractapi",
                        "valid": data.get("valid", False),
                        "format": data.get("format", {}),
                        "country": data.get("country", {}),
                        "location": data.get("location"),
                        "carrier": data.get("carrier")
                    }
                return {"source": "abstractapi", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "abstractapi", "error": str(e)}


async def search_phone_sypex(phone: str) -> Dict[str, Any]:
    try:
        url = "https://sypex.ru/search.php"
        params = {"q": phone.replace("+", ""), "s": "1"}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    tables = soup.find_all("table", class_="search")
                    if tables:
                        rows = tables[0].find_all("tr")[1:]
                        results = []
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) >= 4:
                                results.append({
                                    "region": cols[1].text.strip(),
                                    "operator": cols[2].text.strip(),
                                    "info": cols[3].text.strip()
                                })
                        return {"source": "sypex", "results": results}
                return {"source": "sypex", "found": False}
    except Exception as e:
        return {"source": "sypex", "error": str(e)}


async def search_phone_avito(phone: str) -> Dict[str, Any]:
    try:
        url = f"https://www.avito.ru/items/phone/{phone.replace('+', '')}"
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "avito",
                        "items": data.get("items", []),
                        "count": len(data.get("items", []))
                    }
                return {"source": "avito", "found": False}
    except Exception as e:
        return {"source": "avito", "error": str(e)}


async def search_phone_youla(phone: str) -> Dict[str, Any]:
    try:
        url = f"https://youla.ru/web-api/users/phone/{phone.replace('+', '')}"
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "youla",
                        "user": data.get("user"),
                        "products_count": len(data.get("products", []))
                    }
                return {"source": "youla", "found": False}
    except Exception as e:
        return {"source": "youla", "error": str(e)}


async def search_phone_vk(phone: str) -> Dict[str, Any]:
    try:
        phone_clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        if phone_clean.startswith("8"):
            phone_clean = "7" + phone_clean[1:]

        url = "https://api.vk.com/method/users.search"
        params = {
            "q": phone_clean,
            "fields": "photo_max,contacts,connections",
            "access_token": "YOUR_VK_TOKEN",  # нужен токен
            "v": "5.131"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("response", {}).get("items"):
                        return {
                            "source": "vk",
                            "users": data["response"]["items"],
                            "count": len(data["response"]["items"])
                        }
                return {"source": "vk", "found": False}
    except Exception as e:
        return {"source": "vk", "error": str(e)}


async def search_phone_ok(phone: str) -> Dict[str, Any]:
    try:
        return {"source": "ok", "found": False, "note": "requires signed requests"}
    except Exception as e:
        return {"source": "ok", "error": str(e)}


async def search_phone_google(phone: str) -> Dict[str, Any]:
    try:
        url = "https://www.google.com/search"
        params = {"q": f'"{phone}"'}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'About ([0-9,]+) results', html)
                    count = match.group(1).replace(',', '') if match else 0
                    return {
                        "source": "google",
                        "results_count": int(count) if count else 0,
                        "url": f"https://www.google.com/search?q=%22{phone}%22"
                    }
                return {"source": "google", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "google", "error": str(e)}


async def search_phone_yandex(phone: str) -> Dict[str, Any]:
    try:
        url = "https://yandex.ru/search/"
        params = {"text": f'"{phone}"', "lr": "213"}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'Нашлось ([0-9 ]+) ответов', html)
                    count = match.group(1).replace(' ', '') if match else 0
                    return {
                        "source": "yandex",
                        "results_count": int(count) if count else 0,
                        "url": f"https://yandex.ru/search/?text=%22{phone}%22"
                    }
                return {"source": "yandex", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "yandex", "error": str(e)}


async def search_phone_phndb(phone: str) -> Dict[str, Any]:
    try:
        url = f"https://phndb.net/phone/{phone.replace('+', '')}"
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    leaks = soup.find_all("div", class_="leak-item")
                    results = []
                    for leak in leaks:
                        title = leak.find("h3")
                        if title:
                            results.append(title.text.strip())
                    return {
                        "source": "phndb",
                        "leaks": results,
                        "count": len(results)
                    }
                return {"source": "phndb", "found": False}
    except Exception as e:
        return {"source": "phndb", "error": str(e)}


async def search_phone_phonelookup(phone: str) -> Dict[str, Any]:
    try:
        url = "https://www.phonelookup.com/result"
        params = {"phonenumber": phone}
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    carrier = soup.find("span", class_="carrier")
                    location = soup.find("span", class_="location")
                    return {
                        "source": "phonelookup",
                        "carrier": carrier.text.strip() if carrier else None,
                        "location": location.text.strip() if location else None,
                        "valid": True
                    }
                return {"source": "phonelookup", "found": False}
    except Exception as e:
        return {"source": "phonelookup", "error": str(e)}


async def search_phone_syncme(phone: str) -> Dict[str, Any]:
    return {"source": "syncme", "found": False, "note": "mobile app required"}