from typing import Dict, Any
import json


def format_phone_result(query: str, data: Dict[str, Any]) -> str:
    text = f"🔍 <b>Результаты по номеру {query}</b>\n\n"

    summary = data.get("summary", {})
    text += f"📊 <b>Сводка:</b>\n"
    text += f"• Источников с данными: {summary.get('successful', 0)}/{summary.get('total_sources', 0)}\n"
    if summary.get('carrier'):
        text += f"• Оператор: {summary['carrier']}\n"
    if summary.get('region'):
        text += f"• Регион: {summary['region']}\n"
    if summary.get('scam_detected'):
        text += f"• ⚠️ <b>Отмечен как мошеннический</b>\n"
    text += "\n"

    for res in data.get("results", []):
        source = res.get("source", "unknown")
        text += f"<b>{source.upper()}:</b>\n"
        if res.get("error"):
            text += f"  Ошибка: {res['error']}\n"
        elif source == "telegram" and res.get("found"):
            text += f"  Username: @{res['username']}\n"
            if res.get("profile_url"):
                text += f"  {res['profile_url']}\n"
        elif source == "getcontact" and res.get("tags"):
            text += f"  Теги: {', '.join(res['tags'][:5])}\n"
            if res.get("spam_count"):
                text += f"  Жалоб на спам: {res['spam_count']}\n"
        elif source == "numverify" and res.get("valid"):
            text += f"  Страна: {res.get('country_name')}\n"
            text += f"  Оператор: {res.get('carrier')}\n"
            text += f"  Тип линии: {res.get('line_type')}\n"
        elif source in ["google", "yandex"]:
            text += f"  Результатов в поиске: {res.get('results_count', 0)}\n"
            text += f"  {res.get('url', '')}\n"
        elif source == "avito" and res.get("count"):
            text += f"  Объявлений: {res['count']}\n"
        elif source == "vk" and res.get("count"):
            text += f"  Найдено пользователей: {res['count']}\n"
            for user in res.get("users", [])[:3]:
                text += f"    • {user.get('first_name')} {user.get('last_name')} (id{user.get('id')})\n"
        elif source == "phndb" and res.get("count"):
            text += f"  Утечек в базе: {res['count']}\n"
        text += "\n"

    if not data.get("results"):
        text += "❌ Ничего не найдено.\n"

    return text


def format_email_result(query: str, data: Dict[str, Any]) -> str:
    text = f"🔍 <b>Результаты по email {query}</b>\n\n"

    summary = data.get("summary", {})
    text += f"📊 <b>Сводка:</b>\n"
    text += f"• Источников с данными: {summary.get('successful', 0)}/{summary.get('total_sources', 0)}\n"
    if summary.get('gravatar'):
        text += f"• Есть Gravatar\n"
    if summary.get('breaches'):
        text += f"• Утечек: {summary['breaches']}\n"
    if summary.get('reputation'):
        text += f"• Репутация: {summary['reputation']}\n"
    text += "\n"

    for res in data.get("results", []):
        source = res.get("source", "unknown")
        text += f"<b>{source.upper()}:</b>\n"
        if res.get("error"):
            text += f"  Ошибка: {res['error']}\n"
        elif source == "gravatar" and res.get("found"):
            text += f"  Профиль: {res['profile_url']}\n"
            text += f"  Аватар: {res['avatar_url']}\n"
        elif source == "haveibeenpwned" and res.get("breaches"):
            text += f"  Утечек: {res['count']}\n"
            for breach in res['breaches'][:5]:
                text += f"    • {breach.get('Name')} ({breach.get('BreachDate')})\n"
        elif source == "emailrep":
            if res.get("suspicious"):
                text += f"  ⚠️ Подозрительный\n"
            text += f"  Репутация: {res.get('reputation', 'N/A')}\n"
            text += f"  Детали: спаммер {res.get('details', {}).get('spammer')}, вредоносный {res.get('details', {}).get('malicious_activity')}\n"
        elif source == "abstractapi":
            text += f"  Валидный: {res.get('valid_format', False)}\n"
            text += f"  Бесплатный: {res.get('free', False)}\n"
            text += f"  Одноразовый: {res.get('disposable', False)}\n"
            text += f"  Ролевой: {res.get('role', False)}\n"
            text += f"  Качество: {res.get('quality_score')}/100\n"
        elif source in ["google", "yandex"]:
            text += f"  Результатов в поиске: {res.get('results_count', 0)}\n"
            text += f"  {res.get('url', '')}\n"
        elif source == "github" and res.get("total_count"):
            text += f"  Коммитов: {res['total_count']}\n"
        text += "\n"

    if not data.get("results"):
        text += "❌ Ничего не найдено.\n"

    return text


def format_username_result(query: str, data: Dict[str, Any]) -> str:
    text = f"🔍 <b>Результаты по username @{query}</b>\n\n"
    text += f"📊 Проверено платформ: {data.get('total_checked', 0)}\n"
    text += f"✅ Найдено профилей: {data.get('found_count', 0)}\n\n"

    for res in data.get("results", []):
        text += f"• <b>{res['platform']}</b>: {res.get('url')}\n"

    if not data.get("results"):
        text += "❌ Профили не найдены.\n"

    return text


def format_ip_result(query: str, data: Dict[str, Any]) -> str:
    text = f"🔍 <b>Результаты по IP {query}</b>\n\n"

    summary = data.get("summary", {})
    text += f"📊 <b>Сводка:</b>\n"
    text += f"• Источников с данными: {summary.get('successful', 0)}/{summary.get('total_sources', 0)}\n"
    if summary.get('country'):
        text += f"• Страна: {summary['country']}\n"
    if summary.get('asn'):
        text += f"• ASN: {summary['asn']}\n"
    if summary.get('isp'):
        text += f"• ISP: {summary['isp']}\n"
    if summary.get('vpn'):
        text += f"• VPN: ДА\n"
    if summary.get('tor'):
        text += f"• Tor: ДА\n"
    if summary.get('abuse_reports'):
        text += f"• Жалоб на абьюз: {summary['abuse_reports']}\n"
    text += "\n"

    for res in data.get("results", []):
        source = res.get("source", "unknown")
        text += f"<b>{source.upper()}:</b>\n"
        if res.get("error"):
            text += f"  Ошибка: {res['error']}\n"
        elif source == "ipinfo":
            text += f"  Город: {res.get('city')}, {res.get('region')}, {res.get('country')}\n"
            text += f"  Координаты: {res.get('loc')}\n"
            text += f"  Организация: {res.get('org')}\n"
        elif source == "ipapi":
            text += f"  Тип: {res.get('type')}\n"
            text += f"  Страна: {res.get('country_name')}\n"
            text += f"  Регион: {res.get('region_name')}, {res.get('city')}\n"
            sec = res.get("security", {})
            if sec.get("is_vpn"):
                text += f"  VPN: ДА\n"
            if sec.get("is_tor"):
                text += f"  Tor: ДА\n"
        elif source == "abuseipdb":
            text += f"  Уверенность в абьюзе: {res.get('abuse_confidence_score')}%\n"
            text += f"  Всего репортов: {res.get('total_reports')}\n"
            text += f"  ISP: {res.get('isp')}\n"
            text += f"  Тип использования: {res.get('usage_type')}\n"
        elif source == "virustotal":
            stats = res.get("last_analysis_stats", {})
            text += f"  Репутация: {res.get('reputation')}\n"
            text += f"  Детектов: {stats.get('malicious', 0)}/{stats.get('total', 0)}\n"
            text += f"  Теги: {', '.join(res.get('tags', []))}\n"
        elif source == "shodan":
            text += f"  Порты: {', '.join(map(str, res.get('ports', [])[:10]))}\n"
            if res.get("vulns"):
                text += f"  Уязвимости: {', '.join(res['vulns'][:5])}\n"
        elif source == "greynoise":
            text += f"  Шум: {res.get('noise')}\n"
            text += f"  Классификация: {res.get('classification')}\n"
        text += "\n"

    if not data.get("results"):
        text += "❌ Ничего не найдено.\n"

    return text