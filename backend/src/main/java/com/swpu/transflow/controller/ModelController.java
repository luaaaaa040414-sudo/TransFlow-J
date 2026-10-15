package com.swpu.transflow.controller;

import com.swpu.transflow.service.ModelCatalogService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 模型池目录接口。 */
@RestController
@RequestMapping("/api")
public class ModelController {

    private final ModelCatalogService modelCatalogService;

    public ModelController(ModelCatalogService modelCatalogService) {
        this.modelCatalogService = modelCatalogService;
    }

    /** 模型池：厂商 / 架构 / 聪明程度 / 是否已配 key */
    @GetMapping("/models")
    public ResponseEntity<?> models() {
        return ResponseEntity.ok(modelCatalogService.catalog());
    }
}
