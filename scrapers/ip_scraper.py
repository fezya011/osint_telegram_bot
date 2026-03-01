import asyncio

import aiohttp
from typing import Dict, Any
from config import USER_AGENTS, PROXY_LIST, API_KEYS
from utils.proxy_rotator import get_random_proxy
from utils.user_agent import get_random_ua
import socket
import struct
import ipaddress


async def search_ip(ip: str) -> Dict[str, Any]:
    tasks = [
        search_ip_ipinfo(ip),
        search_ip_ipapi(ip),
        search_ip_abuseipdb(ip),
        search_ip_virustotal(ip),
        search_ip_shodan(ip),
        search_ip_censys(ip),
        search_ip_binaryedge(ip),
        search_ip_greynoise(ip),
        search_ip_whatismyip(ip),
        search_ip_ip2location(ip)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined = {
        "source": "ip_search",
        "query": ip,
        "results": [],
        "summary": {
            "total_sources": len(results),
            "successful": 0,
            "country": None,
            "asn": None,
            "isp": None,
            "vpn": False,
            "tor": False,
            "abuse_reports": 0
        }
    }

    for res in results:
        if isinstance(res, Exception) or not res:
            continue
        combined["results"].append(res)
        combined["summary"]["successful"] += 1
        if res.get("country") and not combined["summary"]["country"]:
            combined["summary"]["country"] = res["country"]
        if res.get("asn") and not combined["summary"]["asn"]:
            combined["summary"]["asn"] = res["asn"]
        if res.get("isp") and not combined["summary"]["isp"]:
            combined["summary"]["isp"] = res["isp"]
        if res.get("vpn"):
            combined["summary"]["vpn"] = True
        if res.get("tor"):
            combined["summary"]["tor"] = True
        if res.get("abuse_reports"):
            combined["summary"]["abuse_reports"] += res["abuse_reports"]

    return combined


async def search_ip_ipinfo(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://ipinfo.io/{ip}/json"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "ipinfo",
                        "ip": data.get("ip"),
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country"),
                        "loc": data.get("loc"),
                        "org": data.get("org"),
                        "postal": data.get("postal"),
                        "timezone": data.get("timezone"),
                        "asn": data.get("asn", {}).get("asn") if isinstance(data.get("asn"), dict) else None,
                        "company": data.get("company", {}).get("name") if isinstance(data.get("company"),
                                                                                     dict) else None
                    }
                return {"source": "ipinfo", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "ipinfo", "error": str(e)}


async def search_ip_ipapi(ip: str) -> Dict[str, Any]:
    try:
        url = f"http://api.ipapi.com/{ip}?access_key={API_KEYS.get('ipapi', 'demo')}"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "ipapi",
                        "ip": data.get("ip"),
                        "type": data.get("type"),
                        "continent_code": data.get("continent_code"),
                        "continent_name": data.get("continent_name"),
                        "country_code": data.get("country_code"),
                        "country_name": data.get("country_name"),
                        "region_code": data.get("region_code"),
                        "region_name": data.get("region_name"),
                        "city": data.get("city"),
                        "zip": data.get("zip"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),
                        "location": data.get("location", {}),
                        "time_zone": data.get("time_zone", {}),
                        "currency": data.get("currency", {}),
                        "connection": data.get("connection", {}),
                        "security": data.get("security", {})
                    }
                return {"source": "ipapi", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "ipapi", "error": str(e)}


async def search_ip_abuseipdb(ip: str) -> Dict[str, Any]:
    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        params = {"ipAddress": ip, "maxAgeInDays": 90}
        headers = {
            "Key": API_KEYS.get("abuseipdb", "YOUR_KEY"),
            "Accept": "application/json",
            "User-Agent": get_random_ua()
        }
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "abuseipdb",
                        "ip": data.get("data", {}).get("ipAddress"),
                        "is_public": data.get("data", {}).get("isPublic"),
                        "ip_version": data.get("data", {}).get("ipVersion"),
                        "is_whitelisted": data.get("data", {}).get("isWhitelisted"),
                        "abuse_confidence_score": data.get("data", {}).get("abuseConfidenceScore"),
                        "country_code": data.get("data", {}).get("countryCode"),
                        "usage_type": data.get("data", {}).get("usageType"),
                        "isp": data.get("data", {}).get("isp"),
                        "domain": data.get("data", {}).get("domain"),
                        "hostnames": data.get("data", {}).get("hostnames", []),
                        "total_reports": data.get("data", {}).get("totalReports"),
                        "num_distinct_users": data.get("data", {}).get("numDistinctUsers"),
                        "last_reported_at": data.get("data", {}).get("lastReportedAt"),
                        "reports": data.get("data", {}).get("reports", [])
                    }
                return {"source": "abuseipdb", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "abuseipdb", "error": str(e)}


async def search_ip_virustotal(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        headers = {"x-apikey": API_KEYS.get("virustotal", "YOUR_KEY")}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    attributes = data.get("data", {}).get("attributes", {})
                    return {
                        "source": "virustotal",
                        "ip": ip,
                        "asn": attributes.get("asn"),
                        "as_owner": attributes.get("as_owner"),
                        "country": attributes.get("country"),
                        "network": attributes.get("network"),
                        "regional_internet_registry": attributes.get("regional_internet_registry"),
                        "reputation": attributes.get("reputation"),
                        "last_analysis_stats": attributes.get("last_analysis_stats", {}),
                        "tags": attributes.get("tags", [])
                    }
                return {"source": "virustotal", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "virustotal", "error": str(e)}


async def search_ip_shodan(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://api.shodan.io/shodan/host/{ip}?key={API_KEYS.get('shodan', 'YOUR_KEY')}"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "shodan",
                        "ip": data.get("ip_str"),
                          "ports": data.get("ports", []),
                        "hostnames": data.get("hostnames", []),
                        "city": data.get("city"),
                        "region": data.get("region_code"),
                        "country": data.get("country_code"),
                        "org": data.get("org"),
                        "asn": data.get("asn"),
                        "isp": data.get("isp"),
                        "os": data.get("os"),
                        "last_update": data.get("last_update"),
                        "vulns": data.get("vulns", []),
                        "tags": data.get("tags", [])
                    }
                return {"source": "shodan", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "shodan", "error": str(e)}

async def search_ip_censys(ip: str) -> Dict[str, Any]:
    try:
        auth = aiohttp.BasicAuth(login=API_KEYS.get("censys_id", ""), password=API_KEYS.get("censys_secret", ""))
        url = f"https://search.censys.io/api/v2/hosts/{ip}"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=auth, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    return {
                        "source": "censys",
                        "ip": result.get("ip"),
                        "location": result.get("location", {}),
                        "autonomous_system": result.get("autonomous_system", {}),
                        "services": result.get("services", []),
                        "labels": result.get("labels", [])
                    }
                return {"source": "censys", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "censys", "error": str(e)}

async def search_ip_binaryedge(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://api.binaryedge.io/v2/query/ip/{ip}"
        headers = {"X-Key": API_KEYS.get("binaryedge", "YOUR_KEY")}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "binaryedge",
                        "ip": data.get("target", {}).get("ip"),
                        "events": data.get("events", []),
                        "total": data.get("total", 0)
                    }
                return {"source": "binaryedge", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "binaryedge", "error": str(e)}

async def search_ip_greynoise(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://api.greynoise.io/v3/community/{ip}"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "greynoise",
                        "ip": data.get("ip"),
                        "noise": data.get("noise"),
                        "riot": data.get("riot"),
                        "classification": data.get("classification"),
                        "name": data.get("name"),
                        "link": data.get("link"),
                        "last_seen": data.get("last_seen")
                    }
                return {"source": "greynoise", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "greynoise", "error": str(e)}

async def search_ip_whatismyip(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://whatismyipaddress.com/ip/{ip}"
        headers = {"User-Agent": get_random_ua()}
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                if resp.status == 200:
                    html = await resp.text()

                    import re
                    ip_info = {}

                    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
                    if tables:
                        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.DOTALL)
                        for row in rows:
                            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
                            if len(cells) >= 2:
                                key = re.sub(r'<[^>]+>', '', cells[0]).strip()
                                value = re.sub(r'<[^>]+>', '', cells[1]).strip()
                                ip_info[key] = value
                    return {
                        "source": "whatismyip",
                        "ip": ip,
                        "info": ip_info
                    }
                return {"source": "whatismyip", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "whatismyip", "error": str(e)}

async def search_ip_ip2location(ip: str) -> Dict[str, Any]:
    try:
        url = f"https://api.ip2location.com/v2/?ip={ip}&key={API_KEYS.get('ip2location', 'demo')}&package=WS1"
        proxy = get_random_proxy()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "ip2location",
                        "ip": data.get("ip"),
                        "country_code": data.get("country_code"),
                        "country_name": data.get("country_name"),
                        "region_name": data.get("region_name"),
                        "city_name": data.get("city_name"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),
                        "zip_code": data.get("zip_code"),
                        "time_zone": data.get("time_zone"),
                        "asn": data.get("asn"),
                        "as": data.get("as")
                    }
                return {"source": "ip2location", "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"source": "ip2location", "error": str(e)}