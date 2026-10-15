package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.swpu.transflow.util.Maps;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.util.Collections;
import java.util.Map;

/**
 * 期刊风格翻译：按所选期刊对文本做「成段 / 整篇」翻译。
 * 优先调用 ML 服务（ml/app.py）里的风格模型；服务未启动时降级返回风格约束卡与明确状态。
 */
@Service
public class StyleService {

    private final JsonDataService data;
    private final RestTemplate rest;
    private final String mlServiceUrl;

    public StyleService(JsonDataService data,
                        @Value("${transflow.ml-service-url:}") String mlServiceUrl) {
        this.data = data;
        this.mlServiceUrl = mlServiceUrl == null ? "" : mlServiceUrl.trim();
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(2000);
        factory.setReadTimeout(120000);
        this.rest = new RestTemplate(factory);
    }

    public Map<String, Object> translate(String journal, String text, String scope, String modelId) {
        if (text == null || text.trim().isEmpty()) {
            return Maps.of("status", "invalid", "message", "请先输入要翻译的文本");
        }
        String scopeValue = (scope == null || scope.isEmpty()) ? "paragraph" : scope;
        Map<String, Object> styleCard = styleCard(journal);

        // 1. 尝试调用 ML 服务
        if (!mlServiceUrl.isEmpty()) {
            try {
                Map<String, Object> body = Maps.of(
                        "journal", journal,
                        "text", text,
                        "scope", scopeValue,
                        "model", modelId);
                @SuppressWarnings("unchecked")
                Map<String, Object> resp = rest.postForObject(mlServiceUrl + "/style/translate", body, Map.class);
                if (resp != null) {
                    Map<String, Object> r = Maps.newMap();
                    r.putAll(resp);
                    r.put("style_card", styleCard);
                    r.put("engine", "ml-service");
                    return r;
                }
            } catch (Exception ignored) {
                // 降级到下方
            }
        }

        // 2. 降级：返回风格约束卡
        Map<String, Object> r = Maps.newMap();
        r.put("status", "model_unavailable");
        r.put("message", "期刊风格模型服务未启动（ml/app.py 未运行）。已按所选期刊生成风格约束卡，启动模型服务后即可翻译。");
        r.put("journal", journal);
        r.put("scope", scopeValue);
        r.put("style_card", styleCard);
        r.put("engine", "none");
        return r;
    }

    /** 生成该期刊的风格约束卡（期刊元信息 + 通用学术风格约束） */
    private Map<String, Object> styleCard(String journal) {
        Map<String, Object> card = Maps.newMap();
        card.put("journal", journal);

        Map<String, Object> found = findJournal(journal);
        if (found != null) {
            card.put("domain", found.get("domain"));
            card.put("domain_zh", found.get("domain_zh"));
            card.put("tier", found.get("tier"));
            card.put("publisher_zh", found.get("publisher_zh"));
            card.put("note", found.get("note"));
        } else {
            card.put("domain", "generic");
            card.put("domain_zh", "通用学术风格");
        }

        card.put("register", "正式学术书面语");
        card.put("person", "第三人称，以客观陈述与适度被动语态为主");
        card.put("terminology", "术语严格对齐权威信源，禁止随意同义替换");
        card.put("sentence", "允许长句，但须避免口语化、冗余与中式英语");
        card.put("numbers", "数字、单位、缩写遵循期刊惯例（如 SPE、EOR、MPa）");
        return card;
    }

    /** 在各领域期刊库中按名称查找期刊 */
    private Map<String, Object> findJournal(String name) {
        if (name == null || name.trim().isEmpty()) {
            return null;
        }
        File dir = new File(data.dataDir(), "profiles/domains");
        File[] files = dir.listFiles((d, n) -> n.endsWith(".json"));
        if (files == null) {
            return null;
        }
        for (File f : files) {
            JsonNode root = data.read("profiles/domains/" + f.getName());
            if (root == null) {
                continue;
            }
            Map<String, Object> hit = matchIn(root.path("journals"), root, name);
            if (hit != null) {
                return hit;
            }
            for (JsonNode sub : root.path("subfields")) {
                hit = matchIn(sub.path("journals"), root, name);
                if (hit != null) {
                    return hit;
                }
            }
        }
        return null;
    }

    private Map<String, Object> matchIn(JsonNode journals, JsonNode domainRoot, String name) {
        for (JsonNode j : journals) {
            if (j.path("name").asText().equalsIgnoreCase(name)) {
                return Maps.of(
                        "domain", domainRoot.path("domain").asText(),
                        "domain_zh", domainRoot.path("domain_zh").asText(),
                        "tier", j.path("tier").asText(),
                        "publisher_zh", j.path("publisher_zh").asText(),
                        "note", j.path("note").asText());
            }
        }
        return null;
    }
}
