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
        String q = AuthorityLookupService.normalizeTerm(term);
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

        // 3. 确定该词的英文译名：优先「术语在线」的国家审定译名，其次本地术语库一级源译法。
        //    各网站检索词不同——中文站用中文原词，英文站（中国政府网英文版、教育部英文官网等）
        //    必须用英文译名，否则必然搜不到。所以要先拿到英文译名再构造检索深链。
        String enTerm = "";
        if (Boolean.TRUE.equals(auth.get("found"))) {
            enTerm = String.valueOf(auth.get("translation"));
        }
        if (enTerm.isEmpty()) {
            enTerm = firstEnglishFromTermbase(q);
        }
        result.put("en_term", enTerm.isEmpty() ? null : enTerm);

        // 4. 本地术语库（若已收录，给出完整分级证据链；同时并入术语在线的国家审定译名一起裁决）
        Map<String, Object> hit = lookupTermbase(q, enTerm);
        if (hit != null) {
            mergeAuthorityEvidence(hit, auth);
            // 在线补查失败不是“一级源无覆盖”，不得因此自动采用二级证据。
            if (!Boolean.TRUE.equals(auth.get("search_complete"))
                    && "confirmed".equals(hit.get("status"))) {
                hit.put("status", "pending");
                hit.put("translation", null);
                hit.put("verdict_label", "一级源查询未完成 · 待查证");
                hit.put("reason", "二级源虽交叉一致，但一级源在线查询未完成，暂不能降级定稿");
            }
            // 本地已有其他一级源证据时，权威卡片不能继续显示“找不到”。
            if (!Boolean.TRUE.equals(auth.get("found"))) {
                Map<String, Object> local = localAuthority(hit, q, auth);
                if (local != null) result.put("authority", local);
            }
            result.putAll(hit);
            result.put("source", "termbase");
            result.put("policy", policy());
            return result;
        }

        // 5. 术语库未收录但一级源命中 → 全部真实条目统一裁决，不忽略同词异译
        if (Boolean.TRUE.equals(auth.get("found"))) {
            List<Map<String, Object>> evidence = evidenceFromAuthority(auth, enTerm);
            result.putAll(adjudicate(evidence));
            result.put("evidence", evidence);
            result.put("policy", policy());
            result.put("source", "authority");
            return result;
        }

        // 6. 本次自动查询未取到证据 → 继续核验其他一级源，不能断言所有一级源均未收录
        result.put("status", "pending");
        result.put("verdict_label", "待查证");
        result.put("translation", null);
        result.put("evidence", Collections.emptyList());
        result.put("message", Boolean.TRUE.equals(auth.get("search_complete"))
                ? "本次自动核查未取得译文，请先继续核验其他一级源；只有确认一级源无覆盖，才可采用两个独立二级源的一致译法"
                : "一级源在线查询未完成，不能判断是否收录；请重试或在官网核验，不应直接降级采用二级源");
        result.put("searchPlan", buildSearchPlan(q, enTerm));
        result.put("policy", policy());
        result.put("source", "plan");
        return result;
    }

    /** 单独取一级源权威译文（供页面「显示译文」按需调用） */
    public Map<String, Object> authorityLookup(String term) {
        return authority.lookup(term);
    }

    /** 从本地术语库取该词的首个英文译名（优先一级源），取不到返回空串 */
    private String firstEnglishFromTermbase(String term) {
        JsonNode root = data.read("termbase/terms.json");
        if (root == null) {
            return "";
        }
        for (JsonNode t : root.path("terms")) {
            if (!AuthorityLookupService.normalizeTerm(t.path("term").asText()).equalsIgnoreCase(term)) {
                continue;
            }
            String fallback = "";
            for (JsonNode tr : t.path("translations")) {
                String text = tr.path("text").asText("");
                if (text.isEmpty()) {
                    continue;
                }
                if (fallback.isEmpty()) {
                    fallback = text;
                }
                if ("tier1".equals(tr.path("tier").asText())) {
                    return text;
                }
            }
            return fallback;
        }
        return "";
    }

    /** 将每一条真实检索条目分别转成证据，不把聚合总览的译名与库名按下标猜配。 */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> evidenceFromAuthority(Map<String, Object> auth, String enTerm) {
        List<Map<String, Object>> list = new ArrayList<>();
        Object also = auth.get("also_from");
        List<Map<String, Object>> entries = also instanceof List
                ? (List<Map<String, Object>>) also : Collections.singletonList(auth);
        if (entries.isEmpty()) entries = Collections.singletonList(auth);
        for (Map<String, Object> entry : entries) {
            String detail = String.valueOf(entry.get("detail_url"));
            list.add(Maps.of("text", entry.get("translation"), "tier", "tier1",
                    "source_id", auth.get("source_id"), "source_name", auth.get("source_name"),
                    "termbase", entry.get("termbase"), "url", detail,
                    "snippet", entry.get("definition"), "search_url", detail,
                    "search_kind", "site-detail", "search_query", entry.get("term"),
                    "search_lang", "zh", "search_label", "术语在线原始条目",
                    "search_probe", "接口精确检索，原始条目逐条核验"));
        }
        return list;
    }

    @SuppressWarnings("unchecked")
    private void mergeAuthorityEvidence(Map<String, Object> hit, Map<String, Object> auth) {
        if (!Boolean.TRUE.equals(auth.get("found"))) return;
        List<Map<String, Object>> evidence = (List<Map<String, Object>>) hit.get("evidence");
        for (Map<String, Object> row : evidenceFromAuthority(auth, "")) {
            boolean duplicate = false;
            for (Map<String, Object> old : evidence) {
                if (row.get("url").equals(old.get("url")) && row.get("text").equals(old.get("text"))) {
                    duplicate = true;
                    break;
                }
            }
            if (!duplicate) evidence.add(row);
        }
        hit.putAll(adjudicate(evidence));
    }

    /** 本地收录的一级证据与实时查询分开标注，不冒充本次在线取证。 */
    @SuppressWarnings("unchecked")
    private Map<String, Object> localAuthority(Map<String, Object> hit, String q, Map<String, Object> remote) {
        List<Map<String, Object>> evidence = (List<Map<String, Object>>) hit.get("evidence");
        List<Map<String, Object>> t1 = filter(evidence, "tier1");
        if (t1.isEmpty()) return null;
        Map<String, Object> row = t1.get(0);
        return Maps.of("found", true, "term", q, "translation", row.get("text"),
                "source_id", row.get("source_id"), "source_name", row.get("source_name"),
                "termbase", row.get("source_name"), "definition", row.get("snippet"),
                "detail_url", row.get("url"), "site", row.get("url"),
                "lookup_status", "local_evidence", "search_complete", remote.get("search_complete"),
                "checks", remote.get("checks"), "online_lookup", remote,
                "reason", "本地术语库已收录该一级源证据，并非本次实时获取；请打开原文复核。在线补查：" + remote.get("reason"));
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
    private Map<String, Object> lookupTermbase(String term, String enTerm) {
        JsonNode root = data.read("termbase/terms.json");
        if (root == null) {
            return null;
        }
        for (JsonNode t : root.path("terms")) {
            if (!AuthorityLookupService.normalizeTerm(t.path("term").asText()).equalsIgnoreCase(term)) {
                continue;
            }
            List<Map<String, Object>> evidence = new ArrayList<>();
            for (JsonNode tr : t.path("translations")) {
                String url = tr.path("url").asText();
                String h = hostOf(url);
                Map<String, Object> row = Maps.newMap();
                row.put("text", tr.path("text").asText());
                row.put("tier", tr.path("tier").asText());
                row.put("source_id", tr.path("source_id").asText());
                row.put("source_name", tr.path("source_name").asText());
                row.put("termbase", tr.path("source_name").asText());
                row.put("url", url);
                row.put("snippet", tr.path("snippet").asText());
                row.putAll(siteSearch(h, term, enTerm));
                evidence.add(row);
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
    private List<Map<String, Object>> buildSearchPlan(String term, String enTerm) {
        JsonNode sources = data.read("sources/sources.json");
        List<Map<String, Object>> plan = new ArrayList<>();
        if (sources == null) {
            return plan;
        }
        JsonNode tiers = sources.path("tiers");
        plan.add(round(tiers.path("tier1"), "tier1", "第一轮 · 一级源（官方权威，命中即锁定）", term, enTerm, 9));
        plan.add(round(tiers.path("tier2"), "tier2", "第二轮 · 二级源（一级源无覆盖时才用，需两个独立源一致）", term, enTerm, 8));
        plan.add(Maps.of("tier", "tier3", "label", "三级源（黑名单）", "count", 0,
                "sources", Collections.emptyList(), "note", "一律不采用"));
        return plan;
    }

    private Map<String, Object> round(JsonNode tier, String key, String label,
                                      String term, String enTerm, int limit) {
        List<Map<String, Object>> list = new ArrayList<>();
        JsonNode arr = tier.path("sources");
        int i = 0;
        for (JsonNode s : arr) {
            if (i++ >= limit) {
                break;
            }
            JsonNode domains = s.path("domains");
            String host = domains.isArray() && domains.size() > 0 ? domains.get(0).asText() : "";
            Map<String, Object> item = Maps.newMap();
            item.put("name", s.path("name").asText());
            item.put("affiliation", s.path("affiliation").asText());
            item.put("site", host);
            item.put("url", host.isEmpty() ? "" : "https://" + host + "/");
            item.putAll(siteSearch(host, term, enTerm));
            list.add(item);
        }
        return Maps.of("tier", key, "label", label, "count", list.size(), "sources", list);
    }

    /**
     * 构造「进入该站检索该词」的深链。**不同网站要用不同的检索词**：
     *   - 中文站（中国政府网、中科院、术语在线）→ 用中文原词
     *   - 英文站（中国政府网英文版、教育部英文官网）→ 必须用英文译名，用中文词必然搜不到
     * 各站的检索参数名与编码方式也各不相同，统一由 search_templates.json v3 驱动。
     * 未配置可用深链的站点如实标注为 homepage / form，绝不假装能检索。
     *
     * @return url / search_kind / search_query / search_lang / search_label / search_note / search_probe
     */
    private Map<String, Object> siteSearch(String host, String zhTerm, String enTerm) {
        Map<String, Object> out = Maps.newMap();
        if (host == null || host.isEmpty()) {
            out.put("search_url", "");
            out.put("search_kind", "homepage");
            out.put("search_query", "");
            out.put("search_lang", "zh");
            out.put("search_label", "");
            out.put("search_note", "");
            out.put("search_probe", "");
            return out;
        }

        String base = "https://" + host;
        JsonNode cfg = data.read("sources/search_templates.json");
        JsonNode def = cfg == null ? null : cfg.path("default");
        JsonNode t = cfg == null ? null : cfg.path("templates").path(host);
        boolean configured = t != null && !t.isMissingNode() && !t.isNull();

        String kind = configured ? t.path("kind").asText("homepage")
                : (def != null && def.hasNonNull("kind") ? def.path("kind").asText("homepage") : "homepage");
        String lang = configured ? t.path("query_lang").asText("zh")
                : (def != null && def.hasNonNull("query_lang") ? def.path("query_lang").asText("zh") : "zh");
        String encMode = configured ? t.path("encode").asText("normal") : "normal";
        String label = configured ? t.path("label").asText("") : "";
        String note = configured ? t.path("note").asText("")
                : (def == null ? "" : def.path("note").asText(""));
        String probe = configured ? t.path("probe").asText("") : "";

        // 按站点要求挑选检索词：英文站用英文译名；若该词没有英文译名则退回中文并如实标注
        String query = zhTerm == null ? "" : zhTerm;
        String usedLang = "zh";
        if ("en".equals(lang)) {
            if (enTerm != null && !enTerm.isEmpty()) {
                query = enTerm;
                usedLang = "en";
            } else {
                usedLang = "zh-fallback";
                if (note.isEmpty()) {
                    note = "该站为英文站，宜用英文译名检索；本次未取得英文译名，暂以中文原词代替";
                }
            }
        }

        String url;
        if (configured && t.hasNonNull("url")) {
            String tpl = t.path("url").asText("");
            url = query.isEmpty() ? tpl : tpl.replace("{q}", enc(query, encMode));
        } else {
            url = base + "/";
        }

        out.put("search_url", url);
        out.put("search_kind", kind);
        out.put("search_query", query);
        out.put("search_lang", usedLang);
        out.put("search_label", label);
        out.put("search_note", note);
        out.put("search_probe", probe);
        return out;
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

    /** 单次 URL 编码。空格统一用 %20（而非 +），部分站点不解析 + 形式的空格 */
    private String encOnce(String s) {
        try {
            return java.net.URLEncoder.encode(s == null ? "" : s, "UTF-8").replace("+", "%20");
        } catch (Exception e) {
            return "";
        }
    }

    /** 按站点要求编码：normal 单次；double 双重（部分站点前端会再 decodeURI 一次，不双重编码会变乱码） */
    private String enc(String s, String mode) {
        String once = encOnce(s);
        return "double".equals(mode) ? encOnce(once) : once;
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
