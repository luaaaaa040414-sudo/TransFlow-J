"""
质量检查服务 - 确定性规则检查（不依赖大模型）
检查项目：数字一致性、术语一致性、段落编号、格式完整性
"""
import re
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


# ============================================================
# 数字提取工具
# ============================================================

# 匹配数字（整数、小数、百分数、科学计数法）
# 匹配数字（支持千分位逗号如 250,000，且连字符不误判为负号）
NUMBER_PATTERN = re.compile(
    r"""
    (?<![a-zA-Z\d])-?          # 负号只在非字母非数字前有效
    (?:
        \d{1,3}(?:,\d{3})+     # 带千分位逗号的数字，如 250,000 或 1,573
        |
        \d+\.?\d*              # 普通整数或小数
        (?:[eE][+-]?\d+)?      # 科学计数法
    )
    \s*%?                      # 可选百分号
    """,
    re.VERBOSE,
)

# 中文数字映射（简单处理）
ZH_NUM_MAP = {
    "零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
    "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
    "十": "10", "百": "100", "千": "1000", "万": "10000",
}


def extract_numbers(text: str) -> List[str]:
    """从文本中提取所有数字字符串，清洗千分位逗号"""
    numbers = NUMBER_PATTERN.findall(text)
    clean = []
    for n in numbers:
        s = n.strip().replace(",", "")
        if s:
            clean.append(s)
    return clean


def normalize_number(num_str: str) -> Optional[float]:
    """将数字字符串归一化为 float，处理百分数"""
    try:
        s = num_str.strip().rstrip("%").strip()
        return float(s)
    except (ValueError, TypeError):
        return None


# ============================================================
# 数字格式化与语言学匹配常量
# ============================================================

def format_num_display(val: float) -> str:
    """美化数字展示，避免 58.0 这种不符合人类直觉的浮点显示"""
    if val == int(val):
        return str(int(val))
    return str(val)


MONTH_WORDS = {
    1: ["january", "jan"],
    2: ["february", "feb"],
    3: ["march", "mar"],
    4: ["april", "apr"],
    5: ["may"],
    6: ["june", "jun"],
    7: ["july", "jul"],
    8: ["august", "aug"],
    9: ["september", "sep", "sept"],
    10: ["october", "oct"],
    11: ["november", "nov"],
    12: ["december", "dec"],
}

WORD_NUMBERS = {
    1: ["one", "first", "1st"],
    2: ["two", "second", "2nd", "twice"],
    3: ["three", "third", "3rd"],
    4: ["four", "fourth", "4th"],
    5: ["five", "fifth", "5th"],
    6: ["six", "sixth", "6th"],
    7: ["seven", "seventh", "7th"],
    8: ["eight", "eighth", "8th"],
    9: ["nine", "ninth", "9th"],
    10: ["ten", "tenth", "10th"],
    14: ["fourteen", "14th"],
    15: ["fifteen", "15th"],
    20: ["twenty", "20th"],
    25: ["twenty-five", "25th"],
    50: ["fifty", "50th"],
    60: ["sixty", "60th"],
    64: ["sixty-four"],
    68: ["sixty-eight"],
}


# ============================================================
# 数字一致性检查
# ============================================================

class NumberConsistencyChecker:

    def check(self, source_text: str, translated_text: str) -> List[Dict[str, Any]]:
        """
        检查原文和译文中的数字是否一致
        智能支持：
        1. 月份对应（例如 9月 -> September, 11月 -> November）
        2. 两位数年份/年级推演（例如 58级/58年 -> 1958, 93届 -> 1993）
        3. 万字单位转换（例如 25万 -> 250,000）
        4. 常用英文数字单词（例如 two, three, four）
        5. 去除 [S001] 或 [FLAG] 标签干扰
        """
        issues = []
        if not translated_text:
            return issues

        # 清洗译文中的段落标签如 [S001]、[FLAG: ...]
        clean_target = re.sub(r"\[S\d+\]", "", translated_text)
        clean_target = re.sub(r"\[FLAG:[^\]]+\]", "", clean_target)
        target_lower = clean_target.lower()

        src_numbers = extract_numbers(source_text)
        tgt_numbers = extract_numbers(clean_target)

        # 归一化后比较
        src_normalized = set()
        for n in src_numbers:
            v = normalize_number(n)
            if v is not None:
                src_normalized.add(v)

        tgt_normalized = set()
        for n in tgt_numbers:
            v = normalize_number(n)
            if v is not None:
                tgt_normalized.add(v)

        # 检查原文数字是否在译文中被有效表达
        missing = set()
        for val in (src_normalized - tgt_normalized):
            int_val = int(val) if val == int(val) else None
            satisfied = False

            # 1. 月份识别：例如 9月 -> September, 08月/8月 -> August, 11月 -> November
            if int_val in MONTH_WORDS:
                if re.search(rf"(?<!\d)0?{int_val}\s*月", source_text):
                    for mw in MONTH_WORDS[int_val]:
                        if re.search(rf"\b{mw}\b", target_lower):
                            satisfied = True
                            break

            # 2. 两位数年份/年级/届次：例如 58级/58年 -> 1958, 93届 -> 1993
            if not satisfied and int_val is not None and 10 <= int_val <= 99:
                if re.search(rf"(?<!\d){int_val}\s*(?:年|级|届|代)", source_text):
                    full_yr = 1900 + int_val if int_val >= 30 else 2000 + int_val
                    if float(full_yr) in tgt_normalized or f"'{int_val}" in clean_target:
                        satisfied = True

            # 3. 英文数字词：例如 2 -> two, 3 -> three, 5 -> five
            if not satisfied and int_val in WORD_NUMBERS:
                for wn in WORD_NUMBERS[int_val]:
                    if re.search(rf"\b{wn}\b", target_lower):
                        satisfied = True
                        break

            # 4. 万单位：例如 20万/20余万 -> 200,000, 25万 -> 250,000
            if not satisfied and int_val is not None:
                if re.search(rf"(?<!\d){int_val}\s*(?:余|多|几)?\s*万", source_text):
                    wan_val = float(int_val * 10000)
                    if (
                        wan_val in tgt_normalized
                        or f"{int_val * 10} thousand" in target_lower
                        or f"{int_val * 10}k" in target_lower
                        or f"{int_val * 10},000" in clean_target
                    ):
                        satisfied = True

            # 5. 亿单位转换：例如 200亿 -> 20 billion, 10亿 -> 1 billion, 1亿 -> 100 million
            if not satisfied and int_val is not None:
                if re.search(rf"(?<!\d){int_val}\s*(?:余|多|几)?\s*亿", source_text):
                    billion_val = float(int_val / 10)
                    million_val = float(int_val * 100)
                    full_yi = float(int_val * 100000000)
                    if (
                        (billion_val in tgt_normalized and "billion" in target_lower)
                        or (million_val in tgt_normalized and "million" in target_lower)
                        or full_yi in tgt_normalized
                    ):
                        satisfied = True

            if not satisfied:
                missing.add(val)

        for val in missing:
            val_display = format_num_display(val)
            issues.append({
                "type": "number_missing",
                "severity": "major",
                "description": f"原文中的数字 {val_display} 在译文中未出现",
                "source_numbers": src_numbers,
                "target_numbers": tgt_numbers,
            })

        # 译文多出的数字检查
        extra = set()
        zh_to_num = {
            "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
            "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
            "二十": 20, "三十": 30, "四十": 40, "五十": 50, "六十": 60,
            "七十": 70, "八十": 80, "九十": 90, "一百": 100,
        }

        for val in (tgt_normalized - src_normalized):
            # 排除合理情况：
            # 1. 合理的四位年份（如 1900~2035）由原文两位年扩展而来
            if 1900 <= val <= 2035:
                short_yr = float(int(val) % 100)
                if short_yr in src_normalized and re.search(rf"(?<!\d){int(short_yr)}\s*(?:年|级|届)", source_text):
                    continue
                if (val == 1980.0 or val == 80.0) and "八十年代" in source_text:
                    continue
                if (val == 1950.0 or val == 50.0) and "50年代" in source_text:
                    continue
            # 2. 万字单位展开（如 250000 对应原文 25万）
            if val >= 10000 and (val / 10000) in src_normalized:
                continue
            # 3. 中文汉字数字在英文中写为阿拉伯数字（如 六十余年 -> 60, 十大 -> 10, 十五大 -> 15）
            int_extra = int(val) if val == int(val) else None
            if int_extra in zh_to_num.values() and any(zh in source_text for zh, n in zh_to_num.items() if n == int_extra):
                continue
            # 4. 序数词与常见分类标号（如 step 1, phase 2）
            if val in (1.0, 2.0, 3.0) and any(kw in target_lower for kw in ["part", "phase", "stage", "step"]):
                continue
            # 5. 亿单位对应（如 20 billion 对应原文 200亿；100 million 对应原文 1亿）
            src_yi_b = val * 10
            if src_yi_b in src_normalized and re.search(rf"(?<!\d){int(src_yi_b)}\s*亿", source_text) and "billion" in target_lower:
                continue
            src_yi_m = val / 100
            if src_yi_m in src_normalized and re.search(rf"(?<!\d){int(src_yi_m)}\s*亿", source_text) and "million" in target_lower:
                continue
            if val >= 100000000 and (val / 100000000) in src_normalized:
                continue

            extra.add(val)

        for val in extra:
            val_display = format_num_display(val)
            issues.append({
                "type": "number_extra",
                "severity": "minor",
                "description": f"译文中出现了原文没有的数字 {val_display}",
                "source_numbers": src_numbers,
                "target_numbers": tgt_numbers,
            })

        return issues


# ============================================================
# 术语一致性检查
# ============================================================

class TerminologyConsistencyChecker:

    def check_project_segments(
        self,
        segments: List[Dict],
        terminology_map: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        检查整个项目的术语一致性
        returns: { "consistent_count": N, "total_count": N, "rate": 0.xx, "issues": [...] }
        """
        issues = []
        total_occurrences = 0
        consistent_occurrences = 0

        for seg in segments:
            source = seg.get("source_text", "")
            translated = seg.get("translated_text", "") or ""
            seg_id = seg.get("segment_id", "?")

            for zh_term, en_term in terminology_map.items():
                if zh_term in source:
                    total_occurrences += 1
                    # 检查英文术语是否出现在译文中（不区分大小写）
                    if en_term.lower() in translated.lower():
                        consistent_occurrences += 1
                    else:
                        issues.append({
                            "segment_id": seg_id,
                            "zh_term": zh_term,
                            "expected_en": en_term,
                            "description": f"段落 {seg_id} 含有术语「{zh_term}」但译文中未使用约定译法「{en_term}」",
                        })

        rate = consistent_occurrences / total_occurrences if total_occurrences > 0 else 1.0
        return {
            "consistent_count": consistent_occurrences,
            "total_count": total_occurrences,
            "rate": round(rate, 4),
            "issues": issues,
        }

    def check_single_segment(
        self,
        source_text: str,
        translated_text: str,
        terminology_map: Dict[str, str],
        segment_id: str = "?",
    ) -> List[Dict]:
        """检查单个段落的术语一致性"""
        issues = []
        for zh_term, en_term in terminology_map.items():
            if zh_term in source_text and translated_text:
                if en_term.lower() not in translated_text.lower():
                    issues.append({
                        "segment_id": segment_id,
                        "zh_term": zh_term,
                        "expected_en": en_term,
                        "description": f"术语「{zh_term}」应译为「{en_term}」",
                    })
        return issues


# ============================================================
# 段落编号完整性检查
# ============================================================

class SegmentIntegrityChecker:

    def check_numbering(self, segments: List[Dict]) -> List[Dict]:
        """检查段落编号是否连续、无遗漏"""
        issues = []
        expected_ids = [f"S{i+1:03d}" for i in range(len(segments))]
        actual_ids = [s.get("segment_id", "") for s in segments]

        for expected, actual in zip(expected_ids, actual_ids):
            if expected != actual:
                issues.append({
                    "type": "segment_id_mismatch",
                    "severity": "minor",
                    "expected": expected,
                    "actual": actual,
                })

        return issues

    def check_empty_translations(self, segments: List[Dict]) -> List[Dict]:
        """检查是否存在未翻译的段落"""
        issues = []
        for seg in segments:
            if not seg.get("translated_text") and seg.get("status") not in ("pending",):
                issues.append({
                    "type": "missing_translation",
                    "severity": "major",
                    "segment_id": seg.get("segment_id"),
                    "description": f"段落 {seg.get('segment_id')} 缺少译文",
                })
        return issues


# ============================================================
# 统一质量检查入口
# ============================================================

class QualityChecker:

    def __init__(self):
        self.number_checker = NumberConsistencyChecker()
        self.term_checker = TerminologyConsistencyChecker()
        self.integrity_checker = SegmentIntegrityChecker()

    def check_segment(
        self,
        source_text: str,
        translated_text: str,
        segment_id: str,
        terminology_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """检查单个段落"""
        result = {
            "segment_id": segment_id,
            "number_issues": [],
            "terminology_issues": [],
            "passed": True,
        }

        # 数字检查
        num_issues = self.number_checker.check(source_text, translated_text)
        result["number_issues"] = num_issues

        # 术语检查
        if terminology_map:
            term_issues = self.term_checker.check_single_segment(
                source_text, translated_text, terminology_map, segment_id
            )
            result["terminology_issues"] = term_issues

        result["passed"] = (
            len(num_issues) == 0 and len(result.get("terminology_issues", [])) == 0
        )
        return result

    def generate_project_report(
        self,
        segments: List[Dict],
        terminology_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """生成项目级质量报告"""
        total = len(segments)
        translated = sum(1 for s in segments if s.get("translated_text"))
        approved = sum(1 for s in segments if s.get("status") == "approved")
        flagged = sum(1 for s in segments if s.get("has_flag"))

        # 数字检查
        total_number_errors = 0
        number_issues_detail = []
        for seg in segments:
            if seg.get("translated_text"):
                num_issues = self.number_checker.check(
                    seg.get("source_text", ""),
                    seg.get("translated_text", ""),
                )
                total_number_errors += len([i for i in num_issues if i["type"] == "number_missing"])
                number_issues_detail.extend([{**i, "segment_id": seg.get("segment_id")} for i in num_issues])

        # 术语一致性检查
        term_result = {}
        if terminology_map and translated > 0:
            translated_segs = [s for s in segments if s.get("translated_text")]
            term_result = self.term_checker.check_project_segments(translated_segs, terminology_map)

        # 人工修改率（判断初始译文和当前译文是否不同）
        edited_count = sum(
            1 for s in segments
            if s.get("initial_translation") and s.get("translated_text") != s.get("initial_translation")
        )
        human_edit_rate = edited_count / translated if translated > 0 else 0

        return {
            "total_segments": total,
            "translated_segments": translated,
            "approved_segments": approved,
            "flagged_segments": flagged,
            "number_errors": total_number_errors,
            "number_issues_detail": number_issues_detail,
            "terminology_consistency_rate": term_result.get("rate"),
            "terminology_issues": term_result.get("issues", []),
            "human_edit_rate": round(human_edit_rate, 4),
            "integrity_issues": self.integrity_checker.check_numbering(segments),
        }


quality_checker = QualityChecker()
