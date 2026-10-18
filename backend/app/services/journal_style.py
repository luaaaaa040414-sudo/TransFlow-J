"""
期刊风格适配服务 (Journal Style Service)
1. 加载期刊官方指南规范
2. 构建翻译模型约束指令 (Prompt Injection)
3. 翻译后期刊风格合规性复核 (Post-Translation Style Check)
"""
import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 英美拼写差异字典
SPELLING_VARIANTS = {
    # American -> British
    "color": "colour",
    "behavior": "behaviour",
    "flavor": "flavour",
    "labor": "labour",
    "neighbor": "neighbour",
    "analyze": "analyse",
    "catalyze": "catalyse",
    "paralyze": "paralyse",
    "optimize": "optimise",
    "organize": "organise",
    "recognize": "recognise",
    "center": "centre",
    "meter": "metre",
    "fiber": "fibre",
    "defense": "defence",
    "license": "licence",
}

# 反向映射 British -> American
REVERSE_SPELLING = {v: k for k, v in SPELLING_VARIANTS.items()}


class JournalStyleService:

    def build_system_instruction(
        self,
        journal_meta: Dict[str, Any],
        article_type: str = "Research Article",
        terminology_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        根据官方指南构建真正影响模型输出的翻译系统指令
        """
        journal_name = journal_meta.get("name", "未指定期刊")
        variant = journal_meta.get("english_variant", "American")
        rules = journal_meta.get("style_rules") or {}

        parts = [
            f"你是一名资深学术翻译专家与英文同行评议人。",
            f"你的核心任务：将中文学术论文翻译为符合国际顶级期刊规范的高水准学术英文论文。",
            f"",
            f"【目标期刊】{journal_name}",
            f"【文章类型】{article_type}",
            f"【语言规范】严格遵守 {variant} English 拼写与标点规范。",
        ]

        if rules:
            parts.append("【期刊官方作者指南硬性要求】")
            if rules.get("tense"):
                parts.append(f"  * 时态规则：{rules['tense']}")
            if rules.get("voice"):
                parts.append(f"  * 语态倾向：{rules['voice']}")
            if rules.get("abbreviations"):
                parts.append(f"  * 缩写与专有名词：{rules['abbreviations']}")
            if rules.get("citation_style"):
                parts.append(f"  * 引用格式规范：{rules['citation_style']}")
            if rules.get("other"):
                for r in rules.get("other", []):
                    parts.append(f"  * 特殊要求：{r}")

        if terminology_map:
            parts.append("")
            parts.append("【核定学术术语表（强制优先采纳，不得随意替换同义词）】")
            for zh, en in terminology_map.items():
                parts.append(f"  * {zh} => {en}")

        parts.extend([
            "",
            "【学术翻译质量底线要求】",
            "1. 严禁改动原文中的任何具体数值、单位量纲、公式符号。",
            "2. 严禁凭空添加原文不存在的研究推论或实验结论。",
            "3. 如遇专业表述模糊或存疑处，标注 [FLAG: 说明原因]。",
            "4. 务必保留段落标签与句式对应关系。",
        ])

        return "\n".join(parts)

    def check_compliance(
        self,
        source_text: str,
        translated_text: str,
        section: str,
        journal_meta: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        翻译后复核：检查译文是否满足目标期刊语言规范
        """
        violations = []
        if not translated_text:
            return violations

        variant = journal_meta.get("english_variant", "American").lower()
        lower_trans = translated_text.lower()

        # 检查英美拼写一致性
        if "american" in variant:
            for us_word, uk_word in SPELLING_VARIANTS.items():
                # 寻找使用了 British 拼写的情况
                pattern = r"\b" + re.escape(uk_word) + r"\b"
                if re.search(pattern, lower_trans):
                    violations.append({
                        "rule": "Spelling Variant",
                        "severity": "minor",
                        "description": f"期刊要求 American English，检测到英式拼写「{uk_word}」，建议改为「{us_word}」",
                        "expected": us_word,
                        "found": uk_word,
                    })
        elif "british" in variant:
            for us_word, uk_word in SPELLING_VARIANTS.items():
                pattern = r"\b" + re.escape(us_word) + r"\b"
                if re.search(pattern, lower_trans):
                    violations.append({
                        "rule": "Spelling Variant",
                        "severity": "minor",
                        "description": f"期刊要求 British English，检测到美式拼写「{us_word}」，建议改为「{uk_word}」",
                        "expected": uk_word,
                        "found": us_word,
                    })

        # 摘要字数复核
        if "摘要" in section or "abstract" in section.lower():
            limit = journal_meta.get("abstract_word_limit")
            if limit and limit > 0:
                words = re.findall(r"\b\w+\b", translated_text)
                word_count = len(words)
                if word_count > limit:
                    violations.append({
                        "rule": "Abstract Word Limit",
                        "severity": "major",
                        "description": f"摘要译文词数 ({word_count} 词) 超出该期刊上限 ({limit} 词)",
                        "expected": f"<= {limit} words",
                        "found": f"{word_count} words",
                    })

        return violations


journal_style_service = JournalStyleService()
