package com.swpu.transflow.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.swpu.transflow.util.Maps;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

class TermPrepServiceTest {
    private final ObjectMapper mapper = new ObjectMapper();

    private Map<String, Object> analyze(Object terms, Map<String, Object> online) {
        JsonDataService data = mock(JsonDataService.class);
        when(data.read("termbase/terms.json")).thenReturn(mapper.valueToTree(Maps.of("terms", terms)));
        AuthorityLookupService authority = mock(AuthorityLookupService.class);
        when(authority.lookup(anyString())).thenReturn(online);
        return new TermPrepService(data, authority).analyze("term", "context");
    }

    private Map<String, Object> evidence(String translation, String tier, String source) {
        return Maps.of("text", translation, "tier", tier, "source_id", source, "source_name", source,
                "url", "https://example.gov.cn/" + source, "snippet", "original quote");
    }

    private Map<String, Object> miss(boolean complete) {
        return Maps.of("found", false, "search_complete", complete, "reason", "本次在线补查未取得条目");
    }

    @Test
    void localTierOneEvidenceIsNotShownAsNoAuthorityFound() {
        Map<String, Object> result = analyze(Collections.singletonList(Maps.of("term", "term", "translations",
                Collections.singletonList(evidence("official", "tier1", "T1-01")))), miss(false));
        assertEquals("locked", result.get("status"));
        @SuppressWarnings("unchecked") Map<String, Object> auth = (Map<String, Object>) result.get("authority");
        assertEquals(true, auth.get("found"));
        assertEquals("local_evidence", auth.get("lookup_status"));
        assertEquals("T1-01", auth.get("source_name"));
    }

    @Test
    void cannotDowngradeToTierTwoOnNetworkFailure() {
        List<Map<String, Object>> rows = Arrays.asList(evidence("agreed", "tier2", "T2-01"), evidence("agreed", "tier2", "T2-02"));
        Object terms = Collections.singletonList(Maps.of("term", "term", "translations", rows));
        Map<String, Object> result = analyze(terms, miss(false));
        assertEquals("pending", result.get("status"));
        assertNull(result.get("translation"));
        assertEquals("confirmed", analyze(terms, miss(true)).get("status"));
    }

    @Test
    void competingOnlineTranslationsAreNotSilentlyLocked() {
        Map<String, Object> a = Maps.of("term", "term", "translation", "one", "detail_url", "https://www.termonline.cn/wordDetail?id=1", "termbase", "库一");
        Map<String, Object> b = Maps.of("term", "term", "translation", "two", "detail_url", "https://www.termonline.cn/wordDetail?id=2", "termbase", "库二");
        Map<String, Object> online = Maps.of("found", true, "search_complete", true, "translation", "one",
                "source_id", "T1-06", "source_name", "术语在线", "also_from", Arrays.asList(a, b));
        Map<String, Object> result = analyze(Collections.emptyList(), online);
        assertEquals("conflict", result.get("status"));
        assertNull(result.get("translation"));
        @SuppressWarnings("unchecked") List<Map<String, Object>> rows = (List<Map<String, Object>>) result.get("evidence");
        assertNotEquals(rows.get(0).get("url"), rows.get(1).get("url"));
    }

    @Test
    void noLocalHitStillRequiresOtherTierOneSourcesToBeChecked() {
        Map<String, Object> result = analyze(Collections.emptyList(), miss(true));
        assertEquals("pending", result.get("status"));
        assertTrue(result.get("message").toString().contains("继续核验其他一级源"));
        assertFalse(result.get("message").toString().contains("一级源未收录"));
    }
}
