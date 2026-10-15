package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.swpu.transflow.util.Maps;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 译前准备：术语查证。
 *
 * 流程：输入词语(可带上下文) → 判定所属领域 → 按「一级源优先，找不到再降二级，三级一律不用」检索信源
 * → 给出候选译文 + 权威信源证据 + 裁决状态；未收录的词语则给出分级查证方案。
 */
@Service
public class TermPrepService {

    private final JsonDataService data;
    private final AuthorityLookupService authority;

    public TermPrepService(JsonDataService data, AuthorityLookupService authority) {
        this.data = data;
        this.authority = authority;
    }

    /** 术语查证主入口 */
    public Map<String, Object> analyze(String term, String context) {
        String q = term == null ? "" : term.trim();
        if (q.isEmpty()) {
            return Maps.of("term", "", "status", "invalid", "message", "请输入要查证的词语");
        }

        Map<String, Object> result = Maps.newMap();
        result.put("term", q);

        // 1. 领域判定
        Map<String, Object> domain = detectDomain(q, context);
        result.put("domain", domain);

        // 2. 一级源直取：不经过搜索引擎，直接向「术语在线」(T1-06) 取官方英文译名
        Map<String, Object> auth = authority.lookup(q);
        result.put("authority", auth);

        // 3. 本地术语库（若已收录，给出完整分级证据链）
        Map<String, Object> hit = lookupTermbase(q);
        if (hit != null) {
            result.putAll(hit);
            result.put("source", "termbase");
            result.put("policy", policy());
            return result;
        }

        // 4. 术语库未收录，但一级源命中 → 直接锁定为该词的定译
        if (Boolean.TRUE.equals(auth.get("found"))) {
            String en = String.valueOf(auth.get("translation"));
            result.put("status", "locked");
            result.put("verdict_label", "锁定 · 一级源定译");
            result.put("translation", en);
            result.put("evidence", evidenceFromAuthority(auth));
            result.put("reason", "一级源「全国术语在线」(T1-06) 已收录，出处《"
                    + auth.get("termbase") + "》，依策略可直接作为定译依据");
            result.put("policy", policy());
            result.put("source", "authority");
            return result;
        }

        // 5. 两级都没有 → 生成分级查证方案（三级源一律不用）
        result.put("status", "pending");
        result.put("verdict_label", "待查证");
        result.put("translation", null);
        result.put("evidence", Collections.emptyList());
        result.put("message", "一级源未收录该词，已按领域生成分级查证方案，请降级逐级核查（二级源需两个独立来源一致）");
        result.put("searchPlan", buildSearchPlan(q));
        result.put("policy", policy());
        result.put("source", "plan");
        return result;
    }

    /** 单独取一级源权威译文（供页面「显示译文」按需调用） */
    public Map<String, Object> authorityLookup(String term) {
        return authority.lookup(term);
    }

    /** 把一级源结果转成与术语库同构的证据行，便于前端统一渲染 */
    private List<Map<String, Object>> evidenceFromAuthority(Map<String, Object> auth) {
        List<Map<String, Object>> list = new ArrayList<>();
        String detail = String.valueOf(auth.get("detail_url"));
        list.add(Maps.of(
                "text", String.valueOf(auth.get("translation")),
                "tier", "tier1",
                "source_id", String.valueOf(auth.get("source_id")),
                "source_name", String.valueOf(auth.get("source_name")),
                "termbase", String.valueOf(auth.get("termbase")),
                "url", detail,
                "search_url", detail,
                "search_kind", "site-detail",
                "snippet", String.valueOf(auth.get("definition"))));
        Object also = auth.get("also_from");
        if (also instanceof List) {
            for (Object o : (List<?>) also) {
                if (!(o instanceof Map)) {
                    continue;
                }
                @SuppressWarnings("unchecked")
                Map<String, Object> m = (Map<String, Object>) o;
                String en = String.valueOf(m.get("translation"));
                String tb = String.valueOf(m.get("termbase"));
                if (en.isEmpty() || "null".equals(en)) {
                    continue;
                }
                if (en.equals(String.valueOf(auth.get("translation")))) {
                    continue;
                }
                list.add(Maps.of(
                        "text", en,
                        "tier", "tier1",
                        "source_id", String.valueOf(auth.get("source_id")),
                        "source_name", String.valueOf(auth.get("source_name")),
                        "termbase", tb,
                        "url", detail,
                        "search_url", detail,
                        "search_kind", "site-detail",
                        "snippet", "术语库《" + tb + "》给出的译名"));
            }
        }
        return list;
    }

    /** 领域判定：对 term + context 做关键词打分 */
    private Map<String, Object> detectDomain(String term, String context) {
        JsonNode root = data.read("termbase/domain_keywords.json");
        String hay = (term + " " + (context == null ? "" : context)).toLowerCase();

        String bestKey = null;
        String bestZh = null;
        int bestScore = 0;
        List<String> bestHits = new ArrayList<>();

        if (root != null) {
            JsonNode domains = root.path("domains");
            Iterator<String> it = domains.fieldNames();
            while (it.hasNext()) {
                String key = it.next();
                JsonNode d = domains.get(key);
                List<String> hits = new ArrayList<>();
                for (JsonNode kw : d.path("keywords")) {
                    String k = kw.asText().toLowerCase();
                    if (!k.isEmpty() && hay.contains(k)) {
                        hits.add(kw.asText());
                    }
                }
                if (hits.size() > bestScore) {
                    bestScore = hits.size();
                    bestKey = key;
                    bestZh = d.path("domain_zh").asText();
                    bestHits = hits;
                }
            }
        }

        if (bestKey == null) {
            return Maps.of("domain", "unknown", "domain_zh", "未识别领域",
                    "confidence", 0.0, "matched_keywords", Collections.emptyList(),
                    "reason", "未命中任何领域关键词，建议补充上下文或人工确认");
        }
        double confidence = Math.min(1.0, bestScore / 3.0);
        confidence = Math.round(confidence * 100) / 100.0;
        return Maps.of("domain", bestKey, "domain_zh", bestZh,
                "confidence", confidence, "matched_keywords", bestHits,
                "reason", "命中 " + bestScore + " 个领域关键词：" + String.join("、", bestHits));
    }

    /** 术语库查询；命中返回带裁决的结果，否则 null */
    private Map<String, Object> lookupTermbase(String term) {
        JsonNode root = data.read("termbase/terms.json");
        if (root == null) {
            return null;
        }
        for (JsonNode t : root.path("terms")) {
            if (!t.path("term").asText().equalsIgnoreCase(term)) {
                continue;
            }
            List<Map<String, Object>> evidence = new ArrayList<>();
            for (JsonNode tr : t.path("translations")) {
                String url = tr.path("url").asText();
                String h = hostOf(url);
                evidence.add(Maps.of(
                        "text", tr.path("text").asText(),
                        "tier", tr.path("tier").asText(),
                        "source_id", tr.path("source_id").asText(),
                        "source_name", tr.path("source_name").asText(),
                        "termbase", tr.path("source_name").asText(),
                        "url", url,
                        "search_url", buildSearchUrl(h, term),
                        "search_kind", hasSiteSearch(h) ? "site-search" : "homepage",
                        "snippet", tr.path("snippet").asText()));
            }
            Map<String, Object> r = Maps.newMap();
            r.put("term", t.path("term").asText());
            r.put("term_domain", t.path("domain").asText());
            r.put("evidence", evidence);
            r.putAll(adjudicate(evidence));
            return r;
        }
        return null;
    }

    /** 分级裁决：三级作废 > 一级锁定 > 二级交叉一致 > 待人工 */
    private Map<String, Object> adjudicate(List<Map<String, Object>> evidence) {
        for (Map<String, Object> e : evidence) {
            if ("tier3".equals(e.get("tier"))) {
                return Maps.of("status", "blocked", "translation", null,
                        "verdict_label", "作废重查",
                        "reason", "证据链命中黑名单「" + e.get("source_name") + "」，本条术语全部作废");
            }
        }

        List<Map<String, Object>> t1 = filter(evidence, "tier1");
        if (!t1.isEmpty()) {
            Set<String> texts = new LinkedHashSet<>();
            for (Map<String, Object> e : t1) {
                texts.add(String.valueOf(e.get("text")));
            }
            if (texts.size() == 1) {
                return Maps.of("status", "locked", "translation", t1.get(0).get("text"),
                        "verdict_label", "锁定 · 强制译法",
                        "reason", "一级源一致通过，锁定为强制译法");
            }
            return Maps.of("status", "conflict", "translation", null,
                    "verdict_label", "冲突待裁定",
                    "reason", "多个一级源译法不一致：" + texts + "，需人工裁定");
        }

        List<Map<String, Object>> t2 = filter(evidence, "tier2");
        if (!t2.isEmpty()) {
            Set<String> texts = new LinkedHashSet<>();
            Set<String> srcs = new LinkedHashSet<>();
            for (Map<String, Object> e : t2) {
                texts.add(String.valueOf(e.get("text")));
                srcs.add(String.valueOf(e.get("source_name")));
            }
            if (texts.size() == 1 && srcs.size() >= 2) {
                return Maps.of("status", "confirmed", "translation", t2.get(0).get("text"),
                        "verdict_label", "暂定 · 二级源交叉一致",
                        "reason", "两个独立二级源交叉一致，暂定译法");
            }
            return Maps.of("status", "pending", "translation", null,
                    "verdict_label", "待人工确认",
                    "reason", "仅有二级源且未达交叉验证标准（需 ≥2 个独立来源译法一致）");
        }

        return Maps.of("status", "pending", "translation", null,
                "verdict_label", "待人工确认", "reason", "无有效信源覆盖");
    }

    /** 未收录词语的分级查证方案：一级优先 → 二级 → 三级不用 */
    private List<Map<String, Object>> buildSearchPlan(String term) {
        JsonNode sources = data.read("sources/sources.json");
        List<Map<String, Object>> plan = new ArrayList<>();
        if (sources == null) {
            return plan;
        }
        JsonNode tiers = sources.path("tiers");
        plan.add(round(tiers.path("tier1"), "tier1", "第一轮 · 一级源（官方权威，命中即锁定）", term, 9));
        plan.add(round(tiers.path("tier2"), "tier2", "第二轮 · 二级源（一级源无覆盖时才用，需两个独立源一致）", term, 8));
        plan.add(Maps.of("tier", "tier3", "label", "三级源（黑名单）", "count", 0,
                "sources", Collections.emptyList(), "note", "一律不采用"));
        return plan;
    }

    private Map<String, Object> round(JsonNode tier, String key, String label, String term, int limit) {
        List<Map<String, Object>> list = new ArrayList<>();
        JsonNode arr = tier.path("sources");
        int i = 0;
        for (JsonNode s : arr) {
            if (i++ >= limit) {
                break;
            }
            JsonNode domains = s.path("domains");
            String host = domains.isArray() && domains.size() > 0 ? domains.get(0).asText() : "";
            list.add(Maps.of(
                    "name", s.path("name").asText(),
                    "affiliation", s.path("affiliation").asText(),
                    "site", host,
                    "url", host.isEmpty() ? "" : "https://" + host + "/",
                    "search_url", buildSearchUrl(host, term),
                    "search_kind", hasSiteSearch(host) ? "site-search" : "homepage",
                    "query", term));
        }
        return Maps.of("tier", key, "label", label, "count", list.size(), "sources", list);
    }

    /** 构造「进入该官网检索该词」的深链；未配置模板则回退到该站首页（绝不经过搜索引擎） */
    private String buildSearchUrl(String host, String term) {
        if (host == null || host.isEmpty()) {
            return "";
        }
        String q = enc(term);
        JsonNode cfg = data.read("sources/search_templates.json");
        if (cfg != null) {
            String tpl = templateFor(cfg.path("templates"), host);
            if (tpl != null && !tpl.isEmpty()) {
                return tpl.replace("{q}", q);
            }
            String def = cfg.path("default").asText("");
            if (!def.isEmpty()) {
                return def.replace("{base}", "https://" + host).replace("{q}", q);
            }
        }
        return "https://" + host + "/";
    }

    /** 该信源是否有站内检索模板（有=可直接检索，无=只能打开首页） */
    private boolean hasSiteSearch(String host) {
        if (host == null || host.isEmpty()) {
            return false;
        }
        JsonNode cfg = data.read("sources/search_templates.json");
        return cfg != null && templateFor(cfg.path("templates"), host) != null;
    }

    /** 精确匹配 host（显式子域需在模板中单独列出，避免 scio.gov.cn 被误配成 gov.cn） */
    private String templateFor(JsonNode templates, String host) {
        JsonNode t = templates.path(host);
        return (t.isTextual() && !t.asText().isEmpty()) ? t.asText() : null;
    }

    private String hostOf(String url) {
        try {
            String withScheme = url.contains("://") ? url : "http://" + url;
            String host = new java.net.URI(withScheme).getHost();
            return host == null ? "" : host.toLowerCase().replaceAll("^www\\.", "");
        } catch (Exception e) {
            return "";
        }
    }

    private String enc(String s) {
        try {
            return java.net.URLEncoder.encode(s == null ? "" : s, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    private Map<String, Object> policy() {
        return Maps.of(
                "tier1", "一级源可直接作为定译依据",
                "tier2", "仅当一级源未覆盖时使用，且需两个独立二级源译法一致",
                "tier3", "黑名单一律不采用，命中即整条作废",
                "unmatched", "无信源覆盖则标记「待人工确认」");
    }

    private List<Map<String, Object>> filter(List<Map<String, Object>> list, String tier) {
        List<Map<String, Object>> r = new ArrayList<>();
        for (Map<String, Object> e : list) {
            if (tier.equals(e.get("tier"))) {
                r.add(e);
            }
        }
        return r;
    }
}
