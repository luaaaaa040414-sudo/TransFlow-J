package com.swpu.transflow.controller;

import com.swpu.transflow.service.TermPrepService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 译前准备：术语查证接口。 */
@RestController
@RequestMapping("/api")
public class PrepController {

    private final TermPrepService termPrepService;

    public PrepController(TermPrepService termPrepService) {
        this.termPrepService = termPrepService;
    }

    /** 请求体：待查证的词语 + 可选上下文 */
    public static class TermRequest {
        private String term;
        private String context;

        public String getTerm() { return term; }
        public void setTerm(String term) { this.term = term; }
        public String getContext() { return context; }
        public void setContext(String context) { this.context = context; }
    }

    /** 术语查证：判定领域 → 分级信源检索 → 返回译文与权威证据 */
    @PostMapping("/term/analyze")
    public ResponseEntity<?> analyze(@RequestBody TermRequest req) {
        return ResponseEntity.ok(termPrepService.analyze(req.getTerm(), req.getContext()));
    }

    /** 直取一级源权威译文：不经过搜索引擎，返回该中文词在「术语在线」的官方英文译名 */
    @PostMapping("/term/authority")
    public ResponseEntity<?> authority(@RequestBody TermRequest req) {
        return ResponseEntity.ok(termPrepService.authorityLookup(req.getTerm()));
    }
}
