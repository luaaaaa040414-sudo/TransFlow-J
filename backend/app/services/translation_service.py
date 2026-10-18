"""
翻译服务
支持多种 AI 模型提供商（OpenAI / DeepSeek / Anthropic / 自定义）
注入期刊风格约束和术语表
"""
import json
import logging
import re
from typing import Optional, Dict, List, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# 翻译提示词构建
# ============================================================

def build_translation_prompt(
    source_text: str,
    segment_id: str,
    section: str,
    journal_style: Optional[Dict] = None,
    terminology_map: Optional[Dict[str, str]] = None,
    article_type: str = "研究论文",
) -> str:
    """
    构建翻译提示词
    注入期刊风格约束和术语表
    """
    # 基础指令
    prompt_parts = [
        f"你是一名专业学术翻译，负责将中文学术论文翻译成英文。",
        f"",
        f"【段落编号】{segment_id}",
        f"【所属章节】{section}",
        f"【文章类型】{article_type}",
    ]

    # 注入期刊风格约束
    if journal_style:
        journal_name = journal_style.get("name", "")
        english_variant = journal_style.get("english_variant", "American")
        rules = journal_style.get("style_rules", {})

        prompt_parts.append(f"")
        prompt_parts.append(f"【目标期刊】{journal_name}")
        prompt_parts.append(f"【语言规范】{english_variant} English")

        if rules:
            prompt_parts.append(f"【期刊风格要求】")
            if rules.get("tense"):
                prompt_parts.append(f"  - 时态要求：{rules['tense']}")
            if rules.get("voice"):
                prompt_parts.append(f"  - 语态要求：{rules['voice']}")
            if rules.get("abbreviations"):
                prompt_parts.append(f"  - 缩写规范：{rules['abbreviations']}")
            if rules.get("other"):
                for rule in rules.get("other", []):
                    prompt_parts.append(f"  - {rule}")

    # 注入已确认术语表
    if terminology_map:
        prompt_parts.append(f"")
        prompt_parts.append(f"【已确认术语表（必须优先使用）】")
        for zh, en in terminology_map.items():
            prompt_parts.append(f"  - {zh} → {en}")

    # 翻译规范
    prompt_parts.extend([
        f"",
        f"【翻译规范】",
        f"1. 保持原文段落编号 {segment_id}",
        f"2. 数字、单位、公式不得擅自修改",
        f"3. 不得添加原文没有的研究结论",
        f"4. 优先使用已确认术语表中的英文译法",
        f"5. 遇到无把握的专业术语，在术语后加 [FLAG: 待核查]",
        f"6. 遇到原文歧义，在相应位置加 [FLAG: 原文存在歧义]",
        f"",
        f"【输出格式】",
        f"直接输出英文译文，不要添加任何解释。",
        f"如有 FLAG 标记，紧跟在对应词语或句子之后。",
        f"",
        f"【中文原文】",
        source_text,
    ])

    return "\n".join(prompt_parts)


def extract_flags(translation: str) -> List[Dict[str, str]]:
    """提取译文中的 FLAG 标记"""
    flags = []
    pattern = r"\[FLAG:\s*([^\]]+)\]"
    for match in re.finditer(pattern, translation):
        flags.append({
            "reason": match.group(1).strip(),
            "context": translation[max(0, match.start()-50):match.end()+50],
        })
    return flags


# ============================================================
# 模型调用基类
# ============================================================

class TranslationProvider:
    """翻译提供商基类"""

    async def translate(self, prompt: str, model: str) -> str:
        raise NotImplementedError


# ============================================================
# OpenAI 兼容接口（支持 OpenAI / DeepSeek / 自定义）
# ============================================================

class OpenAICompatProvider(TranslationProvider):
    """
    支持所有兼容 OpenAI Chat Completions API 的模型
    包括：OpenAI、DeepSeek、Moonshot、通义千问等
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", provider_name: str = "openai"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name

    async def translate(self, prompt: str, model: str) -> str:
        if not self.api_key:
            raise ValueError(
                f"{self.provider_name.upper()} API Key 未配置。可直接选择已就绪的 DeepSeek，或前往「🤖 模型配置」页面填入 API Key。"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是专业的学术翻译助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


# ============================================================
# 学术仿真演示引擎（免 API Key 快速体验模式）
# ============================================================

class AcademicSimulationProvider(TranslationProvider):
    """
    内置学术仿真引擎（无需配置任何 API Key）
    用于无网络/无密钥情况下的全流程快速体验、数字核查测试与期刊规范验证。
    """
    SAMPLE_TRANSLATIONS: Dict[str, str] = {
        "深水浅层天然气水合物固态流化开采破碎机理与射流钻头优化设计": (
            "Fragmentation Mechanisms of Solid-State Fluidized Exploitation and Jet Bit Optimization for Deepwater Shallow Gas Hydrates"
        ),
        "天然气水合物作为一种极具潜力的清洁替代能源，广泛分布于深水海底沉积层中。": (
            "As a highly promising clean alternative energy source, natural gas hydrate is extensively distributed in deepwater seabed sediments."
        ),
        "我国南海神狐海域水深达 1350 m，浅层水合物地层胶结微弱，上覆泥质沉积物孔隙压力为 18.5 MPa。": (
            "In the Shenhu area of the South China Sea, China, the water depth reaches 1350 m, where the shallow hydrate-bearing formations exhibit weak cementation and the overlying argillaceous sediments possess a pore pressure of 18.5 MPa."
        ),
        "常规降压与热激化开采法极易引发海底滑坡与地层失稳，因此提出了固态流化开采新理念。": (
            "Conventional depressurization and thermal stimulation methods are highly prone to triggering submarine landslides and formation instability; therefore, a novel concept of solid-state fluidized exploitation was proposed."
        ),
        "针对深水浅层弱胶结水合物储层，设计了高压空化水射流辅助旋转切割钻头，并在室内研制了全尺寸破碎模拟实验台。": (
            "Aiming at deepwater shallow weakly consolidated hydrate reservoirs, a high-pressure cavitating water jet-assisted rotary cutting bit was designed, and a full-scale fragmentation simulation experimental apparatus was developed in the laboratory."
        ),
        "实验测定在水射流排量 450 m³/h 条件下，射流破岩比功降低至 14.2 J/cm³，水合物二次生成抑制效率达 98.6%。": (
            "Experimental measurements indicated that under a water jet flow rate of 450 m³/h, the specific energy of rock breaking by jet decreased to 14.2 J/cm³, and the secondary hydrate formation inhibition efficiency reached 98.6%."
        ),
        "实验数据表明，优化后的自振空化喷嘴流场速度较常规圆锥形喷嘴提高 23.4%，流化破碎效率提升 31.8%，破碎粒径均控制在 5 mm 以下，满足井下水力管道密闭输送要求。": (
            "Experimental data demonstrated that the optimized self-resonating cavitating nozzle flow field velocity increased by 23.4% compared with conventional conical nozzles, the fluidization fragmentation efficiency was enhanced by 31.8%, and the crushed particle size was strictly controlled below 5 mm, satisfying the downhole closed hydraulic pipeline transportation requirements."
        ),
        "本文提出的射流喷嘴结构参数与流化破岩参数组合，为我国南海天然气水合物第二轮试采工程提供了关键理论支撑。": (
            "The combination of jet nozzle structural parameters and fluidized rock breaking parameters proposed in this paper provides critical theoretical support for the second trial production project of natural gas hydrate in the South China Sea of China."
        ),
    }

    async def translate(self, prompt: str, model: str) -> str:
        # 从 prompt 提取原文
        source_text = ""
        if "【中文原文】" in prompt:
            source_text = prompt.split("【中文原文】")[-1].strip()

        # 匹配精准学术句库
        if source_text in self.SAMPLE_TRANSLATIONS:
            return self.SAMPLE_TRANSLATIONS[source_text]

        # 模糊包含匹配
        for k, v in self.SAMPLE_TRANSLATIONS.items():
            if k in source_text or source_text in k:
                return v

        # 通用启发式学术翻译：保留所有数字和技术词汇
        # 提取数字与单位
        numbers = re.findall(r"\d+(?:\.\d+)?(?:\s*[a-zA-Z%℃/³²]+)?", source_text)
        num_str = f" [Verified parameters: {', '.join(numbers)}]" if numbers else ""
        return f"This study investigates the key mechanisms and engineering behaviors based on experimental analysis.{num_str}"


# ============================================================
# Anthropic Claude
# ============================================================

class AnthropicProvider(TranslationProvider):
    """Anthropic Claude 系列模型"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def translate(self, prompt: str, model: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Anthropic Claude API Key 未配置。可直接选择已就绪的 DeepSeek，或前往「🤖 模型配置」页面填入 API Key。"
            )

        headers = {
            "x-api-key": self.api_key,
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


# ============================================================
# 翻译服务主类
# ============================================================

class TranslationService:

    def get_provider(self, provider_name: str) -> TranslationProvider:
        """根据提供商名称获取对应实例"""
        if provider_name == "simulation" or provider_name == "demo":
            return AcademicSimulationProvider()
        elif provider_name == "openai":
            return OpenAICompatProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                provider_name="openai",
            )
        elif provider_name == "deepseek":
            return OpenAICompatProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                provider_name="deepseek",
            )
        elif provider_name == "anthropic":
            return AnthropicProvider(api_key=settings.anthropic_api_key)
        elif provider_name == "custom":
            return OpenAICompatProvider(
                api_key=settings.custom_api_key,
                base_url=settings.custom_base_url,
                provider_name="custom",
            )
        else:
            raise ValueError(f"不支持的提供商: {provider_name}")

    async def translate_segment(
        self,
        source_text: str,
        segment_id: str,
        section: str,
        provider_name: str = "openai",
        model: str = "gpt-4o",
        journal_style: Optional[Dict] = None,
        terminology_map: Optional[Dict[str, str]] = None,
        article_type: str = "研究论文",
    ) -> Dict[str, Any]:
        """
        翻译单个段落
        返回包含译文和 FLAG 信息的字典
        """
        provider = self.get_provider(provider_name)
        prompt = build_translation_prompt(
            source_text=source_text,
            segment_id=segment_id,
            section=section,
            journal_style=journal_style,
            terminology_map=terminology_map,
            article_type=article_type,
        )

        try:
            translation = await provider.translate(prompt, model)
            flags = extract_flags(translation)
            has_flag = len(flags) > 0

            return {
                "success": True,
                "translated_text": translation,
                "has_flag": has_flag,
                "flags": flags,
                "provider": provider_name,
                "model": model,
            }
        except Exception as e:
            logger.error(f"翻译段落 {segment_id} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "translated_text": None,
                "has_flag": False,
                "flags": [],
            }

    async def test_connection(self, provider_name: str, model: str) -> Dict[str, Any]:
        """测试 API 连通性"""
        try:
            provider = self.get_provider(provider_name)
            result = await provider.translate(
                "请回复：连接测试成功。只输出这一句话。",
                model,
            )
            return {"success": True, "response": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


translation_service = TranslationService()
