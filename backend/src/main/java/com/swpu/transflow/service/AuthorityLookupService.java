package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.swpu.transflow.util.Maps;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.URI;
import java.net.URLEncoder;
import java.text.Normalizer;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.security.cert.Certificate;
import java.security.cert.CertificateException;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * 权威译文直取：不经过搜索引擎，直接调用「全国科学技术名词审定委员会·术语在线」(termonline.cn)
 * 的站内检索接口，拿到该中文词对应的官方英文译名，供译前准备页「显示」译文。
 *
 * 仅接受正式审定库及标准库中的精确匹配条目，不将站内其他来源/百科视为一级证据。
 * drawWordSearch 单条推荐 → allSearch 审定库精确检索（match=1）→ standardSearch 标准库补查。
 * 每条证据保留独立的原文链接。网络、协议、分页失败与有效空结果分开报告。
 */
@Service
public class AuthorityLookupService {

    /** 术语在线站点根 */
    private static final String SITE = "https://www.termonline.cn";
    /** 一级源编号，与 data/sources/sources.json 保持一致 */
    private static final String SOURCE_ID = "T1-06";
    private static final String SOURCE_NAME = "全国术语在线";

    private static final String UA =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    + "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    private static final Logger log = LoggerFactory.getLogger(AuthorityLookupService.class);

    private final ObjectMapper mapper = new ObjectMapper();
    private final RestTemplate rest;

    public AuthorityLookupService() {
        SimpleClientHttpRequestFactory factory;
        SSLSocketFactory sf = buildSslSocketFactory();
        if (sf != null) {
            factory = new SslAwareRequestFactory(sf);
        } else {
            factory = new SimpleClientHttpRequestFactory();
        }
        factory.setConnectTimeout(2500);
        factory.setReadTimeout(5000);

        // 若运行环境通过 http(s)_proxy 环境变量指定了出口代理（容器 / 企业网常见），
        // 则让本服务的对外请求也走它；普通本机直连环境没有该变量，自动直连，无需配置。
        Proxy proxy = detectProxy();
        if (proxy != null) {
            factory.setProxy(proxy);
            log.info("[术语在线] 已启用出口代理 {}", proxy.address());
        }
        this.rest = new RestTemplate(factory);
    }

    // 正式审定库与标准库才可作为一级证据。站内“其他来源库”包含百科，不能按域名一概提级。
    private static final String APPROVED_DB = "00000000000000000000000000000000";
    private static final String STANDARD_DB = "00000000000000000000000000000007";
    private static final int PAGE_SIZE = 50;
    private static final int MAX_PAGES = 3;

    /** 供无网络回归测试注入 HTTP 客户端；生产仍使用上面的安全网络配置。 */
    AuthorityLookupService(RestTemplate rest) {
        this.rest = rest;
    }

    /** 统一处理复制/PDF 选词中的全角空格、零宽字符与中文断行，不改写词义。 */
    static String normalizeTerm(String term) {
        if (term == null) return "";
        return Normalizer.normalize(term, Normalizer.Form.NFKC)
                .replaceAll("[\\p{Cf}]", "")
                .replaceAll("[\\s\\p{Z}]+", " ")
                .replaceAll("(?<=[\\p{IsHan}]) +(?=[\\p{IsHan}])", "").trim();
    }

    public Map<String, Object> lookup(String term) {
        String q = normalizeTerm(term);
        if (q.isEmpty()) {
            return Maps.of("found", false, "term", "", "lookup_status", "invalid", "reason", "未提供待查词语");
        }
        // 所有诊断信息为本次请求局部变量，避免并发用户间串词或串错误。
        List<Map<String, Object>> trace = new ArrayList<>();
        List<Map<String, Object>> candidates = new ArrayList<>();
        JsonNode draw = getJson(api("drawWordSearch", q, 1, false), trace);
        if (draw != null && draw.path("result").isObject()) {
            JsonNode row = draw.path("result");
            String db = row.path("dbId").asText("");
            if ("0".equals(db) || APPROVED_DB.equals(db)) addCandidate(row, q, false, candidates);
        }

        // 推荐接口可能返回空值或没有英文的条目；仍须用官网正式检索接口查完整结果。
        boolean complete = search(q, false, candidates, trace);
        if (candidates.isEmpty()) {
            complete = search(q, true, candidates, trace) && complete;
        }
        Map<String, Object> out = Maps.of("found", !candidates.isEmpty(), "term", q,
                "engine", "termonline.cn", "tier", "tier1", "source_id", SOURCE_ID,
                "source_name", SOURCE_NAME, "homepage", SITE + "/",
                "search_url", SITE + "/search?searchText=" + enc(q), "checks", trace,
                "search_complete", complete, "coverage", "自动核查术语在线审定库（无命中时补查标准库），其他一级源仍需核验");
        if (!candidates.isEmpty()) {
            out.putAll(candidates.get(0));
            out.put("also_from", candidates);
            out.put("lookup_status", complete ? "found" : "partial");
            out.put("reason", complete ? "已取得与查询词精确匹配的一级源原始条目"
                    : "已取得一级源证据，但补充检索未完成；不能据此认定已覆盖所有译法");
        } else {
            out.put("lookup_status", complete ? "not_found" : "unavailable");
            out.put("reason", complete
                    ? "本次在术语在线审定库及标准库未取得精确匹配的英文条目，不代表其他一级源未收录；请继续核验一级源"
                    : "权威站点查询未完成（网络、接口或检索范围受限），无法判断是否收录；请重试或打开官网核验，不能据此降级定稿");
        }
        return out;
    }

    private String api(String endpoint, String q, int page, boolean standard) {
        return SITE + "/main-serve/business/tm/tmWord/" + endpoint + "?term=" + enc(q)
                + ("drawWordSearch".equals(endpoint) ? "" : "&match=1&sources=&pubYears=&pageSize="
                + PAGE_SIZE + "&pageNo=" + page + "&baseId=" + (standard ? STANDARD_DB : "1"));
    }

    /** match=1 是官网精确检索；分页有界，达到上限则明确标记未完成而不是谎报未收录。 */
    private boolean search(String q, boolean standard, List<Map<String, Object>> candidates,
                           List<Map<String, Object>> trace) {
        String endpoint = standard ? "standardSearch" : "allSearch";
        for (int page = 1; page <= MAX_PAGES; page++) {
            String url = api(endpoint, q, page, standard);
            JsonNode root = getJson(url, trace);
            if (root == null) return false;
            JsonNode result = root.path("result");
            // 官网同样会在全空响应后初始化库列表并重查一次，避免暂时空响应导致漏查。
            if (!standard && page == 1 && emptyGroups(result)) {
                getJson(SITE + "/main-serve/business/tm/tmDatabase/listFront?pageNo=1&pageSize=10", trace);
                root = getJson(url, trace);
                if (root == null) return false;
                result = root.path("result");
            }
            JsonNode group = standard ? result.path("standardVO") : approvedGroup(result);
            if (!group.isObject() || !group.path("tmWordList").isArray()
                    || !group.path("totalRecords").canConvertToInt()) {
                trace.add(Maps.of("endpoint", endpoint, "status", "protocol_error", "message", "检索响应结构不完整"));
                return false;
            }
            for (JsonNode row : group.path("tmWordList")) addCandidate(row, q, standard, candidates);
            int total = group.path("totalRecords").asInt();
            if (total < 0) return false;
            if (page * PAGE_SIZE >= total) return true;
            if (group.path("tmWordList").size() == 0) break;
        }
        trace.add(Maps.of("endpoint", endpoint, "status", "incomplete", "message", "结果分页尚未取全，需官网继续核验"));
        return false;
    }

    private JsonNode approvedGroup(JsonNode result) {
        for (JsonNode group : result.path("searchResult")) {
            if (APPROVED_DB.equals(group.path("id").asText())) return group.path("result");
        }
        return mapper.createObjectNode();
    }

    private boolean emptyGroups(JsonNode result) {
        JsonNode groups = result.path("searchResult");
        if (!groups.isArray() || groups.size() == 0) return false;
        for (JsonNode group : groups) {
            if (group.path("result").path("totalRecords").asInt(-1) != 0) return false;
        }
        return true;
    }

    private void addCandidate(JsonNode row, String q, boolean standard, List<Map<String, Object>> out) {
        String cn = clean(row.path(standard ? "cnName" : "cn").asText(""));
        String en = clean(row.path(standard ? "enName" : "en").asText(""));
        // 不能把相关词/包含该词的长词直接锁定为本词，也不把无英文条目当作翻译证据。
        if (!normalizeTerm(cn).equalsIgnoreCase(q) || en.isEmpty()) return;
        String id = row.path("id").asText("");
        String source = standard ? clean(row.path("standardCode").asText("") + " "
                + row.path("standardName").asText("")) : clean(row.path("source").asText(""));
        if (id.isEmpty() || source.isEmpty()) return;
        String db = standard ? STANDARD_DB : APPROVED_DB;
        String detail = SITE + (standard ? "/wordDetailByStandard" : "/wordDetail")
                + "?termName=" + enc(cn) + "&subject=" + enc(id) + "&base=" + db;
        for (Map<String, Object> existing : out) {
            if (detail.equals(existing.get("detail_url"))) return;
        }
        out.add(Maps.of("term", cn, "translation", en, "variants", splitVariants(en),
                "definition", clean(row.path("definition").asText("")), "termbase", source,
                "subject", clean(row.path("subjectFullName").asText(row.path("subjectName").asText(""))),
                "subject_name", clean(row.path("subjectName").asText("")),
                "publish_year", row.path("publishYear").asText(""),
                "word_number", row.path(standard ? "termCode" : "wordNumber").asText(""),
                "also_name", clean(row.path("alsoName").asText("")), "tw", clean(row.path("tw").asText("")),
                "site", SITE, "detail_url", detail, "database_id", db,
                "quote", joinQuote(clean(row.path("quote1").asText("")), clean(row.path("quote2").asText("")))));
    }

    private String clean(String text) {
        return text.replaceAll("<[^>]*>", "").replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"")
                .replaceAll("[\\s\\p{Z}]+", " ").trim();
    }

    /** 请求失败与有效的空结果分别记录，绝不把超时/拦截/改版描述成“未收录”。 */
    private JsonNode getJson(String url, List<Map<String, Object>> trace) {
        // 限制最坏网络耗时（6 次 × 单次连接/读取超时），低于前端请求超时。
        long requests = trace.stream().filter(t -> t.containsKey("url")).count();
        if (requests >= 6) {
            trace.add(Maps.of("endpoint", "budget", "status", "incomplete", "message", "已达本次请求上限"));
            return null;
        }
        Map<String, Object> check = Maps.of("url", url, "status", "error");
        trace.add(check);
        try {
            HttpHeaders h = new HttpHeaders();
            h.set("User-Agent", UA);
            h.set("Referer", SITE + "/");
            h.set("Accept", "application/json, text/plain, */*");
            // 传 URI，避免 RestTemplate 把已编码中文二次编码。
            ResponseEntity<String> resp = rest.exchange(new URI(url), HttpMethod.GET,
                    new HttpEntity<String>(h), String.class);
            String body = resp.getBody();
            if (body == null || body.trim().isEmpty()) throw new IOException("空响应");
            JsonNode root = mapper.readTree(body);
            if (root == null || !root.isObject() || !root.has("result")
                    || (root.hasNonNull("code") && root.path("code").asInt(-1) != 200)
                    || (root.has("success") && !root.path("success").asBoolean())) {
                throw new IOException("接口状态或响应格式异常: " + brief(body));
            }
            check.put("status", "ok");
            return root;
        } catch (Exception e) {
            String message = e.toString();
            String hint = message.contains("SSL") || message.contains("PKIX")
                    ? "HTTPS 证书校验失败；请检查系统可信根或配置可信 CA 包，勿关闭证书校验。"
                    : message.toLowerCase(java.util.Locale.ROOT).contains("timed out")
                    ? "权威站点连接或读取超时，请稍后重试。" : "权威站点请求或响应异常，请重试或官网核验。";
            check.put("message", hint);
            check.put("error_detail", message);
            log.warn("[术语在线] 请求失败 url={} err={}", url, e.toString());
            return null;
        }
    }

    // ==================== 网络环境适配 ====================

    /** "petroleum; oil" → ["petroleum","oil"]（分号/中文分号/斜杠均可分隔） */
    private List<String> splitVariants(String en) {
        List<String> out = new ArrayList<>();
        if (en == null || en.isEmpty()) {
            return out;
        }
        String[] parts = en.split("[;；/]");
        for (String p : parts) {
            String v = p.trim();
            if (!v.isEmpty()) {
                out.add(v);
            }
        }
        return out.isEmpty() ? Collections.singletonList(en) : out;
    }

    private String joinQuote(String q1, String q2) {
        StringBuilder sb = new StringBuilder();
        if (q1 != null && !q1.isEmpty()) {
            sb.append(q1);
        }
        if (q2 != null && !q2.isEmpty()) {
            if (sb.length() > 0) {
                sb.append("；");
            }
            sb.append(q2);
        }
        return sb.toString();
    }

    private String enc(String s) {
        try {
            return URLEncoder.encode(s == null ? "" : s, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    /** 日志用：截断响应体，避免刷屏 */
    private String brief(String body) {
        if (body == null) {
            return "<null>";
        }
        String s = body.replaceAll("\\s+", " ").trim();
        return s.length() > 200 ? s.substring(0, 200) + "..." : s;
    }

    /** 从环境变量读取出口代理；没有则返回 null（直连） */
    private Proxy detectProxy() {
        String p = System.getenv("HTTPS_PROXY");
        if (isBlank(p)) {
            p = System.getenv("https_proxy");
        }
        if (isBlank(p)) {
            p = System.getenv("HTTP_PROXY");
        }
        if (isBlank(p)) {
            p = System.getenv("http_proxy");
        }
        if (isBlank(p)) {
            return null;
        }
        try {
            URI u = URI.create(p.trim());
            String host = u.getHost();
            if (host == null || host.isEmpty()) {
                return null;
            }
            int port = u.getPort() > 0 ? u.getPort() : 80;
            return new Proxy(Proxy.Type.HTTP, new InetSocketAddress(host, port));
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 默认 JDK 信任库 + Windows 系统可信根 + 可选 PEM，保持证书链和域名校验。
     * 老 JDK 的 CA 库可能无法验证浏览器已经信任的官网证书，因此仅有 PEM 适配还不够。
     * 使用 Java 官方 SunMSCAPI 的 Windows-ROOT，不导入远程自签证书、不改全局信任库。
     */
    private SSLSocketFactory buildSslSocketFactory() {
        try {
            X509TrustManager trusted = defaultTrustManager();
            boolean enhanced = false;
            if (System.getProperty("os.name", "").toLowerCase(java.util.Locale.ROOT).startsWith("windows")) {
                try {
                    KeyStore windows = KeyStore.getInstance("Windows-ROOT");
                    windows.load(null, null);
                    TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
                    tmf.init(windows);
                    trusted = new CompositeTrustManager(trusted, firstX509(tmf));
                    enhanced = true;
                    log.info("[术语在线] 已并入 Windows 系统可信根证书（保留 HTTPS 校验）");
                } catch (Exception e) {
                    log.warn("[术语在线] 无法读取 Windows 可信根，继续使用 JDK 信任库：{}", e.toString());
                }
            }
            String pem = System.getenv("NODE_EXTRA_CA_CERTS");
            if (isBlank(pem)) pem = System.getenv("SSL_CERT_FILE");
            if (!isBlank(pem)) {
                try {
                    trusted = new CompositeTrustManager(trusted, pemTrustManager(new File(pem.trim())));
                    enhanced = true;
                    log.info("[术语在线] 已并入系统 CA 包：{}", pem);
                } catch (Exception e) {
                    log.warn("[术语在线] 额外 CA 包加载失败，保留现有信任链：{}", e.toString());
                }
            }
            if (!enhanced) return null;
            SSLContext ctx = SSLContext.getInstance("TLS");
            ctx.init(null, new TrustManager[]{trusted}, new SecureRandom());
            return ctx.getSocketFactory();
        } catch (Exception e) {
            log.warn("[术语在线] 增强信任链构建失败，回退 JDK 默认信任库：{}", e.toString());
            return null;
        }
    }

    private X509TrustManager defaultTrustManager() throws Exception {
        TrustManagerFactory tmf =
                TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init((KeyStore) null);
        return firstX509(tmf);
    }

    private X509TrustManager pemTrustManager(File pemFile) throws Exception {
        CertificateFactory cf = CertificateFactory.getInstance("X.509");
        Collection<? extends Certificate> certs;
        InputStream in = new FileInputStream(pemFile);
        try {
            certs = cf.generateCertificates(in);
        } finally {
            in.close();
        }
        KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
        ks.load(null, null);
        int i = 0;
        for (Certificate c : certs) {
            ks.setCertificateEntry("sysca-" + (i++), c);
        }
        TrustManagerFactory tmf =
                TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(ks);
        return firstX509(tmf);
    }

    private X509TrustManager firstX509(TrustManagerFactory tmf) {
        for (TrustManager tm : tmf.getTrustManagers()) {
            if (tm instanceof X509TrustManager) {
                return (X509TrustManager) tm;
            }
        }
        throw new IllegalStateException("未找到可用的 X509TrustManager");
    }

    private boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }

    /** 组合信任管理器：先按 JDK 默认库校验，不通过再按系统 CA 包校验 */
    private static final class CompositeTrustManager implements X509TrustManager {
        private final X509TrustManager primary;
        private final X509TrustManager secondary;

        CompositeTrustManager(X509TrustManager primary, X509TrustManager secondary) {
            this.primary = primary;
            this.secondary = secondary;
        }

        @Override
        public void checkClientTrusted(X509Certificate[] chain, String authType)
                throws CertificateException {
            try {
                primary.checkClientTrusted(chain, authType);
            } catch (CertificateException e) {
                secondary.checkClientTrusted(chain, authType);
            }
        }

        @Override
        public void checkServerTrusted(X509Certificate[] chain, String authType)
                throws CertificateException {
            try {
                primary.checkServerTrusted(chain, authType);
            } catch (CertificateException e) {
                secondary.checkServerTrusted(chain, authType);
            }
        }

        @Override
        public X509Certificate[] getAcceptedIssuers() {
            X509Certificate[] a = primary.getAcceptedIssuers();
            X509Certificate[] b = secondary.getAcceptedIssuers();
            X509Certificate[] all = new X509Certificate[a.length + b.length];
            System.arraycopy(a, 0, all, 0, a.length);
            System.arraycopy(b, 0, all, a.length, b.length);
            return all;
        }
    }

    /** 让 SimpleClientHttpRequestFactory 用上自定义 SSLSocketFactory */
    private static final class SslAwareRequestFactory extends SimpleClientHttpRequestFactory {
        private final SSLSocketFactory sslSocketFactory;

        SslAwareRequestFactory(SSLSocketFactory sslSocketFactory) {
            this.sslSocketFactory = sslSocketFactory;
        }

        @Override
        protected void prepareConnection(HttpURLConnection connection, String httpMethod)
                throws IOException {
            if (connection instanceof HttpsURLConnection) {
                ((HttpsURLConnection) connection).setSSLSocketFactory(sslSocketFactory);
            }
            super.prepareConnection(connection, httpMethod);
        }
    }
}
