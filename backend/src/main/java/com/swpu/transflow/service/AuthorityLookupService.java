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
 * 依据信源分级：termonline.cn = T1-06 一级源，命中即可直接作为定译依据。
 *
 * 站内接口（公开、无鉴权）：
 *   GET /main-serve/business/tm/tmWord/drawWordSearch?term={中文词}
 *        → 单条术语详情：cn / en / definition / source(术语库) / subjectFullName / publishYear / wordNumber / id
 *   GET /main-serve/business/tm/tmWord/standardSearch?term={中文词}&match=2&pageNo=1&pageSize=20&baseId=...07
 *        → 多库总览：overView.en[] / overView.source[]，用于列出「有哪些术语库给出过译名」
 *
 * 网络不可达或站点改版时，返回 found=false + 明确原因，由上层降级到分级查证方案，绝不臆造译文。
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
        factory.setConnectTimeout(4000);
        factory.setReadTimeout(12000);

        // 若运行环境通过 http(s)_proxy 环境变量指定了出口代理（容器 / 企业网常见），
        // 则让本服务的对外请求也走它；普通本机直连环境没有该变量，自动直连，无需配置。
        Proxy proxy = detectProxy();
        if (proxy != null) {
            factory.setProxy(proxy);
            log.info("[术语在线] 已启用出口代理 {}", proxy.address());
        }
        this.rest = new RestTemplate(factory);
    }

    /**
     * 查一个中文词的权威英文译名。
     *
     * @param term 待查证的中文词
     * @return found=true 时含 translation(英文译名) / termbase / subject / definition 等；
     *         found=false 时含 reason，供上层降级。
     */
    public Map<String, Object> lookup(String term) {
        String q = term == null ? "" : term.trim();
        if (q.isEmpty()) {
            return Maps.of("found", false, "term", "", "reason", "未提供待查词语");
        }

        Map<String, Object> detail = fetchDetail(q);
        if (detail != null) {
            detail.put("found", true);
            detail.put("engine", "termonline.cn");
            detail.put("tier", "tier1");
            detail.put("source_id", SOURCE_ID);
            detail.put("source_name", SOURCE_NAME);
            // 多库总览（失败不影响主结果）
            detail.put("also_from", fetchSourceOverview(q));
            return detail;
        }

        Map<String, Object> miss = Maps.newMap();
        miss.put("found", false);
        miss.put("term", q);
        miss.put("engine", "termonline.cn");
        miss.put("tier", "tier1");
        miss.put("source_id", SOURCE_ID);
        miss.put("source_name", SOURCE_NAME);
        miss.put("reason", "一级源「术语在线」未收录该词，按策略降级到二级源交叉核查（三级源一律不用）");
        miss.put("homepage", SITE + "/");
        miss.put("search_url", SITE + "/search?searchText=" + enc(q));
        return miss;
    }

    /** 单条术语详情 */
    private Map<String, Object> fetchDetail(String term) {
        String url = SITE + "/main-serve/business/tm/tmWord/drawWordSearch?term=" + enc(term);
        JsonNode root = getJson(url, SITE + "/");
        if (root == null) {
            return null;
        }
        JsonNode r = root.path("result");
        if (r.isMissingNode() || r.isNull()) {
            return null;
        }
        String cn = r.path("cn").asText("");
        String en = r.path("en").asText("");
        if (cn.isEmpty() || en.isEmpty()) {
            return null;
        }

        Map<String, Object> m = Maps.newMap();
        m.put("term", cn);
        m.put("translation", en);
        m.put("variants", splitVariants(en));
        m.put("definition", r.path("definition").asText(""));
        m.put("termbase", r.path("source").asText(""));
        m.put("subject", r.path("subjectFullName").asText(""));
        m.put("subject_name", r.path("subjectName").asText(""));
        m.put("publish_year", r.path("publishYear").asText(""));
        m.put("word_number", r.path("wordNumber").asText(""));
        m.put("also_name", r.path("alsoName").asText(""));
        m.put("tw", r.path("tw").isNull() ? "" : r.path("tw").asText(""));

        String id = r.path("id").asText("");
        m.put("site", SITE);
        m.put("detail_url", SITE + "/wordDetail?termName=" + enc(cn) + "&subject=" + enc(id) + "&base=1");
        m.put("quote", joinQuote(r.path("quote1").asText(""), r.path("quote2").asText("")));
        return m;
    }

    /** 多术语库总览：有哪些库给过译名（用于「权威翻译证明」的横向罗列） */
    private List<Map<String, Object>> fetchSourceOverview(String term) {
        String url = SITE + "/main-serve/business/tm/tmWord/standardSearch?term=" + enc(term)
                + "&match=2&sources=&pubYears=&pageSize=20&pageNo=1"
                + "&baseId=00000000000000000000000000000007";
        JsonNode root = getJson(url, SITE + "/");
        List<Map<String, Object>> list = new ArrayList<>();
        if (root == null) {
            return list;
        }
        JsonNode ov = root.path("result").path("overView");
        JsonNode ens = ov.path("en");
        JsonNode srcs = ov.path("source");
        int n = Math.max(ens.size(), srcs.size());
        for (int i = 0; i < n; i++) {
            String en = i < ens.size() && !ens.get(i).isNull() ? ens.get(i).asText("") : "";
            String src = i < srcs.size() && !srcs.get(i).isNull() ? srcs.get(i).asText("") : "";
            // 只保留真正给出译名的条目；仅有库名无译名的（如「建筑学名词」）不展示
            if (en.isEmpty()) {
                continue;
            }
            list.add(Maps.of("translation", en, "termbase", src));
        }
        return list;
    }

    /** 带 UA / Referer 抓 JSON；失败返回 null（不抛异常，交由上层降级） */
    private JsonNode getJson(String url, String referer) {
        try {
            HttpHeaders h = new HttpHeaders();
            h.set("User-Agent", UA);
            h.set("Referer", referer);
            h.set("Accept", "application/json, text/plain, */*");
            // 必须传 URI 对象：若传 String，RestTemplate 会把 URL 中已编码的 %E7 再编码成 %25E7，
            // 服务端拿到的是字面量而非中文词，导致查不到结果。
            URI uri = new URI(url);
            ResponseEntity<String> resp =
                    rest.exchange(uri, HttpMethod.GET, new HttpEntity<String>(h), String.class);
            String body = resp.getBody();
            if (body == null || body.trim().isEmpty()) {
                return null;
            }
            JsonNode root = mapper.readTree(body);
            if (root.hasNonNull("code") && root.path("code").asInt() != 200) {
                log.warn("[术语在线] 非 200 响应 url={} body={}", url, brief(body));
                return null;
            }
            if (!root.hasNonNull("result")) {
                log.warn("[术语在线] 响应缺少 result 字段 url={} body={}", url, brief(body));
            }
            return root;
        } catch (Exception e) {
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
     * 构建 HTTPS 信任链：在 JDK 默认信任库之外，额外并入系统 CA 包
     * （NODE_EXTRA_CA_CERTS / SSL_CERT_FILE 指向的 PEM）。
     * 企业代理或容器环境常在此处存放自签根证书；普通本机无该变量时直接返回 null，走 JDK 默认校验。
     * 注意：这只是「增加可信来源」，不会关闭证书校验。
     */
    private SSLSocketFactory buildSslSocketFactory() {
        String pem = System.getenv("NODE_EXTRA_CA_CERTS");
        if (isBlank(pem)) {
            pem = System.getenv("SSL_CERT_FILE");
        }
        if (isBlank(pem)) {
            return null;
        }
        File f = new File(pem.trim());
        if (!f.isFile()) {
            return null;
        }
        try {
            X509TrustManager def = defaultTrustManager();
            X509TrustManager extra = pemTrustManager(f);
            SSLContext ctx = SSLContext.getInstance("TLS");
            ctx.init(null, new TrustManager[]{new CompositeTrustManager(def, extra)}, new SecureRandom());
            log.info("[术语在线] 已并入系统 CA 包以增强 HTTPS 信任链：{}", f.getPath());
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
