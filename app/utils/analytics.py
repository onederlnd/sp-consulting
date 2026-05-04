from user_agents import parse as parse_ua


BOT_PATTERNS = [
    "bot",
    "crawler",
    "spider",
    "slurp",
    "bingbot",
    "googlebot",
    "yahoo",
    "baidu",
    "duckduck",
    "facebot",
    "ia_archiver",
    "semrush",
    "ahrefsbot",
    "mj12bot",
    "dotbot",
    "rogerbot",
]


def is_bot(user_agent_string):
    if not user_agent_string:
        return False
    ua_lower = user_agent_string.lower()
    if any(pattern in ua_lower for pattern in BOT_PATTERNS):
        return True
    try:
        ua = parse_ua(user_agent_string)
        return ua.is_bot
    except Exception:
        return False


def parse_device_type(user_agent_string):
    if not user_agent_string:
        return "unknown"
    try:
        ua = parse_ua(user_agent_string)
        if ua.is_mobile:
            return "mobile"
        elif ua.is_tablet:
            return "tablet"
        else:
            return "desktop"
    except Exception:
        return "unknown"


def parse_browser(user_agent_string):
    if not user_agent_string:
        return "unknown"
    try:
        ua = parse_ua(user_agent_string)
        return ua.browser.family or "unknown"
    except Exception:
        return "unknown"


def parse_os(user_agent_string):
    if not user_agent_string:
        return "unknown"
    try:
        ua = parse_ua(user_agent_string)
        return ua.os.family or "unknown"
    except Exception:
        return "unknown"


def lookup_geo(ip_address):
    """Geo lookup stub — wire up a provider here later."""
    return None, None


def get_client_ip(request):
    """Get real IP, handling proxies."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr
