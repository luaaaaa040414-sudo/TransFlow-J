"""
信源站内检索深链构造 (Source Search Links)

问题：证据里的 source_url 大多只写到网站首页（https://www.termonline.cn），
      用户点「查看权威出处」进去还得自己再搜一遍，等于没帮上忙。

目标：把首页地址换成【该站针对本术语的检索结果页】。
      例：https://www.termonline.cn  →  https://www.termonline.cn/search?searchText=carbon%20neutrality

实现要点：
1. 按 host 后缀匹配模板（www.termonline.cn 命中 termonline.cn）；
   host 匹配不到时，再用信源名称关键词兜底（"TermOnline" / "全国科学技术名词审定委员会"）。
2. 不同站点用不同检索词：中文站用中文原词，英文站必须用英文译名
   （拿中文词去 nature.com 搜必然 0 结果）。
3. 每个模板都带 verified 字段记录实测日期，没有实测过的站点一律不写模板，
   宁可打开首页，也不给"点了没结果"的假链接。

2026-10-18 实测结论（curl + 浏览器 UA，检索词 carbon neutrality）：
  ✅ termonline.cn   200 《术语在线》
  ✅ nature.com      200 「carbon neutrality | Nature Search Results」
  ✅ ieeexplore      200 「IEEE Xplore Search Results」
  ✅ dl.acm.org      403 Cloudflare 挑战页（真人浏览器可过，链接格式正确）
  ✅ ncbi.nlm.nih.gov 200 「carbon neutrality - MeSH - NCBI」
  ✅ iso.org         200 「ISO - Search」
  ✅ arxiv.org       200 「Search | arXiv」
  ✅ sciencedirect   200 「carbon neutrality - Search | ScienceDirect」
  ⚠️ onepetro.org    403 Cloudflare 挑战页（链接格式正确）
  ❌ cae.cn / chnmuseum.cn / api.org / swpu.edu.cn  无可用检索深链 → 打开首页
"""
import re
from typing import Dict, Optional, Tuple
from urllib.parse import quote, urlparse

# ============================================================
# 站点检索模板
#   url   ：检索地址，{q} 会被替换成编码后的检索词
#   lang  ：zh = 用中文原词，en = 用英文译名
#   double：该站前端会再 decodeURI 一次，需要二次编码
# ============================================================
SEARCH_TEMPLATES: Dict[str, Dict] = {
    # ---------- 一级：国家/国际权威术语库 ----------
    "termonline.cn": {
        "url": "https://www.termonline.cn/search?searchText={q}",
        "lang": "zh",
        "label": "术语在线",
        "verified": "2026-10-18",
        "note": "参数名是 searchText（不是 k）；中文词、英文词都能命中",
    },
    "ncbi.nlm.nih.gov": {
        "url": "https://www.ncbi.nlm.nih.gov/mesh/?term={q}",
        "lang": "en",
        "label": "NCBI MeSH",
        "verified": "2026-10-18",
        "note": "医学主题词表，须用英文",
    },
    "iso.org": {
        "url": "https://www.iso.org/search.html?q={q}",
        "lang": "en",
        "label": "ISO 标准检索",
        "verified": "2026-10-18",
    },

    # ---------- 二级：行业标准 ----------
    "ieeexplore.ieee.org": {
        "url": "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={q}",
        "lang": "en",
        "label": "IEEE Xplore",
        "verified": "2026-10-18",
    },
    "onepetro.org": {
        "url": "https://onepetro.org/search-results?q={q}",
        "lang": "en",
        "label": "OnePetro（SPE 论文库）",
        "verified": "2026-10-18",
        "note": "有 Cloudflare 挑战，真人浏览器正常",
    },

    # ---------- 三级：顶级期刊与学术库 ----------
    "nature.com": {
        "url": "https://www.nature.com/search?q={q}",
        "lang": "en",
        "label": "Nature 检索",
        "verified": "2026-10-18",
    },
    "dl.acm.org": {
        "url": "https://dl.acm.org/action/doSearch?AllField={q}",
        "lang": "en",
        "label": "ACM Digital Library",
        "verified": "2026-10-18",
        "note": "有 Cloudflare 挑战，真人浏览器正常",
    },
    "arxiv.org": {
        "url": "https://arxiv.org/search/?query={q}&searchtype=all",
        "lang": "en",
        "label": "arXiv",
        "verified": "2026-10-18",
    },
    "sciencedirect.com": {
        "url": "https://www.sciencedirect.com/search?qs={q}",
        "lang": "en",
        "label": "ScienceDirect",
        "verified": "2026-10-18",
    },

    # ---------- 国内权威机构（旧版已实测） ----------
    "cas.cn": {
        "url": "https://www.cas.cn/search/index.shtml?keyword={q}",
        "lang": "zh",
        "label": "中国科学院",
        "double": True,
        "verified": "2026-10-15",
        "note": "参数是 keyword；该页会再 decodeURI 一次，必须双重编码",
    },
    "gov.cn": {
        "url": "https://sousuo.www.gov.cn/sousuo/search.shtml?code=17da70961a7&searchWord={q}",
        "lang": "zh",
        "label": "中国政府网",
        "verified": "2026-10-15",
    },
    "english.www.gov.cn": {
        "url": "https://search.english.www.gov.cn/en/search.shtml?code=17dbe3acd9d&dataTypeId=57&searchWord={q}",
        "lang": "en",
        "label": "中国政府网英文版",
        "verified": "2026-10-15",
    },
    "moe.gov.cn": {
        "url": "http://www.moe.gov.cn/was5/web/search?searchword={q}&channelid=254028&page=1",
        "lang": "en",
        "label": "教育部英文官网",
        "verified": "2026-10-15",
        "note": "en.moe.gov.cn 的表单实际提交到这里，须用英文词",
    },
}

# ============================================================
# 信源名称 → 模板 key（source_url 缺失或只是首页时的兜底）
# ============================================================
NAME_HINTS: Dict[str, str] = {
    "termonline": "termonline.cn",
    "术语在线": "termonline.cn",
    "全国科学技术名词": "termonline.cn",
    "全国自然科学名词": "termonline.cn",
    "名词审定委员会": "termonline.cn",
    "ncbi": "ncbi.nlm.nih.gov",
    "mesh": "ncbi.nlm.nih.gov",
    "iso": "iso.org",
    "国际标准化组织": "iso.org",
    "ieee": "ieeexplore.ieee.org",
    "onepetro": "onepetro.org",
    "spe journal": "onepetro.org",
    "spe ": "onepetro.org",
    "society of petroleum": "onepetro.org",
    "nature": "nature.com",
    "acm": "dl.acm.org",
    "arxiv": "arxiv.org",
    "sciencedirect": "sciencedirect.com",
    "elsevier": "sciencedirect.com",
    "中国科学院": "cas.cn",
    "教育部": "moe.gov.cn",
    "国务院": "gov.cn",
}

# 明确没有站内检索、只能打开首页的站点（避免被 NAME_HINTS 误伤）
HOMEPAGE_ONLY = {
    "cae.cn",
    "chnmuseum.cn",
    "cgs.gov.cn",
    "api.org",
    "swpu.edu.cn",
    "scio.gov.cn",
}


def _host(url: str) -> str:
    if not url:
        return ""
    try:
        h = urlparse(url).hostname or ""
    except Exception:
        return ""
    return h.lower()


def _match_host(host: str) -> Optional[str]:
    """host 后缀匹配，长的优先（english.www.gov.cn 要优先于 gov.cn）"""
    if not host:
        return None
    for key in sorted(SEARCH_TEMPLATES.keys(), key=len, reverse=True):
        if host == key or host.endswith("." + key):
            return key
    return None


def _match_name(name: str) -> Optional[str]:
    low = (name or "").lower()
    if not low:
        return None
    for hint, key in sorted(NAME_HINTS.items(), key=lambda kv: len(kv[0]), reverse=True):
        if hint in low:
            return key
    return None


def _is_homepage_only(host: str, name: str) -> bool:
    for bad in HOMEPAGE_ONLY:
        if host == bad or host.endswith("." + bad):
            return True
    return False


def _encode(term: str, double: bool = False) -> str:
    once = quote(term, safe="")
    return quote(once, safe="") if double else once


def build_search_url(
    source_url: str,
    source_name: str = "",
    term_zh: str = "",
    term_en: str = "",
) -> Tuple[str, str]:
    """
    返回 (url, kind)，kind ∈ {"search", "homepage"}

    search   = 该站针对本术语的检索结果页
    homepage = 该站没有可用检索入口，只能打开原地址
    """
    host = _host(source_url)

    # 1. 明确无检索入口的站点，直接返回原地址
    if _is_homepage_only(host, source_name):
        return (source_url or "", "homepage")

    # 2. 找模板：先按 host，再按信源名称
    key = _match_host(host) or _match_name(source_name)
    if not key:
        return (source_url or "", "homepage")

    tpl = SEARCH_TEMPLATES[key]

    # 3. 选检索词
    #    中文站：中文原词优先，没有再用英文
    #    英文站：必须用英文译名。拿中文词去 onepetro / nature 搜必然是 0 结果，
    #            那种"假检索"比打开首页更糟，所以直接降级为 homepage。
    if tpl.get("lang") == "en":
        q = (term_en or "").strip()
        if not q:
            return (source_url or "", "homepage")
    else:
        q = (term_zh or "").strip() or (term_en or "").strip()
    if not q:
        return (source_url or "", "homepage")

    return (tpl["url"].replace("{q}", _encode(q, tpl.get("double", False))), "search")


def annotate_evidence(ev: dict, term_zh: str, term_en: str) -> dict:
    """就地改写一条证据的 source_url，并写入 source_url_kind / source_search_label"""
    url, kind = build_search_url(
        ev.get("source_url", ""), ev.get("source_name", ""), term_zh, term_en
    )
    ev["source_url"] = url
    ev["source_url_kind"] = kind
    if kind == "search":
        host = _host(url)
        key = _match_host(host) or _match_name(ev.get("source_name", ""))
        ev["source_search_label"] = SEARCH_TEMPLATES.get(key, {}).get("label", "站内检索")
    else:
        ev["source_search_label"] = ""
    return ev
