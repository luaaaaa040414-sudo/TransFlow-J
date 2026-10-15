package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.swpu.transflow.util.Maps;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Map;

/** 模型池目录：厂商 / 架构 / 聪明程度 / 是否已配 key。 */
@Service
public class ModelCatalogService {

    private final JsonDataService data;
    private final ObjectMapper mapper = new ObjectMapper();

    public ModelCatalogService(JsonDataService data) {
        this.data = data;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> catalog() {
        JsonNode root = data.read("models/models.json");
        if (root == null) {
            return Maps.of("models", Collections.emptyList(),
                    "roles", Collections.emptyMap(),
                    "capability_scale", Collections.emptyMap(),
                    "total", 0, "configured_count", 0);
        }
        Map<String, Object> r = mapper.convertValue(root, Map.class);
        r.remove("$comment");

        int total = 0;
        int configured = 0;
        for (JsonNode m : root.path("models")) {
            total++;
            if (m.path("configured").asBoolean(false)) {
                configured++;
            }
        }
        r.put("total", total);
        r.put("configured_count", configured);
        return r;
    }
}
