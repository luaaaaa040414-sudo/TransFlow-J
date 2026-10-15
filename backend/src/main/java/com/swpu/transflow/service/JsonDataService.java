package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;

/** 统一读取 data/ 目录下 JSON 数据文件。 */
@Service
public class JsonDataService {

    private final ObjectMapper mapper = new ObjectMapper();
    private final File dataDir;

    public JsonDataService(@Value("${transflow.data-dir}") String dataDir) {
        this.dataDir = new File(dataDir);
    }

    public File dataDir() {
        return dataDir;
    }

    /** 读取相对 data/ 的 JSON；文件不存在返回 null。 */
    public JsonNode read(String relativePath) {
        File f = new File(dataDir, relativePath);
        if (!f.exists()) {
            return null;
        }
        try {
            return mapper.readTree(f);
        } catch (IOException e) {
            throw new IllegalStateException("读取数据文件失败: " + f.getAbsolutePath(), e);
        }
    }
}
