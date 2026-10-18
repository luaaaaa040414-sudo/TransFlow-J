"""
数据初始化填充脚本 (Database Seeder)
预填常用期刊指南及模型配置，便于开箱即用。
"""
from app.core.database import SessionLocal, create_tables
from app.models.database import Journal, ModelConfig

DEFAULT_JOURNALS = [
    {
        "name": "Nature Communications",
        "abbreviation": "Nat Commun",
        "publisher": "Nature Publishing Group / Springer Nature",
        "issn": "2041-1723",
        "impact_factor": 16.6,
        "domain": "综合科学 / 自然科学",
        "english_variant": "British",
        "abstract_word_limit": 150,
        "citation_style": "Nature (Vancouver-like)",
        "author_guide_url": "https://www.nature.com/ncomms/submit",
        "guide_verified_date": "2024-09",
        "style_rules": {
            "tense": "实验方法使用一般过去式，研究结论使用一般现在式",
            "voice": "鼓励使用简明主动语态 (We demonstrate...) 而非过多冗长被动语态",
            "abbreviations": "正文中首次出现必须给出英文全称并在括号内注明缩写",
            "other": [
                "避免空洞陈述（如 It is well known that）",
                "图表题注须简明独立，不阅读正文亦可理解"
            ]
        }
    },
    {
        "name": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
        "abbreviation": "IEEE TPAMI",
        "publisher": "IEEE Computer Society",
        "issn": "0162-8828",
        "impact_factor": 20.8,
        "domain": "人工智能 / 计算机视觉 / 模式识别",
        "english_variant": "American",
        "abstract_word_limit": 200,
        "citation_style": "IEEE",
        "author_guide_url": "https://www.computer.org/csdl/journal/tp",
        "guide_verified_date": "2024-10",
        "style_rules": {
            "tense": "算法描述使用现在时，实验比较使用过去时",
            "voice": "公式定义需严密，符号在首次出现时说明定义域与物理含义",
            "abbreviations": "标准缩写如 CNN, RNN, GAN 首次出现仍需给出全称",
            "other": [
                "遵循美式拼写规范（如 color, analyze, optimize）",
                "数据集名称需准确标注大小写与版本"
            ]
        }
    },
    {
        "name": "Journal of the American Chemical Society",
        "abbreviation": "JACS",
        "publisher": "American Chemical Society",
        "issn": "0002-7863",
        "impact_factor": 15.0,
        "domain": "化学 / 材料化学",
        "english_variant": "American",
        "abstract_word_limit": 250,
        "citation_style": "ACS",
        "author_guide_url": "https://pubs.acs.org/journal/jacsat",
        "guide_verified_date": "2024-08",
        "style_rules": {
            "tense": "合成步骤用过去时无主被动语态",
            "voice": "学术严谨客观",
            "abbreviations": "IUPAC 化学命名标准"
        }
    },
    {
        "name": "Science",
        "abbreviation": "Science",
        "publisher": "AAAS",
        "issn": "0036-8075",
        "impact_factor": 44.7,
        "domain": "综合科学 / 前沿交叉",
        "english_variant": "American",
        "abstract_word_limit": 125,
        "citation_style": "Science (Numbered)",
        "author_guide_url": "https://www.science.org/content/page/instructions-authors",
        "guide_verified_date": "2024-09",
        "style_rules": {
            "tense": "引言与结论现在时，方法与结果过去时",
            "voice": "鼓励简明直接的学术英语，避免过度专业黑话",
            "abbreviations": "除非极常见缩写，一律首次出现定义"
        }
    },
    {
        "name": "Advanced Materials",
        "abbreviation": "Adv Mater",
        "publisher": "Wiley-VCH",
        "issn": "0935-9648",
        "impact_factor": 27.4,
        "domain": "材料科学 / 纳米技术",
        "english_variant": "American",
        "abstract_word_limit": 200,
        "citation_style": "Wiley",
        "author_guide_url": "https://onlinelibrary.wiley.com/page/journal/15214095/homepage/author-guidelines",
        "guide_verified_date": "2024-07",
        "style_rules": {
            "tense": "制备与表征使用过去时",
            "voice": "客观严谨",
            "abbreviations": "材料学标准表述"
        }
    },
    {
        "name": "The Lancet",
        "abbreviation": "Lancet",
        "publisher": "Elsevier",
        "issn": "0140-6736",
        "impact_factor": 98.4,
        "domain": "临床医学 / 公共卫生",
        "english_variant": "British",
        "abstract_word_limit": 300,
        "citation_style": "Vancouver",
        "author_guide_url": "https://www.thelancet.com/for-authors",
        "guide_verified_date": "2024-08",
        "style_rules": {
            "tense": "临床试验步骤使用过去时，流行病学分析使用客观语气",
            "voice": "英式拼写规范（randomised, hospitalised, behaviour）",
            "abbreviations": "国际医学命名标准"
        }
    },
    {
        "name": "ACM Computing Surveys",
        "abbreviation": "CSUR",
        "publisher": "ACM",
        "issn": "0360-0300",
        "impact_factor": 23.8,
        "domain": "计算机科学 / 综述与系统",
        "english_variant": "American",
        "abstract_word_limit": 200,
        "citation_style": "ACM Reference Format",
        "author_guide_url": "https://dl.acm.org/journal/csur/author-guidelines",
        "guide_verified_date": "2024-06",
        "style_rules": {
            "tense": "系统分类与综述对比使用现在时",
            "voice": "逻辑严密清晰",
            "abbreviations": "专业术语建立完整术语缩写表"
        }
    },
    {
        "name": "IEEE Access",
        "abbreviation": "IEEE Access",
        "publisher": "IEEE",
        "issn": "2169-3536",
        "impact_factor": 3.4,
        "domain": "工程技术 / 电子信息 / 自动化",
        "english_variant": "American",
        "abstract_word_limit": 250,
        "citation_style": "IEEE",
        "author_guide_url": "https://ieeeaccess.ieee.org",
        "guide_verified_date": "2024-10",
        "style_rules": {
            "tense": "算法与架构使用现在时，实验数据使用过去时",
            "voice": "遵循 IEEE Transactions 经典学术规范",
            "abbreviations": "首字母大写规范"
        }
    },
    {
        "name": "SPE Journal",
        "abbreviation": "SPE J",
        "publisher": "Society of Petroleum Engineers (SPE)",
        "issn": "1086-055X",
        "impact_factor": 3.6,
        "domain": "石油与天然气工程 / 深海油气 / 地质工程",
        "english_variant": "American",
        "abstract_word_limit": 300,
        "citation_style": "SPE (Author-Year)",
        "author_guide_url": "https://www.spe.org/en/authors/instructions/",
        "guide_verified_date": "2024-10",
        "style_rules": {
            "tense": "实验与模拟过程使用一般过去时，工程规律与理论模型使用一般现在时",
            "voice": "以客观严谨的学术第三人称和被动语态为主，避免第一人称口语化表达",
            "abbreviations": "首次出现使用全称加括号缩写（如 natural gas hydrate (NGH)、computational fluid dynamics (CFD)）",
            "other": [
                "遵循美式拼写规范（如 color, analyze, modeling）",
                "工程参数严格采用国际标准单位制 (SI units) 并注明量纲",
                "涉及水深、压力、流速等重要工程参数需保留精确有效数字"
            ]
        }
    },
    {
        "name": "Marine and Petroleum Geology",
        "abbreviation": "Mar Pet Geol",
        "publisher": "Elsevier",
        "issn": "0264-8172",
        "impact_factor": 4.2,
        "domain": "海洋地质学 / 天然气水合物 / 深水油气勘探",
        "english_variant": "American",
        "abstract_word_limit": 250,
        "citation_style": "Elsevier (Harvard style)",
        "author_guide_url": "https://www.sciencedirect.com/journal/marine-and-petroleum-geology",
        "guide_verified_date": "2024-09",
        "style_rules": {
            "tense": "地质演化与实验数据分析用过去时，地层构造与区域地质背景用现在时",
            "voice": "第三人称客观叙述",
            "abbreviations": "地层分期与地质构造代号首次出现注明全名"
        }
    },
    {
        "name": "Energy & Fuels",
        "abbreviation": "Energy Fuels",
        "publisher": "American Chemical Society",
        "issn": "0887-0624",
        "impact_factor": 5.2,
        "domain": "化学工程 / 能源与动力 / 油气利用",
        "english_variant": "American",
        "abstract_word_limit": 250,
        "citation_style": "ACS",
        "author_guide_url": "https://pubs.acs.org/journal/enfuem",
        "guide_verified_date": "2024-08",
        "style_rules": {
            "tense": "反应动力学分析用过去时，热力学平衡与物性特征用现在时",
            "voice": "客观严谨",
            "abbreviations": "遵循 ACS 缩写与 IUPAC 命名规范"
        }
    }
]

DEFAULT_MODELS = [
    {
        "name": "DeepSeek-R1 (深度求索最新推理旗舰)",
        "provider": "deepseek",
        "model_id": "deepseek-reasoner",
        "capabilities": ["长链深度思考(CoT)", "极强数理逻辑", "学术论文严密审查", "高性价比"],
        "context_window": 128000,
        "supports_json_mode": True,
        "cost_per_1k_input": 0.00055,
        "cost_per_1k_output": 0.00219,
        "use_for_translation": True,
        "use_for_proofreading": True,
    },
    {
        "name": "DeepSeek-V3 (深度求索通用大模型)",
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "capabilities": ["中文理解极强", "极速响应", "期刊风格适配", "超高性价比"],
        "context_window": 128000,
        "supports_json_mode": True,
        "cost_per_1k_input": 0.00014,
        "cost_per_1k_output": 0.00028,
        "use_for_translation": True,
        "use_for_proofreading": True,
    },
    {
        "name": "Claude 3.7 Sonnet (Anthropic 2025最新旗舰)",
        "provider": "anthropic",
        "model_id": "claude-3-7-sonnet-20250219",
        "capabilities": ["混合思考推理", "顶尖科技学术校对", "细致文风规范", "长上下文"],
        "context_window": 200000,
        "supports_json_mode": False,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "use_for_translation": True,
        "use_for_proofreading": True,
    },
    {
        "name": "Claude 3.5 Sonnet (Anthropic 经典高分审校)",
        "provider": "anthropic",
        "model_id": "claude-3-5-sonnet-20241022",
        "capabilities": ["严谨MQM评审", "地道学术语感", "跨语言细微语病检测"],
        "context_window": 200000,
        "supports_json_mode": False,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "use_for_translation": False,
        "use_for_proofreading": True,
    },
    {
        "name": "GPT-4o (OpenAI 官方通用基座)",
        "provider": "openai",
        "model_id": "gpt-4o",
        "capabilities": ["学术通用写作", "多模态图表理解", "高稳定性"],
        "context_window": 128000,
        "supports_json_mode": True,
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01,
        "use_for_translation": True,
        "use_for_proofreading": True,
    },
    {
        "name": "o3-mini (OpenAI 最新推理基座)",
        "provider": "openai",
        "model_id": "o3-mini",
        "capabilities": ["STEM理工科强推理", "逻辑一致性检验", "高准确度"],
        "context_window": 200000,
        "supports_json_mode": True,
        "cost_per_1k_input": 0.0011,
        "cost_per_1k_output": 0.0044,
        "use_for_translation": True,
        "use_for_proofreading": True,
    },
]


def seed_database():
    create_tables()
    db = SessionLocal()
    try:
        # 填充期刊
        for j_data in DEFAULT_JOURNALS:
            exists = db.query(Journal).filter(Journal.name == j_data["name"]).first()
            if not exists:
                journal = Journal(**j_data)
                db.add(journal)
                print(f"  + 预置期刊：{j_data['name']}")

        # 填充模型
        for m_data in DEFAULT_MODELS:
            exists = db.query(ModelConfig).filter(ModelConfig.name == m_data["name"]).first()
            if not exists:
                m = ModelConfig(**m_data)
                db.add(m)
                print(f"  + 预置模型：{m_data['name']}")

        db.commit()
        print("✅ 初始演示数据填充完毕！")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
