package com.swpu.transflow.util;

import java.util.LinkedHashMap;
import java.util.Map;

/** Java 8 兼容的有序 Map 构造工具（替代 Map.of）。 */
public final class Maps {

    private Maps() {
    }

    /** 变长参数构造有序 Map：Maps.of("k1", v1, "k2", v2, ...) */
    public static Map<String, Object> of(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    public static Map<String, Object> newMap() {
        return new LinkedHashMap<>();
    }
}
