"""
MQM 校对服务 - 调用独立校对模型
按 MQM 错误分类规则检查译文质量
"""
import json
import logging
from typing import Optional, Dict, List, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# MQM 错误类型定义
# ============================================================

MQM_ERROR_TYPES = {
    "Accuracy": {
        "description": "译文与原文含义不符",
        "subtypes": ["Mistranslation", "Omission", "Addition", "Untranslated"],
    },
    "Fluency": {
        "description": "译文流畅性、语法问题",
        "subtypes": ["Grammar", "Register", "Spelling", "Punctuation", "Inconsistency"],
    },
    "Terminology": {
        "description": "专业术语使用不当",
        "subtypes": ["Inconsistent", "WrongTerm", "Invented"],
    },
    "Style": {
        "description": "文体风格不符合期刊要求",
        "subtypes": ["Register", "Awkward", "VoiceOrTense"],
    },
    "Locale": {
        "description": "地区性规范问题（英美拼写等）",
        "subtypes": ["Spelling", "NumberFormat", "DateFormat"],
    },
}

MQM_SEVERITY_LEVELS = ["critical", "major", "minor", "neutral"]


# ============================================================
# 校对提示词构建
# ============================================================

def build_proofreading_prompt(
    source_text: str,
    translated_text: str,
    segment_id: str,
    terminology_map: Optional[Dict[str, str]] = None,
    journal_style: Optional[Dict] = None,
) -> str:
    """构建 MQM 校对提示词"""
    prompt_parts = [
        "你是一名专业的学术翻译质量评审专家，使用 MQM（多维质量指标）框架对中译英译文进行评审。",
        "",
        f"【待审段落编号】{segment_id}",
        "",
        "【中文原文】",
        source_text,
        "",
        "【当前英文译文】",
        translated_text,
    ]

    if terminology_map:
        prompt_parts.extend([
            "",
            "【已确认术语表（译文应遵循）】",
        ])
        for zh, en in terminology_map.items():
            prompt_parts.append(f"  {zh} → {en}")

    if journal_style:
        journal_name = journal_style.get("name", "")
        english_variant = journal_style.get("english_variant", "American")
        prompt_parts.extend([
            "",
            f"【目标期刊】{journal_name}",
            f"【语言规范】{english_variant} English",
        ])

    prompt_parts.extend([
        "",
        "【MQM 错误类型参考】",
        "- Accuracy: 准确性（漏译/错译/添加/未翻译）",
        "- Fluency: 流畅性（语法/拼写/标点/不一致）",
        "- Terminology: 术语（不一致/错误术语）",
        "- Style: 风格（语态/时态/语域）",
        "- Locale: 地区规范（英美拼写差异等）",
        "",
        "【严重程度】critical > major > minor > neutral",
        "",
        "【任务】",
        "请逐项检查译文，发现问题请以 JSON 数组格式输出。",
        "如果译文没有问题，返回空数组 []。",
        "",
        "【输出格式（JSON 数组）】",
        """[
  {
    "error_type": "错误类型（Accuracy/Fluency/Terminology/Style/Locale）",
    "error_subtype": "子类型",
    "severity": "critical/major/minor/neutral",
    "source_span": "原文中相关文字片段",
    "translation_span": "译文中相关文字片段",
    "explanation": "问题说明（中文）",
    "suggested_revision": "建议修改后的译文（仅修改有问题的部分）",
    "evidence": "依据（如术语表规定、期刊规范等）"
  }
]""",
        "",
        "注意：只报告真正存在的问题；建议修改必须基于原文，不得添加原文没有的内容；每个 JSON key 必须使用双引号。",
    ])

    return "\n".join(prompt_parts)


def parse_mqm_response(response_text: str) -> List[Dict]:
    """解析模型返回的 MQM JSON"""
    # 提取 JSON 数组
    response_text = response_text.strip()

    # 尝试找到 JSON 数组
    start = response_text.find("[")
    end = response_text.rfind("]")

    if start == -1 or end == -1:
        logger.warning("模型未返回有效 JSON 数组")
        return []

    json_str = response_text[start:end+1]

    try:
        issues = json.loads(json_str)
        if not isinstance(issues, list):
            return []

        # 验证必要字段
        valid_issues = []
        for issue in issues:
            if isinstance(issue, dict) and "error_type" in issue and "explanation" in issue:
                # 确保 severity 是有效值
                if issue.get("severity") not in MQM_SEVERITY_LEVELS:
                    issue["severity"] = "minor"
                valid_issues.append(issue)

        return valid_issues

    except json.JSONDecodeError as e:
        logger.error(f"MQM JSON 解析失败: {e}\n原始响应: {json_str[:500]}")
        return []


# ============================================================
# MQM 校对服务
# ============================================================

class MQMReviewService:

    async def _call_openai_compatible(
        self,
        prompt: str,
        api_key: str,
        base_url: str,
        model: str,
    ) -> str:
        """调用 OpenAI 兼容接口"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是专业的翻译质量评审专家，严格按照 MQM 框架输出结构化 JSON。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,  # 低温度，保证一致性
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _call_anthropic(self, prompt: str, api_key: str, model: str) -> str:
        """调用 Anthropic Claude"""
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()

    def _simulate_mqm_review(
        self,
        source_text: str,
        translated_text: str,
        segment_id: str,
        terminology_map: Optional[Dict[str, str]] = None,
        journal_style: Optional[Dict] = None,
    ) -> List[Dict]:
        issues = []
        # 1. 术语一致性检查
        if terminology_map:
            for zh_term, en_term in terminology_map.items():
                if zh_term in source_text and en_term.lower() not in translated_text.lower():
                    issues.append({
                        "error_type": "Terminology",
                        "error_subtype": "Inconsistent",
                        "severity": "major",
                        "source_span": zh_term,
                        "translation_span": "（译文中未匹配标准译名）",
                        "explanation": f"未按照已确认术语表规范将「{zh_term}」译为「{en_term}」",
                        "suggested_revision": en_term,
                        "evidence": f"项目术语表强约束规则：{zh_term} → {en_term}",
                    })

        # 2. 期刊风格（第一人称检查）
        if journal_style and any(w in translated_text.split() for w in ["We", "we", "Our", "our"]):
            issues.append({
                "error_type": "Style",
                "error_subtype": "VoiceOrTense",
                "severity": "minor",
                "source_span": "第一人称主观表述",
                "translation_span": "we / our",
                "explanation": f"目标期刊 {journal_style.get('name', '学术期刊')} 偏好客观被动语态或第三人称，建议将第一人称主格转为被动或客观论述",
                "suggested_revision": "The study demonstrates / It was observed that...",
                "evidence": "期刊投稿指南要求客观学术语态",
            })

        # 3. 兜底示例
        if not issues:
            issues.append({
                "error_type": "Style",
                "error_subtype": "Register",
                "severity": "minor",
                "source_span": source_text[:30],
                "translation_span": translated_text[:40],
                "explanation": "句式与学术表达良好，建议在最终投稿前结合期刊特定引文排版要求进行微调",
                "suggested_revision": translated_text,
                "evidence": "学术期刊规范审校",
            })

        return issues

    def _get_api_config(self, provider: str) -> tuple:
        """获取 API 配置 (api_key, base_url)"""
        if provider == "openai":
            return settings.openai_api_key, settings.openai_base_url
        elif provider == "deepseek":
            return settings.deepseek_api_key, settings.deepseek_base_url
        elif provider == "custom":
            return settings.custom_api_key, settings.custom_base_url
        return "", ""

    async def review_segment(
        self,
        source_text: str,
        translated_text: str,
        segment_id: str,
        provider: str = "deepseek",
        model: str = "deepseek-chat",
        terminology_map: Optional[Dict[str, str]] = None,
        journal_style: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        对单个段落进行 MQM 校对
        返回错误列表和摘要
        """
        if not translated_text or not translated_text.strip():
            return {
                "success": False,
                "error": "译文为空，无法校对",
                "issues": [],
                "segment_id": segment_id,
            }

        prompt = build_proofreading_prompt(
            source_text=source_text,
            translated_text=translated_text,
            segment_id=segment_id,
            terminology_map=terminology_map,
            journal_style=journal_style,
        )

        try:
            if provider in ("simulation", "demo"):
                issues = self._simulate_mqm_review(
                    source_text=source_text,
                    translated_text=translated_text,
                    segment_id=segment_id,
                    terminology_map=terminology_map,
                    journal_style=journal_style,
                )
                raw_response = json.dumps(issues, ensure_ascii=False)
            elif provider == "anthropic":
                api_key = settings.anthropic_api_key
                if not api_key:
                    raise ValueError("Anthropic API Key 未配置。可直接选择已就绪的 DeepSeek，或前往「🤖 模型配置」填写 Key。")
                raw_response = await self._call_anthropic(prompt, api_key, model)
                issues = parse_mqm_response(raw_response)
            else:
                api_key, base_url = self._get_api_config(provider)
                if not api_key:
                    raise ValueError(f"{provider.upper()} API Key 未配置。可直接选择已就绪的 DeepSeek，或前往「🤖 模型配置」填写 Key。")
                raw_response = await self._call_openai_compatible(prompt, api_key, base_url, model)
                issues = parse_mqm_response(raw_response)

            # 统计
            severity_counts = {"critical": 0, "major": 0, "minor": 0, "neutral": 0}
            for issue in issues:
                sev = issue.get("severity", "minor")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            return {
                "success": True,
                "segment_id": segment_id,
                "issues": issues,
                "issue_count": len(issues),
                "severity_counts": severity_counts,
                "provider": provider,
                "model": model,
                "raw_response": raw_response,
            }

        except Exception as e:
            logger.error(f"MQM 校对段落 {segment_id} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "segment_id": segment_id,
            }


mqm_review_service = MQMReviewService()
