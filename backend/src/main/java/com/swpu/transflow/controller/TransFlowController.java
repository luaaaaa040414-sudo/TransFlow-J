package com.swpu.transflow.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.swpu.transflow.service.SourceTierService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import java.io.File;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 后端 API 入口。
 * 说明：为兼容 IDEA 2020.3 / Java 8，不使用 record、Map.of、List.of。
 */
@RestController
@RequestMapping("/api")
public class TransFlowController {

    private final SourceTierService sourceTierService;
    private final ObjectMapper mapper = new ObjectMapper();
    private final File dataDir;

    public TransFlowController(SourceTierService sourceTierService,
                               @Value("${transflow.data-dir}") String dataDir) {
        this.sourceTierService = sourceTierService;
        this.dataDir = new File(dataDir);
    }

    /** 信源分级清单 */
    @GetMapping("/sources/tiers")
    public ResponseEntity<?> sourceTiers() {
        return ResponseEntity.ok(sourceTierService.tierSummary());
    }

    /** 判定单个信源链接的等级 */
    @PostMapping("/sources/classify")
    public ResponseEntity<?> classify(@Valid @RequestBody ClassifyRequest req) {
        return ResponseEntity.ok(sourceTierService.classify(req.getUrl()));
    }

    /** 请求体：待判定的信源链接（普通静态类，便于 Jackson 反序列化） */
    public static class ClassifyRequest {
        @NotBlank(message = "url 不能为空")
        private String url;

        public String getUrl() { return url; }
        public void setUrl(String url) { this.url = url; }
    }

    /** 领域列表（来自 data/profiles/domains） */
    @GetMapping("/profiles/domains")
    public ResponseEntity<?> domains() throws Exception {
        File dir = new File(dataDir, "profiles/domains");
        List<Map<String, Object>> list = new ArrayList<>();
        File[] files = dir.listFiles((d, name) -> name.endsWith(".json"));
        if (files != null) {
            for (File f : files) {
                JsonNode node = mapper.readTree(f);
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("domain", node.path("domain").asText());
                m.put("domain_zh", node.path("domain_zh").asText());
                m.put("priority", node.path("priority").asInt());
                m.put("school_college", node.path("school_college").asText());
                list.add(m);
            }
        }
        return ResponseEntity.ok(list);
    }

    /** 单个领域的期刊列表（摊平各 subfield） */
    @GetMapping("/profiles/domains/{domain}")
    public ResponseEntity<?> domainDetail(@PathVariable String domain) throws Exception {
        File f = new File(dataDir, "profiles/domains/" + domain + ".json");
        if (!f.exists()) {
            return ResponseEntity.notFound().build();
        }
        JsonNode root = mapper.readTree(f);
        List<Map<String, Object>> journals = new ArrayList<>();
        JsonNode topJournals = root.path("journals");
        if (topJournals.isArray()) {
            topJournals.forEach(j -> journals.add(journal(j, "")));
        }
        for (JsonNode sub : root.path("subfields")) {
            String subName = sub.path("name").asText();
            for (JsonNode j : sub.path("journals")) {
                journals.add(journal(j, subName));
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("domain", root.path("domain").asText());
        result.put("domain_zh", root.path("domain_zh").asText());
        result.put("journal_count", journals.size());
        result.put("journals", journals);
        return ResponseEntity.ok(result);
    }

    private Map<String, Object> journal(JsonNode j, String subName) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("name", j.path("name").asText());
        m.put("publisher_zh", j.path("publisher_zh").asText());
        m.put("tier", j.path("tier").asText());
        m.put("open_access", j.path("open_access").isBoolean()
                ? j.path("open_access").asBoolean() : j.path("open_access").asText());
        m.put("collect_scope", j.path("collect_scope").asText());
        m.put("site", j.path("site").asText());
        m.put("note", j.path("note").asText());
        if (!subName.isEmpty()) {
            m.put("subfield", subName);
        }
        return m;
    }
}
