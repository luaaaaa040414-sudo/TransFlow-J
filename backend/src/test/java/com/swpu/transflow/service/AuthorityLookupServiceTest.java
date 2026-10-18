package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.swpu.transflow.util.Maps;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AuthorityLookupServiceTest {
    private static final String BASE = "https://www.termonline.cn/main-serve/business/tm/";
    private static final String DB = "00000000000000000000000000000000";
    private final ObjectMapper mapper = new ObjectMapper();
    private MockRestServiceServer server;
    private AuthorityLookupService service;

    @BeforeEach
    void setup() {
        RestTemplate rest = new RestTemplate();
        server = MockRestServiceServer.bindTo(rest).build();
        service = new AuthorityLookupService(rest);
    }

    private String url(String endpoint, String encoded, int page) {
        return BASE + "tmWord/" + endpoint + "?term=" + encoded
                + (endpoint.equals("drawWordSearch") ? "" : "&match=1&sources=&pubYears=&pageSize=50&pageNo="
                + page + "&baseId=" + (endpoint.equals("standardSearch")
                ? "00000000000000000000000000000007" : "1"));
    }

    private void reply(String endpoint, String encoded, int page, Object result) throws Exception {
        server.expect(requestTo(url(endpoint, encoded, page))).andRespond(withSuccess(
                mapper.writeValueAsString(Maps.of("success", true, "code", 200, "result", result)), MediaType.APPLICATION_JSON));
    }

    private Map<String, Object> row(String term, String en, String id) {
        return Maps.of("cn", term, "en", en, "id", id, "dbId", "0", "source", "计算机科学技术名词");
    }

    private Map<String, Object> groups(int total, Object... rows) {
        return Maps.of("searchResult", Collections.singletonList(Maps.of("id", DB,
                "result", Maps.of("totalRecords", total, "tmWordList", Arrays.asList(rows)))));
    }

    @Test
    void fallsBackToExactSearchWhenRecommendationIsEmptyAndEncodesChineseOnce() throws Exception {
        String encoded = "%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD";
        reply("drawWordSearch", encoded, 1, null);
        reply("allSearch", encoded, 1, groups(1, row("人工智能", "artificial intelligence", "ai")));
        Map<String, Object> out = service.lookup("　人\n工\u200B智能　");
        assertEquals(true, out.get("found"));
        assertEquals("artificial intelligence", out.get("translation"));
        assertEquals("found", out.get("lookup_status"));
        assertTrue(out.get("detail_url").toString().endsWith("&base=" + DB));
        server.verify();
    }

    @Test
    void supplementsNoEnglishRecommendationWithExactStandardEntry() throws Exception {
        reply("drawWordSearch", "term", 1, row("term", "", "empty"));
        reply("allSearch", "term", 1, groups(1, row("term", "", "empty")));
        reply("standardSearch", "term", 1, Maps.of("standardVO", Maps.of("totalRecords", 1,
                "tmWordList", Collections.singletonList(Maps.of("cnName", "term", "enName", "<em>official</em>&nbsp;term",
                        "id", "standard", "standardCode", "GB/T 1", "standardName", "标准")))));
        Map<String, Object> out = service.lookup("term");
        assertEquals("official term", out.get("translation"));
        assertTrue(out.get("detail_url").toString().contains("wordDetailByStandard"));
        assertEquals(true, out.get("search_complete"));
        server.verify();
    }

    @Test
    void neverAcceptsRelatedTermsOrThirdPartyEncyclopediaAsTierOne() throws Exception {
        reply("drawWordSearch", "term", 1, Maps.of("cn", "term", "en", "wiki translation", "dbId", "2",
                "id", "wiki", "source", "维基百科"));
        Map<String, Object> results = groups(1, row("longer term", "unrelated", "other"));
        @SuppressWarnings("unchecked") List<Object> groups = (List<Object>) results.get("searchResult");
        results.put("searchResult", Arrays.asList(groups.get(0), Maps.of("id", "00000000000000000000000000000002",
                "result", Maps.of("totalRecords", 1, "tmWordList", Collections.singletonList(row("term", "wrong", "wiki"))))));
        reply("allSearch", "term", 1, results);
        reply("standardSearch", "term", 1, Maps.of("standardVO", Maps.of("totalRecords", 0, "tmWordList", Collections.emptyList())));
        Map<String, Object> out = service.lookup("term");
        assertEquals(false, out.get("found"));
        assertEquals("not_found", out.get("lookup_status"));
        assertTrue(out.get("reason").toString().contains("不代表其他一级源"));
        server.verify();
    }

    @Test
    void retriesAfterInitializingLibrariesForTransientEmptySearch() throws Exception {
        reply("drawWordSearch", "term", 1, null);
        reply("allSearch", "term", 1, groups(0));
        server.expect(requestTo(BASE + "tmDatabase/listFront?pageNo=1&pageSize=10"))
                .andRespond(withSuccess("{\"code\":200,\"result\":[]}", MediaType.APPLICATION_JSON));
        reply("allSearch", "term", 1, groups(1, row("term", "recovered", "r")));
        assertEquals("recovered", service.lookup("term").get("translation"));
        server.verify();
    }

    @Test
    void networkFailuresAreUnavailableNotNotFound() {
        for (String endpoint : Arrays.asList("drawWordSearch", "allSearch", "standardSearch")) {
            server.expect(requestTo(url(endpoint, "term", 1))).andRespond(request -> { throw new IOException("timeout"); });
        }
        Map<String, Object> out = service.lookup("term");
        assertEquals(false, out.get("found"));
        assertEquals(false, out.get("search_complete"));
        assertEquals("unavailable", out.get("lookup_status"));
        server.verify();
    }

    @Test
    void malformedProtocolIsNotMistakenForAnEmptyResult() throws Exception {
        reply("drawWordSearch", "term", 1, null);
        reply("allSearch", "term", 1, Maps.of("renamed_field", Collections.emptyList()));
        reply("standardSearch", "term", 1, Maps.of("renamed_field", Collections.emptyList()));
        assertEquals("unavailable", service.lookup("term").get("lookup_status"));
        server.verify();
    }

    @Test
    void rejectsHtmlAndBusinessErrorsWithoutLosingAlreadyVerifiedEvidence() throws Exception {
        reply("drawWordSearch", "term", 1, row("term", "verified", "v"));
        server.expect(requestTo(url("allSearch", "term", 1)))
                .andRespond(withSuccess("<html>captcha</html>", MediaType.TEXT_HTML));
        Map<String, Object> out = service.lookup("term");
        assertEquals(true, out.get("found"));
        assertEquals("partial", out.get("lookup_status"));
        assertEquals("verified", out.get("translation"));
        server.verify();
    }

    @Test
    void preservesIndividualEvidenceLinksAndDoesNotPairOverviewArrays() throws Exception {
        reply("drawWordSearch", "term", 1, row("term", "one", "first"));
        Map<String, Object> results = groups(2, row("term", "one", "first"), row("term", "two", "second"));
        results.put("overView", Maps.of("en", Arrays.asList("untrusted", "random"), "source", Collections.singletonList("unrelated")));
        reply("allSearch", "term", 1, results);
        Map<String, Object> out = service.lookup("term");
        @SuppressWarnings("unchecked") List<Map<String, Object>> also = (List<Map<String, Object>>) out.get("also_from");
        assertEquals(2, also.size());
        assertNotEquals(also.get(0).get("detail_url"), also.get(1).get("detail_url"));
        assertEquals("two", also.get(1).get("translation"));
        server.verify();
    }

    @Test
    void searchesNextExactPageInsteadOfStoppingAtFirstPage() throws Exception {
        reply("drawWordSearch", "term", 1, null);
        reply("allSearch", "term", 1, groups(51, row("longer term", "unrelated", "first")));
        reply("allSearch", "term", 2, groups(51, row("term", "last page", "last")));
        assertEquals("last page", service.lookup("term").get("translation"));
        server.verify();
    }

    @Test
    void blankInputDoesNotAccessNetwork() {
        assertEquals("invalid", service.lookup("\u200B　").get("lookup_status"));
        server.verify();
    }
    @Test
    void businessErrorIsUnavailableEvenWithHttp200() throws Exception {
        reply("drawWordSearch", "term", 1, null);
        server.expect(requestTo(url("allSearch", "term", 1)))
                .andRespond(withSuccess("{\"code\":500,\"success\":false,\"result\":null}", MediaType.APPLICATION_JSON));
        reply("standardSearch", "term", 1, Maps.of("standardVO", Maps.of("totalRecords", 0, "tmWordList", Collections.emptyList())));
        assertEquals("unavailable", service.lookup("term").get("lookup_status"));
        server.verify();
    }

    @Test
    void truncatedPaginationRemainsIncompleteInsteadOfClaimingNotFound() throws Exception {
        reply("drawWordSearch", "term", 1, null);
        for (int page = 1; page <= 3; page++) {
            reply("allSearch", "term", page, groups(151, row("other", "other", "id" + page)));
        }
        reply("standardSearch", "term", 1, Maps.of("standardVO", Maps.of("totalRecords", 0, "tmWordList", Collections.emptyList())));
        assertEquals("unavailable", service.lookup("term").get("lookup_status"));
        server.verify();
    }

    @Test
    void failedRecommendationDoesNotPreventSuccessfulSearch() throws Exception {
        server.expect(requestTo(url("drawWordSearch", "term", 1))).andRespond(request -> { throw new IOException("timeout"); });
        reply("allSearch", "term", 1, groups(1, row("term", "recovered", "id")));
        Map<String, Object> out = service.lookup("term");
        assertEquals("recovered", out.get("translation"));
        assertEquals(true, out.get("search_complete"));
        server.verify();
    }

    @Test
    void normalizerPreservesEnglishWordBoundaries() {
        assertEquals("carbon neutrality", AuthorityLookupService.normalizeTerm(" Ｃａｒｂｏｎ  neutrality ").toLowerCase());
        assertEquals("碳中和", AuthorityLookupService.normalizeTerm("碳\n中\u00A0和"));
    }

}
