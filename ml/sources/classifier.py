# -*- coding: utf-8 -*-
"""信源分级器（Python 版，供 ML 侧术语核查使用）。

规则与 Java 后端保持一致：
  - 命中三级源（黑名单）→ 拦截
  - 命中一级源 → 可定译
  - 命中二级源 → 需交叉验证
  - 兜底：*.edu.cn（非 swpu.edu.cn）→ 二级
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

SOURCES_PATH = Path(__file__).resolve().parents[2] / "data" / "sources" / "sources.json"


@dataclass
class Verdict:
    tier: str          # tier1 / tier2 / tier3 / unknown
    tier_label: str
    matched: bool
    matched_name: str | None
    reason: str

    @property
    def blocked(self) -> bool:
        return self.tier == "tier3"

    def as_dict(self) -> dict:
        return {
            "tier": self.tier,
            "tier_label": self.tier_label,
            "matched": self.matched,
            "matched_name": self.matched_name,
            "reason": self.reason,
        }


def _host(url: str) -> str | None:
    if "://" not in url:
        url = "http://" + url
    host = urlparse(url).hostname
    if not host:
        return None
    return host.lower().removeprefix("www.")


def _match(host: str, pattern: str) -> bool:
    return host == pattern or host.endswith("." + pattern)


class SourceClassifier:
    def __init__(self, path: Path = SOURCES_PATH):
        self.tiers: dict = json.loads(path.read_text(encoding="utf-8"))["tiers"]

    def classify(self, url: str) -> Verdict:
        host = _host(url)
        if host is None:
            return Verdict("unknown", "无法解析", False, None, "不是合法 URL，需人工确认")

        hit = self._match_tier(host, "tier3")
        if hit:
            return Verdict("tier3", "三级源（黑名单）", True, hit, "命中黑名单，禁止作为术语证据")

        hit = self._match_tier(host, "tier1")
        if hit:
            return Verdict("tier1", "一级源", True, hit, "官方权威来源，可直接作为定译依据")

        hit = self._match_tier(host, "tier2")
        if hit:
            return Verdict("tier2", "二级源", True, hit, "有学术价值但非官方定稿，需两个独立二级源交叉验证")

        if host.endswith(".edu.cn") and not host.endswith("swpu.edu.cn"):
            return Verdict("tier2", "二级源（兜底）", False, None,
                           "高校域名且非本校，按二级处理")
        return Verdict("unknown", "待人工确认", False, None,
                       "未命中任何分级信源，需人工逐一确认（短链尤其注意）")

    def _match_tier(self, host: str, tier: str) -> str | None:
        for source in self.tiers.get(tier, {}).get("sources", []):
            for domain in source.get("domains", []):
                if _match(host, domain):
                    return source["name"]
        return None


def judge_term(evidences: list[dict]) -> dict:
    """对单个候选术语的多条证据做定级裁决。

    evidences: [{"url": ..., "translation": ...}]
    返回 {"status": locked|confirmed|blocked|pending|conflict, ...}
    """
    classifier = SourceClassifier()
    verdicts = [classifier.classify(ev["url"]) for ev in evidences]

    if any(v.blocked for v in verdicts):
        bad = [v for v in verdicts if v.blocked][0]
        return {"status": "blocked", "translation": None,
                "reason": f"证据链命中黑名单「{bad.matched_name}」，本条术语全部作废重查"}

    tier1 = [ev for ev, v in zip(evidences, verdicts) if v.tier == "tier1"]
    if tier1:
        translations = {ev["translation"] for ev in tier1}
        if len(translations) == 1:
            return {"status": "locked", "translation": tier1[0]["translation"],
                    "reason": "一级源一致通过，锁定为强制译法",
                    "evidence": tier1[0]["url"]}
        return {"status": "conflict", "translation": None,
                "reason": f"多个一级源译法不一致：{sorted(translations)}，需人工裁定",
                "evidence": [ev["url"] for ev in tier1]}

    tier2 = [ev for ev, v in zip(evidences, verdicts) if v.tier == "tier2"]
    distinct = {(ev["translation"], ev["url"]) for ev in tier2}
    if len({t for t, _ in distinct}) == 1 and len({u for _, u in distinct}) >= 2:
        return {"status": "confirmed", "translation": tier2[0]["translation"],
                "reason": "两个独立二级源交叉一致，暂定译法",
                "evidence": [u for _, u in distinct]}
    if tier2:
        return {"status": "pending", "translation": None,
                "reason": "仅有二级源且未达交叉验证标准，标记为待人工确认",
                "evidence": [ev["url"] for ev in tier2]}

    return {"status": "pending", "translation": None,
            "reason": "无有效信源覆盖，标记为待人工确认"}


if __name__ == "__main__":
    demo = [
        {"url": "https://www.swpu.edu.cn/xxgk/xxjj.htm", "translation": "Southwest Petroleum University"},
        {"url": "https://baike.baidu.com/item/test", "translation": "西南石油高校"},
        {"url": "https://english.henan.gov.cn/", "translation": "Henan Provincial Government"},
    ]
    for item in demo:
        print(item["url"], "→", SourceClassifier().classify(item["url"]).as_dict())
    print(judge_term([demo[0]]))
    print(judge_term([demo[0], {"url": "https://www.gov.cn/", "translation": "Southwest Petroleum University"}]))
    print(judge_term([demo[1]]))
