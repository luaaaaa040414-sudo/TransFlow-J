<template>
  <div class="apple-intro-view">
    <!-- ============================================================
         1. Apple Flagship Hero Keynote
         ============================================================ -->
    <section class="hero-section">
      <div class="hero-eyebrow">
        <span class="eyebrow-pill">A0–D5 全流程学术闭环</span>
        <span class="eyebrow-pill subtle">4套刚性约束 · 0误差确定性门禁</span>
      </div>

      <h1 class="hero-title">
        学术之严，字句立见。<br />
        <span class="hero-title-gradient">面向学术顶刊与学位论文的翻译质量保障体系。</span>
      </h1>

      <p class="hero-subtitle">
        专为 SCI/EI 顶刊学术论文发表与高规格学术文献深度定制。以译前四件套刚性约束为筑基，深度融合 Python 确定性数字零容忍门禁、跨厂商异构模型 MQM 独立互审与导师决策闭环，彻底终结通用大模型“术语幻觉”、“数字翻倍”与“风格漂移”，让每一句学术表达都经得起同行评审与可复现检验。
      </p>

      <!-- Apple Action Pill Buttons -->
      <div class="hero-actions">
        <router-link to="/workspace" class="apple-btn-primary">
          <span>进入翻译工作台</span>
          <span class="btn-arrow">↗</span>
        </router-link>
        <router-link to="/journals" class="apple-btn-secondary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <span>查阅 11 本顶刊规范</span>
        </router-link>
        <a href="#methodology" class="apple-btn-subtle">
          <span>探索 A0–D5 方法论</span>
          <span class="btn-arrow">↓</span>
        </a>
      </div>

      <!-- Hero Live Interface Showcase (Apple Frosted Glass Frame) -->
      <div class="hero-showcase-window">
        <div class="showcase-titlebar">
          <div class="window-controls">
            <span class="ctrl-dot red"></span>
            <span class="ctrl-dot yellow"></span>
            <span class="ctrl-dot green"></span>
          </div>
          <div class="window-address">
            <span class="lock-icon">🔒</span>
            <span class="address-text">academic-qa.engine // A0-D5 Pipeline Inspection</span>
          </div>
          <div class="window-badges">
            <span class="status-tag live">LIVE DEMO</span>
          </div>
        </div>

        <div class="showcase-content">
          <!-- Left: Source & Constraint Injection -->
          <div class="showcase-pane">
            <div class="pane-header">
              <span class="pane-tag">CHINESE SOURCE & CONSTRAINTS</span>
              <span class="domain-tag">石油天然气工程 · 水合物开采</span>
            </div>
            <div class="source-bubble">
              “深水浅层天然气水合物固态流化开采储层改造体积达到 <span class="highlight-num">200 亿</span> 立方米，井底流压稳定在 <span class="highlight-num">15.4 MPa</span>。”
            </div>
            <div class="constraints-bar">
              <div class="constraint-pill">
                <span class="cp-icon">📄</span>
                <span>Brief: SPE 实验研究论文</span>
              </div>
              <div class="constraint-pill">
                <span class="cp-icon">🔍</span>
                <span>Term: 固态流化开采 (SPE 权威证据卡)</span>
              </div>
              <div class="constraint-pill">
                <span class="cp-icon">📐</span>
                <span>Style: SPE Journal 现行主动语态</span>
              </div>
            </div>
          </div>

          <!-- Middle Divider with Engine Arrow -->
          <div class="showcase-divider">
            <div class="engine-badge">
              <span class="engine-icon">⚙️</span>
              <span class="engine-text">A0-D5 引擎</span>
            </div>
          </div>

          <!-- Right: Verified English Translation & Zero-Error Check -->
          <div class="showcase-pane right-pane">
            <div class="pane-header">
              <span class="pane-tag">ACADEMIC ENGLISH OUTPUT</span>
              <span class="verified-tag">✓ 0 误差差分通过</span>
            </div>
            <div class="target-bubble">
              “The stimulated reservoir volume in solid fluidization exploitation of deep-water shallow gas hydrate reached <span class="highlight-num-pass">20 billion</span> m³, with bottom-hole flowing pressure stabilizing at <span class="highlight-num-pass">15.4 MPa</span>.”
            </div>
            <div class="audit-summary-strip">
              <div class="audit-stat pass">
                <span class="stat-dot green"></span>
                <span>确定性数字差分: 0 误差 (200亿 ↔ 20 billion)</span>
              </div>
              <div class="audit-stat mqm">
                <span class="stat-dot blue"></span>
                <span>DeepSeek-R1 独立互审: 扣分 0 (无阻断项)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         2. Paradigm Shift: Naive AI vs Academic QA Engine
         ============================================================ -->
    <section class="comparison-section">
      <div class="section-badge">PARADIGM SHIFT</div>
      <h2 class="section-title">为什么学术翻译绝不能依靠大模型“盲译”？</h2>
      <p class="section-desc">
        通用大模型在学术语境中存在天然的“黑盒幻觉”与“格式失控”。学术中译英必须从随机生成迈向精密工程。
      </p>

      <div class="comparison-grid">
        <!-- Negative Card: Naive AI Translation -->
        <div class="compare-card negative">
          <div class="card-status-badge neg-badge">❌ 传统大模型直接生成（通用盲译）</div>
          <h3 class="card-headline">不可控、易失真、无法溯源</h3>
          <ul class="compare-points">
            <li>
              <div class="point-icon">⚠️</div>
              <div class="point-detail">
                <strong>核心术语幻觉脱节</strong>
                <p>缺乏强制术语表与权威证据卡，同一关键变量与专有名词前后数段译法截然矛盾。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">⚠️</div>
              <div class="point-detail">
                <strong>数字与量级翻倍灾难</strong>
                <p>无纯代码门禁，“200亿”常被直接直译为“200 billion”，造成整整 10 倍级重大科研数据事故。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">⚠️</div>
              <div class="point-detail">
                <strong>期刊投稿风格失调</strong>
                <p>无法自动遵循 Nature/SPE 等顶刊关于主动语态、时态、缩略语界定及法定计量单位的硬性规范。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">⚠️</div>
              <div class="point-detail">
                <strong>黑盒黑箱无法答辩</strong>
                <p>无法导出 audit log 与 decisions 决策日志，无法满足学术硕士 (MTI) 毕业论文与期刊同行的可复现要求。</p>
              </div>
            </li>
          </ul>
        </div>

        <!-- Positive Card: Academic QA Platform -->
        <div class="compare-card positive">
          <div class="card-status-badge pos-badge">✅ 本平台 A0–D5 全流程闭环工程</div>
          <h3 class="card-headline">全约束、零误差、权威复现</h3>
          <ul class="compare-points">
            <li>
              <div class="point-icon">🛡️</div>
              <div class="point-detail">
                <strong>译前四件套刚性约束注入</strong>
                <p>翻译前先确立 Brief 纲要、权威机构 URL 证据卡、目标期刊指南与数字专名规则，源头消灭幻觉。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">🛡️</div>
              <div class="point-detail">
                <strong>确定性数字差分零容忍</strong>
                <p>由纯 Python 正则硬规则门禁逐句扫描，中英文计数（万/亿 ↔ million/billion）不匹配直接阻断。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">🛡️</div>
              <div class="point-detail">
                <strong>跨厂商异构模型独立互审</strong>
                <p>生成与校对彻底解耦，引入第三方独立视角（如 DeepSeek-R1）进行 MQM 细粒度标注与三级严重度分级。</p>
              </div>
            </li>
            <li>
              <div class="point-icon">🛡️</div>
              <div class="point-detail">
                <strong>论文章节映射与完整复现包</strong>
                <p>全周期自动记录 decisions.json，过程数据天然对齐学位论文 Ch2-Ch4 章节，一键导出可复现成果。</p>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ============================================================
         3. A0–D5 Full Lifecycle Methodology Roadmap
         ============================================================ -->
    <section id="methodology" class="methodology-section">
      <div class="section-badge">METHODOLOGY ROADMAP</div>
      <h2 class="section-title">A0–D5 二十二步全生命周期方法论</h2>
      <p class="section-desc">
        将人类资深学术译者的严谨思辨固化为四大阶段、二十二个标准化工程节点的流水线闭环。
      </p>

      <div class="phases-ladder">
        <!-- Phase A -->
        <div class="phase-card">
          <div class="phase-header">
            <span class="phase-num">PHASE A</span>
            <span class="phase-title">译前四件套地基工程</span>
          </div>
          <p class="phase-summary">在翻译任何一个段落前，筑牢坚不可摧的背景与术语约束。</p>
          <div class="step-chips">
            <div class="step-chip"><strong>A0</strong> 论文需求与读者界定</div>
            <div class="step-chip"><strong>A1</strong> 权威术语库与证据卡</div>
            <div class="step-chip"><strong>A2</strong> 目标顶刊指南规范库</div>
            <div class="step-chip"><strong>A3</strong> 数字与专名正则规则</div>
            <div class="step-chip"><strong>A4</strong> 译前四件套基线冻结</div>
          </div>
        </div>

        <!-- Phase B -->
        <div class="phase-card">
          <div class="phase-header">
            <span class="phase-num">PHASE B</span>
            <span class="phase-title">随译自查与随行质保</span>
          </div>
          <p class="phase-summary">动态注入约束提示词，纯代码实时监控数值，疑难句即时 FLAG 标记。</p>
          <div class="step-chips">
            <div class="step-chip"><strong>B1</strong> 四件套 Prompt 动态注入</div>
            <div class="step-chip"><strong>B2</strong> 确定性数字差分即时监控</div>
            <div class="step-chip"><strong>B3</strong> 专有名词一致性校验</div>
            <div class="step-chip"><strong>B4</strong> 疑难长难句 FLAG 标记</div>
            <div class="step-chip"><strong>B5</strong> 导师集中答疑与批注闭环</div>
          </div>
        </div>

        <!-- Phase C -->
        <div class="phase-card">
          <div class="phase-header">
            <span class="phase-num">PHASE C</span>
            <span class="phase-title">跨厂商独立视角 MQM 互审</span>
          </div>
          <p class="phase-summary">翻译与校对解耦，跨模型独立视角进行多维细粒度标注与罚分统计。</p>
          <div class="step-chips">
            <div class="step-chip"><strong>C1</strong> 异构模型独立初审 (DeepSeek-R1)</div>
            <div class="step-chip"><strong>C2</strong> MQM 国际学术框架标注</div>
            <div class="step-chip"><strong>C3</strong> 🔴阻断/🟠重要/🟡轻微分级</div>
            <div class="step-chip"><strong>C4</strong> 严谨修改建议与论证理由</div>
            <div class="step-chip"><strong>C5</strong> 自动扣分与质量门禁判定</div>
          </div>
        </div>

        <!-- Phase D -->
        <div class="phase-card">
          <div class="phase-header">
            <span class="phase-num">PHASE D</span>
            <span class="phase-title">决策闭环与学位成果交付</span>
          </div>
          <p class="phase-summary">三表同步，全流程审计记录，无缝对接学术论文 Ch2–Ch4 与复现归档。</p>
          <div class="step-chips">
            <div class="step-chip"><strong>D1</strong> 导师终审与裁决采纳</div>
            <div class="step-chip"><strong>D2</strong> 中英双语对照与纯英定稿导出</div>
            <div class="step-chip"><strong>D3</strong> decisions.json 全周期决策溯源</div>
            <div class="step-chip"><strong>D4</strong> 毕业论文 Ch2-Ch4 成果映射</div>
            <div class="step-chip"><strong>D5</strong> 包含四件套的可复现归档包</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         4. Four Core Engineering Innovations (Apple Bento Grid)
         ============================================================ -->
    <section class="bento-section">
      <div class="section-badge">ENGINEERING CORE</div>
      <h2 class="section-title">四大工程创新。重构学术翻译标准。</h2>
      <p class="section-desc">每一处交互，每一个模块，皆为解决学术翻译中的核心痛点而生。</p>

      <div class="bento-grid">
        <!-- Bento 1: 译前四件套 -->
        <div class="bento-card bento-card-large">
          <div class="bento-inner">
            <div class="bento-badge">01 · 约束筑基</div>
            <h3 class="bento-heading">译前四件套刚性约束注入</h3>
            <p class="bento-paragraph">
              绝不在没有上下文的情况下翻译任何一句学术文本。翻译发起时，系统自动组装 <strong>brief.md</strong>、<strong>terms.json</strong>（含权威 URL 证据卡）、<strong>style.md</strong> 与 <strong>numbers.md</strong>，将其作为首要不可动摇的系统级硬约束。
            </p>
            <div class="bento-tags-cloud">
              <span class="cloud-pill">📄 论文背景与读者定位</span>
              <span class="cloud-pill">🏛️ 全国科技名词审定委员会信源</span>
              <span class="cloud-pill">📚 11本顶刊时态/语态规则</span>
              <span class="cloud-pill">🔢 万/亿/billion 专名正则</span>
            </div>
          </div>
          <div class="bento-preview-box">
            <div class="preview-mini-header">
              <span class="code-dot"></span>
              <span class="code-title">Four-Pillar Constraint Context</span>
            </div>
            <pre class="preview-mini-code"><code>{
  "project_brief": "深水水合物固态流化开采",
  "journal_guide": "SPE Journal (Active, SI)",
  "evidence_terms": 38,
  "unit_rule": "Strict IEEE/Nature Format"
}</code></pre>
          </div>
        </div>

        <!-- Bento 2: 确定性零误差数字门禁 -->
        <div class="bento-card">
          <div class="bento-inner">
            <div class="bento-badge">02 · 规则引擎</div>
            <h3 class="bento-heading">确定性零误差数字与单位门禁</h3>
            <p class="bento-paragraph">
              脱离大模型飘忽不定的主观概率，采用纯 Python 正则与数值差分引擎对每一句原文与译文进行严格数学比对。
            </p>
            <div class="metric-block">
              <div class="metric-num">0 <span class="metric-unit">误差</span></div>
              <div class="metric-desc">万/亿与 million/billion 等价换算零容忍</div>
            </div>
          </div>
        </div>

        <!-- Bento 3: 跨厂商多模型 MQM 独立互审 -->
        <div class="bento-card">
          <div class="bento-inner">
            <div class="bento-badge">03 · 异构审计</div>
            <h3 class="bento-heading">跨厂商异构模型 MQM 独立互审</h3>
            <p class="bento-paragraph">
              严格遵循翻译与校对分离的工程原则。由 DeepSeek-R1 独立视角根据国际 MQM 框架对译文进行逐句审查，自动标明错误跨度。
            </p>
            <div class="mqm-badges-row">
              <span class="mqm-tag critical">🔴 阻断 (Critical)</span>
              <span class="mqm-tag major">🟠 重要 (Major)</span>
              <span class="mqm-tag minor">🟡 轻微 (Minor)</span>
            </div>
          </div>
        </div>

        <!-- Bento 4: 导师闭环与三表同步 -->
        <div class="bento-card bento-card-wide">
          <div class="bento-inner">
            <div class="bento-badge">04 · 闭环转化</div>
            <h3 class="bento-heading">导师答疑裁决闭环与学位论文成果映射</h3>
            <p class="bento-paragraph">
              在审校中遇到学术争议时，译者可一键打上 FLAG 标记提交导师。导师修改后，系统自动同步更新「原始句段表」、「修改记录表」与「最终定稿表」，并将全周期审计数据无缝输出为学术硕士毕业论文的实证材料。
            </p>
            <div class="delivery-pills-row">
              <span class="delivery-pill">📝 中英对照 Word (.docx)</span>
              <span class="delivery-pill">📄 纯英学术定稿 (.docx)</span>
              <span class="delivery-pill">📊 术语与证据链表 (.xlsx)</span>
              <span class="delivery-pill">📈 MQM 扣分审计表 (.xlsx)</span>
              <span class="delivery-pill">📦 全套可复现归档包 (.zip)</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         5. Interactive Live Deep Dive Showcase
         ============================================================ -->
    <section class="interactive-showcase-section">
      <div class="section-badge">INTERACTIVE INSPECTOR</div>
      <h2 class="section-title">高精模块交互式深度实测</h2>
      <p class="section-desc">切换下方标签，深入探索平台在术语信源、确定性查验、MQM 互审与导师决策中的精细表现。</p>

      <div class="inspector-tabs">
        <button
          v-for="(tab, idx) in showcaseTabs"
          :key="idx"
          class="tab-btn"
          :class="{ active: currentTab === idx }"
          @click="currentTab = idx"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span>{{ tab.name }}</span>
        </button>
      </div>

      <!-- Tab Content Area -->
      <div class="inspector-window">
        <!-- Tab 0: 权威术语证据卡 -->
        <div v-if="currentTab === 0" class="tab-panel">
          <div class="evidence-card-demo">
            <div class="demo-header">
              <div class="evidence-title">
                <span class="cert-badge">权威机构认证</span>
                <h4>天然气水合物 (Natural Gas Hydrate) 证据卡</h4>
              </div>
              <span class="trust-badge">信源等级: L1 (最高权威)</span>
            </div>
            <div class="evidence-body">
              <div class="evidence-row">
                <span class="row-label">规范中文名:</span>
                <span class="row-value font-bold">天然气水合物 / 可燃冰</span>
              </div>
              <div class="evidence-row">
                <span class="row-label">规范英文名:</span>
                <span class="row-value font-bold font-mono">Natural Gas Hydrate</span>
              </div>
              <div class="evidence-row">
                <span class="row-label">权威信源出处:</span>
                <span class="row-value">
                  全国科学技术名词审定委员会 (CNCTST) · 地球物理学名词 / 石油工程
                </span>
              </div>
              <div class="evidence-row">
                <span class="row-label">官方溯源链接:</span>
                <span class="row-value url-link">
                  https://www.termonline.cn/word/129845/1#SPE-Hydrate
                </span>
              </div>
              <div class="evidence-row">
                <span class="row-label">学科权威定义:</span>
                <span class="row-value quote-box">
                  “天然气与水在高压低温条件下形成的类冰状结晶物质。主要赋存于深水海底或陆域永久冻土带。”
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 1: 确定性数字差分零误差自检 -->
        <div v-if="currentTab === 1" class="tab-panel">
          <div class="numeric-check-demo">
            <div class="demo-header">
              <h4>Python 确定性数值与单位差分监控</h4>
              <span class="rule-status-pass">● 0 容忍门禁拦截中</span>
            </div>
            <div class="diff-table">
              <div class="diff-row header-row">
                <span>原文数字提取</span>
                <span>译文等价转换</span>
                <span>换算规则</span>
                <span>检验状态</span>
              </div>
              <div class="diff-row">
                <span class="font-mono">200 亿立方米</span>
                <span class="font-mono">20 billion m³</span>
                <span>100亿 = 10 billion (中英量级转换)</span>
                <span class="pass-tag">✓ PASS 零误差</span>
              </div>
              <div class="diff-row">
                <span class="font-mono">15.4 MPa</span>
                <span class="font-mono">15.4 MPa</span>
                <span>SI 法定压力单位对齐</span>
                <span class="pass-tag">✓ PASS 零误差</span>
              </div>
              <div class="diff-row warning-example">
                <span class="font-mono">3.5 万吨</span>
                <span class="font-mono">3.5 million tons (模拟错误)</span>
                <span>3.5万 = 35,000 / 0.035 million</span>
                <span class="blocked-tag">⚠️ 阻断: 量级虚增100倍</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: 跨模型 MQM 独立互审 -->
        <div v-if="currentTab === 2" class="tab-panel">
          <div class="mqm-audit-demo">
            <div class="demo-header">
              <div class="flex-center gap-8">
                <span class="model-badge">DeepSeek-R1 独立评审视角</span>
                <h4>MQM (Multidimensional Quality Metrics) 细粒度审计报告</h4>
              </div>
              <span class="score-badge">当前段落质量得分: 98.5 / 100</span>
            </div>
            <div class="mqm-issue-card">
              <div class="issue-header">
                <span class="issue-level minor">🟡 轻微 (Minor - 扣 0.5 分)</span>
                <span class="issue-cat">Category: Style / Register (语域与期刊指南)</span>
                <span class="issue-span">标注跨度: "It should be noted that"</span>
              </div>
              <div class="issue-content">
                <p><strong>审计意见:</strong> SPE Journal 指南明确建议避免使用冗长虚词引导句，建议改用直接主动陈述以增强论证效力。</p>
                <div class="fix-comparison">
                  <div class="fix-before"><span class="label">修改前:</span> It should be noted that the hydrate begins to dissociate...</div>
                  <div class="fix-after"><span class="label">建议修正:</span> Notably, the hydrate dissociates when temperature exceeds 4°C.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: 导师答疑与三表同步 -->
        <div v-if="currentTab === 3" class="tab-panel">
          <div class="supervisor-loop-demo">
            <div class="demo-header">
              <h4>导师集中答疑与决策本 (decisions.json) 同步机制</h4>
              <span class="closed-loop-badge">闭环状态: 已审定</span>
            </div>
            <div class="loop-grid">
              <div class="loop-box">
                <div class="box-title">🚩 译者疑难句 FLAG 提问</div>
                <p class="box-text">“文中的‘流化开采’在国外权威文献中既有 solid fluidization exploitation，也有 fluidization mining，何者更符合 SPE 规范？”</p>
              </div>
              <div class="loop-box answer">
                <div class="box-title">👨‍🏫 导师权威批注与裁决</div>
                <p class="box-text">“核对周守为院士 SPE 2020 顶刊论文，统一采用 ‘solid fluidization exploitation’，证据卡已同步归档。”</p>
              </div>
              <div class="loop-box sync">
                <div class="box-title">🔄 三表联动自动同步</div>
                <p class="box-text">段落表、术语证据卡与 decisions.json 全周期决策记录本已全部自动更新，永久保留导师采纳时间戳与论证依据。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         6. Built-in 11 Top Journals Presets Library
         ============================================================ -->
    <section class="journals-preview-section">
      <div class="section-badge">STANDARDS LIBRARY</div>
      <h2 class="section-title">内置 11 本国际顶级期刊投稿指南规范</h2>
      <p class="section-desc">已深度固化各大期刊关于语态、时态、参考文献与图表引用的严苛规则，一键自动匹配。</p>

      <div class="journals-grid">
        <div v-for="journal in presetJournals" :key="journal.code" class="journal-card">
          <div class="journal-card-header">
            <span class="j-publisher">{{ journal.publisher }}</span>
            <span class="j-impact">{{ journal.impact }}</span>
          </div>
          <h3 class="j-name">{{ journal.name }}</h3>
          <p class="j-focus">{{ journal.focus }}</p>
          <div class="j-rules">
            <span class="rule-chip">{{ journal.voice }}</span>
            <span class="rule-chip">{{ journal.tense }}</span>
            <span class="rule-chip">{{ journal.unit }}</span>
          </div>
        </div>
      </div>

      <div class="text-center mt-32">
        <router-link to="/journals" class="apple-btn-secondary">
          <span>查看全部 11 本顶刊详细指南规则</span>
          <span class="btn-arrow">→</span>
        </router-link>
      </div>
    </section>

    <!-- ============================================================
         7. Master Thesis (MTI) Academic Value Mapping
         ============================================================ -->
    <section class="thesis-mapping-section">
      <div class="section-badge">ACADEMIC EXCELLENCE</div>
      <h2 class="section-title">赋能翻译硕士 (MTI) 与工科硕博毕业论文</h2>
      <p class="section-desc">
        将一次翻译实践转化为充实、严谨、有实证数据支撑的学术论文核心章节。
      </p>

      <div class="thesis-chapters-grid">
        <div class="chapter-card">
          <div class="chap-badge">CHAPTER 2</div>
          <h3 class="chap-title">方法论体系构建</h3>
          <p class="chap-desc">
            详述 A0–D5 全生命周期人机协同工程流程，阐明四件套硬核约束注入机制与大语言模型协同工作原理。
          </p>
          <div class="chap-deliverables">
            <span>● brief.md 设计规范</span>
            <span>● 提示工程约束模板</span>
          </div>
        </div>

        <div class="chapter-card">
          <div class="chap-badge">CHAPTER 3</div>
          <h3 class="chap-title">翻译实践与证据链查证</h3>
          <p class="chap-desc">
            提供完整的学科专业术语证据卡矩阵，包含官方信源 URL、词条定义比对与石油工程长难句翻译实证。
          </p>
          <div class="chap-deliverables">
            <span>● 权威术语证据卡清单 (.xlsx)</span>
            <span>● 疑难句长难句导师答疑实录</span>
          </div>
        </div>

        <div class="chapter-card">
          <div class="chap-badge">CHAPTER 4</div>
          <h3 class="chap-title">质量评估与误差反思</h3>
          <p class="chap-desc">
            基于 MQM 国际学术框架的跨模型审校量化统计，深入分析阻断、重要与轻微错误的分布及原因。
          </p>
          <div class="chap-deliverables">
            <span>● MQM 多维罚分审计表 (.xlsx)</span>
            <span>● decisions.json 裁决归档包</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         8. Apple Keynote Grand Closing Banner
         ============================================================ -->
    <section class="keynote-closing-section">
      <div class="closing-container">
        <div class="closing-badge">READY TO START?</div>
        <h2 class="closing-title">告别盲目直译。<br />让每一处学术表达都经得起顶刊审视。</h2>
        <p class="closing-desc">
          无需安装繁琐软件，即刻进入翻译工作台，开启首篇论文的高标准中译英工程。
        </p>

        <div class="closing-actions">
          <router-link to="/workspace" class="apple-btn-primary large">
            <span>立即进入论文工作台</span>
            <span class="btn-arrow">↗</span>
          </router-link>
          <router-link to="/models" class="apple-btn-secondary large">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span>配置 DeepSeek / AI 引擎</span>
          </router-link>
        </div>

        <div class="closing-badges-footer">
          <span>✓ 支持 DeepSeek-V3 / R1 与主流大模型</span>
          <span class="sep">·</span>
          <span>✓ 100% 本地 SQLite / JSON 数据保密</span>
          <span class="sep">·</span>
          <span>✓ 符合学术伦理与同行评审可复现标准</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const currentTab = ref(0)

const showcaseTabs = [
  { name: '权威术语证据卡', icon: '🔍' },
  { name: '确定性数字 0 误差自检', icon: '🔢' },
  { name: '跨模型 MQM 独立互审', icon: '⚖️' },
  { name: '导师答疑与三表同步', icon: '👨‍🏫' },
]

const presetJournals = [
  {
    code: 'spe',
    publisher: 'SPE (Society of Petroleum Engineers)',
    name: 'SPE Journal',
    focus: '石油与天然气工程顶级期刊',
    impact: 'Q1 顶刊',
    voice: '鼓励主动语态',
    tense: '已完成工作用过去时',
    unit: '强制 SPE SI Metric',
  },
  {
    code: 'nature',
    publisher: 'Nature Portfolio',
    name: 'Nature / Communications',
    focus: '跨学科顶尖学术周刊',
    impact: 'IF > 64.8',
    voice: '主动语态优先 (We report)',
    tense: '方法过去时 · 事实现在时',
    unit: '严禁英制 · 强制 SI',
  },
  {
    code: 'ieee',
    publisher: 'IEEE',
    name: 'IEEE Transactions',
    focus: '电子信息与计算工程权威学报',
    impact: 'Top CCF/SCI',
    voice: '允许被动与清晰主动',
    tense: '定理/公理用现在时',
    unit: 'IEEE 标准图表编号',
  },
  {
    code: 'elsevier',
    publisher: 'Elsevier',
    name: 'Journal of Petroleum Science and Eng.',
    focus: '能源开采与油气地质工程',
    impact: 'Q1 TOP',
    voice: '第三人称客观叙述',
    tense: '实验结果用过去时',
    unit: '国际标准计量单位',
  },
]
</script>

<style scoped>
.apple-intro-view {
  display: flex;
  flex-direction: column;
  gap: 84px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 20px 16px 80px;
}

/* Common Section Typography */
.section-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #0071e3;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.section-title {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1d1d1f;
  margin: 0 0 14px;
  line-height: 1.15;
}

.section-desc {
  font-size: 17px;
  color: #86868b;
  line-height: 1.5;
  margin: 0 0 36px;
  max-width: 760px;
}

/* ============================================================
   1. Hero Keynote
   ============================================================ */
.hero-section {
  text-align: center;
  padding-top: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-eyebrow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.eyebrow-pill {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  border: 1px solid rgba(0, 113, 227, 0.18);
  padding: 4px 14px;
  border-radius: 980px;
}

.eyebrow-pill.subtle {
  color: #515154;
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.08);
}

.hero-title {
  font-size: 56px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.1;
  color: #1d1d1f;
  margin: 0 0 20px;
  max-width: 960px;
}

.hero-title-gradient {
  background: linear-gradient(135deg, #0071e3 0%, #43b5ff 60%, #5e5ce6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 18px;
  color: #6e6e73;
  line-height: 1.65;
  max-width: 820px;
  margin: 0 auto 36px;
  font-weight: 400;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 52px;
}

/* Apple Buttons */
.apple-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #0071e3;
  color: #ffffff;
  padding: 12px 26px;
  border-radius: 980px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 113, 227, 0.28);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.apple-btn-primary:hover {
  background: #0077ed;
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 113, 227, 0.36);
  color: #ffffff;
}

.apple-btn-primary.large {
  padding: 15px 34px;
  font-size: 16px;
}

.apple-btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  color: #1d1d1f;
  padding: 12px 24px;
  border-radius: 980px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid rgba(0, 0, 0, 0.12);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.apple-btn-secondary:hover {
  background: #fafafc;
  border-color: rgba(0, 0, 0, 0.24);
  transform: translateY(-1px);
  color: #1d1d1f;
}

.apple-btn-secondary.large {
  padding: 15px 30px;
  font-size: 16px;
}

.apple-btn-subtle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: #0071e3;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s;
}

.apple-btn-subtle:hover {
  opacity: 0.8;
}

.btn-arrow {
  font-size: 16px;
  transition: transform 0.2s;
}

.apple-btn-primary:hover .btn-arrow {
  transform: translate(2px, -2px);
}

/* Hero Showcase Frame */
.hero-showcase-window {
  width: 100%;
  max-width: 1080px;
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 24px 60px -12px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  text-align: left;
}

.showcase-titlebar {
  background: #fbfbfd;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.window-controls {
  display: flex;
  gap: 8px;
}

.ctrl-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
}

.ctrl-dot.red { background: #ff5f56; }
.ctrl-dot.yellow { background: #ffbd2e; }
.ctrl-dot.green { background: #27c93f; }

.window-address {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  padding: 3px 14px;
  border-radius: 6px;
  font-size: 12px;
  color: #6e6e73;
  font-family: var(--apple-font-mono);
}

.status-tag.live {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #34c759;
  background: rgba(52, 199, 89, 0.12);
  padding: 3px 8px;
  border-radius: 4px;
}

.showcase-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  padding: 24px;
  gap: 20px;
  align-items: stretch;
  background: #fafafc;
}

.showcase-pane {
  background: #ffffff;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.pane-tag {
  color: #86868b;
}

.domain-tag {
  color: #0071e3;
  background: rgba(0, 113, 227, 0.06);
  padding: 2px 8px;
  border-radius: 980px;
}

.verified-tag {
  color: #34c759;
  font-weight: 700;
}

.source-bubble, .target-bubble {
  font-size: 14px;
  line-height: 1.7;
  color: #1d1d1f;
  background: #f5f5f7;
  padding: 14px 16px;
  border-radius: 10px;
  border-left: 3px solid #0071e3;
}

.target-bubble {
  border-left-color: #34c759;
}

.highlight-num {
  font-weight: 700;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.12);
  padding: 1px 4px;
  border-radius: 4px;
}

.highlight-num-pass {
  font-weight: 700;
  color: #34c759;
  background: rgba(52, 199, 89, 0.14);
  padding: 1px 4px;
  border-radius: 4px;
}

.constraints-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.constraint-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #515154;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  padding: 6px 10px;
  border-radius: 6px;
}

.showcase-divider {
  display: flex;
  align-items: center;
  justify-content: center;
}

.engine-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 10px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.engine-icon {
  font-size: 20px;
}

.engine-text {
  font-size: 10px;
  font-weight: 700;
  color: #86868b;
  writing-mode: vertical-rl;
  letter-spacing: 0.1em;
}

.audit-summary-strip {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.audit-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.audit-stat.pass {
  background: rgba(52, 199, 89, 0.08);
  color: #1b7e36;
}

.audit-stat.mqm {
  background: rgba(0, 113, 227, 0.08);
  color: #0051a8;
}

.stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.stat-dot.green { background: #34c759; }
.stat-dot.blue { background: #0071e3; }

/* ============================================================
   2. Paradigm Shift Comparison
   ============================================================ */
.comparison-section {
  text-align: center;
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  text-align: left;
}

.compare-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 32px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  position: relative;
}

.compare-card.positive {
  border-color: rgba(0, 113, 227, 0.28);
  box-shadow: 0 12px 32px rgba(0, 113, 227, 0.08);
  background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
}

.card-status-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 980px;
  margin-bottom: 16px;
}

.neg-badge {
  background: rgba(255, 59, 48, 0.08);
  color: #d70015;
}

.pos-badge {
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
}

.card-headline {
  font-size: 22px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 24px;
}

.compare-points {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.compare-points li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.point-icon {
  font-size: 18px;
  line-height: 1.2;
}

.point-detail strong {
  display: block;
  font-size: 15px;
  color: #1d1d1f;
  margin-bottom: 4px;
}

.point-detail p {
  font-size: 13px;
  color: #6e6e73;
  line-height: 1.5;
  margin: 0;
}

/* ============================================================
   3. A0–D5 Methodology Ladder
   ============================================================ */
.methodology-section {
  text-align: center;
}

.phases-ladder {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  text-align: left;
}

.phase-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.phase-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.06);
}

.phase-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}

.phase-num {
  font-size: 11px;
  font-weight: 800;
  color: #0071e3;
  letter-spacing: 0.08em;
}

.phase-title {
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
}

.phase-summary {
  font-size: 12px;
  color: #86868b;
  line-height: 1.5;
  margin: 0 0 18px;
  min-height: 36px;
}

.step-chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.step-chip {
  font-size: 12px;
  color: #3a3a3c;
  background: #f5f5f7;
  padding: 7px 10px;
  border-radius: 8px;
  border-left: 2px solid #0071e3;
}

.step-chip strong {
  color: #0071e3;
  margin-right: 4px;
}

/* ============================================================
   4. Bento Grid 4.0
   ============================================================ */
.bento-section {
  text-align: center;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  text-align: left;
}

.bento-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 28px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.bento-card-large {
  grid-column: span 2;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
}

.bento-card-wide {
  grid-column: span 3;
}

.bento-badge {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #0071e3;
  margin-bottom: 10px;
}

.bento-heading {
  font-size: 20px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 12px;
}

.bento-paragraph {
  font-size: 14px;
  color: #6e6e73;
  line-height: 1.6;
  margin: 0 0 20px;
}

.bento-tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cloud-pill {
  font-size: 11px;
  background: #f5f5f7;
  color: #3a3a3c;
  padding: 4px 10px;
  border-radius: 980px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.bento-preview-box {
  background: #1d1d1f;
  border-radius: 12px;
  padding: 16px;
  color: #ffffff;
  font-family: var(--apple-font-mono);
  font-size: 11px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.preview-mini-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.code-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
}

.code-title {
  font-size: 10px;
  color: #a1a1a6;
}

.preview-mini-code {
  margin: 0;
  color: #64d2ff;
  line-height: 1.5;
}

.metric-block {
  background: #f5f5f7;
  border-radius: 14px;
  padding: 16px;
  text-align: center;
  margin-top: auto;
}

.metric-num {
  font-size: 36px;
  font-weight: 800;
  color: #0071e3;
  line-height: 1;
  margin-bottom: 6px;
}

.metric-unit {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
}

.metric-desc {
  font-size: 12px;
  color: #86868b;
}

.mqm-badges-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.mqm-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
}

.mqm-tag.critical { background: rgba(255, 59, 48, 0.1); color: #d70015; }
.mqm-tag.major { background: rgba(255, 159, 10, 0.1); color: #c97200; }
.mqm-tag.minor { background: rgba(255, 204, 0, 0.15); color: #8e6d00; }

.delivery-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.delivery-pill {
  font-size: 13px;
  font-weight: 500;
  background: #f5f5f7;
  color: #1d1d1f;
  padding: 8px 14px;
  border-radius: 980px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* ============================================================
   5. Interactive Inspector Tabs & Window
   ============================================================ */
.interactive-showcase-section {
  text-align: center;
}

.inspector-tabs {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 980px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  color: #515154;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.tab-btn:hover {
  background: #f5f5f7;
  color: #1d1d1f;
}

.tab-btn.active {
  background: #0071e3;
  color: #ffffff;
  border-color: #0071e3;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.24);
}

.inspector-window {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
  padding: 32px;
  text-align: left;
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.demo-header h4 {
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0;
}

.cert-badge {
  font-size: 10px;
  font-weight: 700;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 4px;
  display: inline-block;
}

.trust-badge {
  font-size: 12px;
  font-weight: 700;
  color: #34c759;
  background: rgba(52, 199, 89, 0.12);
  padding: 4px 10px;
  border-radius: 980px;
}

.evidence-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evidence-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: baseline;
  font-size: 14px;
}

.row-label {
  color: #86868b;
}

.row-value {
  color: #1d1d1f;
}

.url-link {
  color: #0071e3;
  font-family: var(--apple-font-mono);
  font-size: 12px;
}

.quote-box {
  background: #f5f5f7;
  padding: 12px 14px;
  border-radius: 8px;
  line-height: 1.6;
  font-style: italic;
  color: #3a3a3c;
}

/* Numeric Diff Table */
.rule-status-pass {
  font-size: 12px;
  font-weight: 700;
  color: #34c759;
}

.diff-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diff-row {
  display: grid;
  grid-template-columns: 1.5fr 1.5fr 2fr 1.2fr;
  padding: 12px 14px;
  background: #f5f5f7;
  border-radius: 8px;
  font-size: 13px;
  align-items: center;
}

.header-row {
  background: #fafafc;
  font-weight: 700;
  color: #86868b;
  font-size: 12px;
}

.pass-tag {
  color: #34c759;
  font-weight: 700;
}

.blocked-tag {
  color: #ff3b30;
  font-weight: 700;
}

.warning-example {
  background: rgba(255, 59, 48, 0.05);
}

/* MQM Issue Card */
.score-badge {
  font-size: 12px;
  font-weight: 700;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 4px 10px;
  border-radius: 980px;
}

.model-badge {
  font-size: 11px;
  font-weight: 700;
  color: #5856d6;
  background: rgba(88, 86, 214, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.mqm-issue-card {
  background: #fbfbfd;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
}

.issue-level.minor {
  font-weight: 700;
  color: #a06e00;
}

.issue-cat {
  color: #86868b;
}

.issue-span {
  font-family: var(--apple-font-mono);
  background: #ececf0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.fix-comparison {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.fix-before {
  color: #86868b;
  text-decoration: line-through;
}

.fix-after {
  color: #34c759;
  font-weight: 600;
}

/* Supervisor Loop */
.closed-loop-badge {
  font-size: 12px;
  font-weight: 700;
  color: #34c759;
  background: rgba(52, 199, 89, 0.12);
  padding: 4px 10px;
  border-radius: 980px;
}

.loop-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.loop-box {
  background: #f5f5f7;
  border-radius: 12px;
  padding: 16px;
}

.loop-box.answer {
  background: rgba(0, 113, 227, 0.05);
  border: 1px solid rgba(0, 113, 227, 0.12);
}

.loop-box.sync {
  background: rgba(52, 199, 89, 0.05);
  border: 1px solid rgba(52, 199, 89, 0.12);
}

.box-title {
  font-size: 13px;
  font-weight: 700;
  color: #1d1d1f;
  margin-bottom: 8px;
}

.box-text {
  font-size: 13px;
  color: #515154;
  line-height: 1.5;
  margin: 0;
}

/* ============================================================
   6. Built-in Journals Grid
   ============================================================ */
.journals-preview-section {
  text-align: center;
}

.journals-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  text-align: left;
}

.journal-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 22px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
}

.journal-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  margin-bottom: 8px;
}

.j-publisher {
  font-weight: 700;
  color: #86868b;
}

.j-impact {
  font-weight: 800;
  color: #ff9500;
  background: rgba(255, 149, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.j-name {
  font-size: 16px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 6px;
}

.j-focus {
  font-size: 12px;
  color: #86868b;
  margin: 0 0 16px;
  line-height: 1.4;
}

.j-rules {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: auto;
}

.rule-chip {
  font-size: 11px;
  background: #f5f5f7;
  color: #515154;
  padding: 4px 8px;
  border-radius: 6px;
}

/* ============================================================
   7. Thesis Mapping Section
   ============================================================ */
.thesis-mapping-section {
  text-align: center;
}

.thesis-chapters-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  text-align: left;
}

.chapter-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 28px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.chap-badge {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #0071e3;
  margin-bottom: 10px;
}

.chap-title {
  font-size: 19px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 10px;
}

.chap-desc {
  font-size: 13px;
  color: #6e6e73;
  line-height: 1.6;
  margin: 0 0 20px;
}

.chap-deliverables {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #0071e3;
  font-weight: 600;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 14px;
}

/* ============================================================
   8. Keynote Grand Closing Banner
   ============================================================ */
.keynote-closing-section {
  text-align: center;
  background: linear-gradient(145deg, #1d1d1f 0%, #151517 100%);
  border-radius: 28px;
  padding: 64px 32px;
  color: #ffffff;
  box-shadow: 0 24px 64px -16px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: hidden;
}

.keynote-closing-section::before {
  content: '';
  position: absolute;
  top: -120px;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  height: 240px;
  background: radial-gradient(circle, rgba(0, 113, 227, 0.35) 0%, transparent 70%);
  pointer-events: none;
}

.closing-container {
  position: relative;
  z-index: 2;
  max-width: 820px;
  margin: 0 auto;
}

.closing-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #2997ff;
  margin-bottom: 16px;
}

.closing-title {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.18;
  color: #ffffff;
  margin: 0 0 18px;
}

.closing-desc {
  font-size: 17px;
  color: #a1a1a6;
  line-height: 1.6;
  margin: 0 0 36px;
}

.closing-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.closing-actions .apple-btn-secondary {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.closing-actions .apple-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.closing-badges-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 12px;
  color: #86868b;
  flex-wrap: wrap;
}

.closing-badges-footer .sep {
  opacity: 0.5;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .hero-title { font-size: 42px; }
  .showcase-content { grid-template-columns: 1fr; }
  .showcase-divider { display: none; }
  .comparison-grid { grid-template-columns: 1fr; }
  .phases-ladder { grid-template-columns: 1fr 1fr; }
  .bento-grid { grid-template-columns: 1fr; }
  .bento-card-large { grid-column: span 1; grid-template-columns: 1fr; }
  .bento-card-wide { grid-column: span 1; }
  .journals-grid { grid-template-columns: 1fr 1fr; }
  .thesis-chapters-grid { grid-template-columns: 1fr; }
  .loop-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .hero-title { font-size: 32px; }
  .section-title { font-size: 28px; }
  .phases-ladder { grid-template-columns: 1fr; }
  .journals-grid { grid-template-columns: 1fr; }
  .closing-title { font-size: 28px; }
  .diff-row { grid-template-columns: 1fr; gap: 4px; }
}
</style>
