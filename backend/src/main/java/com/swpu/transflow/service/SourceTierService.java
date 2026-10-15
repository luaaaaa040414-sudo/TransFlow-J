package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.File;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 信源分级器：加载 data/sources/sources.json，对任意 URL 判定所属等级。
 * 规则：
 *   - 命中三级源（黑名单）→ 直接拦截，等级优先
 *   - 命中一级源 → 可定译
 *   - 命中二级源 → 需交叉验证
 *   - 兜底：*.edu.cn（非本校域名）判为二级；其余未识别 → 待人工确认
 *
 * 说明：为兼容 IDEA 2020.3 / Java 8，本类不使用 record、Map.of、List.of。
 */
@Service
public class SourceTierService {

    @Value("${transflow.data-dir}")
    private String dataDir;

    private JsonNode tiers;
    private final ObjectMapper mapper = new ObjectMapper();

    /** 信源条目（普通静态类，兼容旧版 IDE） */
    public static class SourceItem {
        private final String id;
        private final String name;
        private final String affiliation;
        private final int hits;
        private final List<String> domains;

        public SourceItem(String id, String name, String affiliation, int hits, List<String> domains) {
            this.id = id;
            this.name = name;
            this.affiliation = affiliation;
            this.hits = hits;
            this.domains = domains;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getAffiliation() { return affiliation; }
        public int getHits() { return hits; }
        public List<String> getDomains() { return domains; }
    }

    @PostConstruct
    public void init() throws Exception {
        File file = new File(dataDir, "sources/sources.json");
        if (!file.exists()) {
            throw new IllegalStateException("信源清单不存在: " + file.getAbsolutePath());
        }
        tiers = mapper.readTree(file).get("tiers");
    }

    /** 判定 URL 等级，返回 tier / tierLabel / matched / reason */
    public Map<String, Object> classify(String url) {
        String host = extractHost(url);
        if (host == null) {
            return map("tier", "unknown", "tierLabel", "无法解析", "matched", false,
                    "reason", "不是合法 URL，需人工确认");
        }

        // 1. 黑名单优先
        String black = matchInTier(host, "tier3");
        if (black != null) {
            return map("tier", "tier3", "tierLabel", "三级源（黑名单）", "matched", true,
                    "matchedName", black, "reason", "命中黑名单，禁止作为术语证据");
        }

        // 2. 一级源
        String top = matchInTier(host, "tier1");
        if (top != null) {
            return map("tier", "tier1", "tierLabel", "一级源", "matched", true,
                    "matchedName", top, "reason", "官方权威来源，可直接作为定译依据");
        }

        // 3. 二级源
        String second = matchInTier(host, "tier2");
        if (second != null) {
            return map("tier", "tier2", "tierLabel", "二级源", "matched", true,
                    "matchedName", second, "reason", "有学术价值但非官方定稿，需两个独立二级源交叉验证");
        }

        // 4. 兜底规则
        if (host.endsWith(".edu.cn") && !host.contains("swpu.edu.cn")) {
            return map("tier", "tier2", "tierLabel", "二级源（兜底）", "matched", false,
                    "reason", "高校域名，本校未在一级清单中，按二级处理");
        }
        return map("tier", "unknown", "tierLabel", "待人工确认", "matched", false,
                "reason", "未命中任何分级信源，需人工逐一确认（短链尤其注意）");
    }

    /** 取出完整分级清单给前端渲染 */
    public Map<String, Object> tierSummary() {
        Map<String, Object> result = new LinkedHashMap<>();
        Iterator<String> fields = tiers.fieldNames();
        while (fields.hasNext()) {
            String key = fields.next();
            JsonNode node = tiers.get(key);
            List<SourceItem> items = new ArrayList<>();
            node.path("sources").forEach(s -> items.add(new SourceItem(
                    s.path("id").asText(), s.path("name").asText(),
                    s.path("affiliation").asText(), s.path("hits").asInt(0),
                    readDomains(s))));
            result.put(key, map(
                    "label", node.path("label").asText(),
                    "rule", node.path("rule").asText(),
                    "sources", items));
        }
        return result;
    }

    /** 读取 sources[].domains 数组；缺失或非数组时返回空列表 */
    private List<String> readDomains(JsonNode source) {
        JsonNode domains = source.path("domains");
        if (domains.isMissingNode() || !domains.isArray()) {
            return Collections.emptyList();
        }
        List<String> list = new ArrayList<>();
        domains.forEach(d -> list.add(d.asText()));
        return list;
    }

    private String matchInTier(String host, String tierKey) {
        JsonNode node = tiers.path(tierKey).path("sources");
        for (JsonNode s : node) {
            for (JsonNode d : s.path("domains")) {
                if (hostMatches(host, d.asText())) {
                    return s.path("name").asText();
                }
            }
        }
        return null;
    }

    private boolean hostMatches(String host, String pattern) {
        return host.equals(pattern) || host.endsWith("." + pattern);
    }

    private String extractHost(String url) {
        try {
            String withScheme = url.contains("://") ? url : "http://" + url;
            URI uri = new URI(withScheme);
            String host = uri.getHost();
            return host == null ? null : host.toLowerCase().replaceAll("^www\\.", "");
        } catch (URISyntaxException e) {
            return null;
        }
    }

    /** Java 8 兼容：变长参数构造有序 Map（替代 Map.of） */
    private static Map<String, Object> map(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }
}
