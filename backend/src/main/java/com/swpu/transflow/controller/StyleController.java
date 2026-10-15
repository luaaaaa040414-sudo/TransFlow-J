package com.swpu.transflow.controller;

import com.swpu.transflow.service.StyleService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 期刊风格翻译接口（成段 / 整篇）。 */
@RestController
@RequestMapping("/api")
public class StyleController {

    private final StyleService styleService;

    public StyleController(StyleService styleService) {
        this.styleService = styleService;
    }

    /** 请求体：期刊 + 文本 + 粒度(paragraph|full) + 可选模型 */
    public static class StyleRequest {
        private String journal;
        private String text;
        private String scope;
        private String model;

        public String getJournal() { return journal; }
        public void setJournal(String journal) { this.journal = journal; }
        public String getText() { return text; }
        public void setText(String text) { this.text = text; }
        public String getScope() { return scope; }
        public void setScope(String scope) { this.scope = scope; }
        public String getModel() { return model; }
        public void setModel(String model) { this.model = model; }
    }

    @PostMapping("/style/translate")
    public ResponseEntity<?> translate(@RequestBody StyleRequest req) {
        return ResponseEntity.ok(
                styleService.translate(req.getJournal(), req.getText(), req.getScope(), req.getModel()));
    }
}
