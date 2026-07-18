package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.apache.jena.ontology.OntModel;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Phase 5 unit tests for the learned-KG-completion WRITER
 * ({@link OverlaySynthesizer}) and the flip-conditioned admission /
 * saveRawStats instrument in {@link StereotypeLearner}.
 *
 * Covers, on synthetic stats against the committed monitor gap/parent KGs:
 *   • emission — a gated same-zone effect on the KG-silent monitor becomes an
 *     EMITTED SZ claim whose Turtle parses and carries the enrichment surface;
 *   • dedup — the SAME stats against the PARENT KG are fully suppressed as
 *     duplicate_asserted (why arm C's overlay is the expected-empty
 *     specificity control), and a negative learned sign on an asserted
 *     surface is flagged sign_conflict_asserted;
 *   • gates — insufficient_samples / z_below_cutoff / effect_below_min;
 *   • sign-mirror — a significant same-signed OFF estimate suppresses the
 *     claim;
 *   • flip arithmetic — flip-conditioned admission counts only samples whose
 *     commanded bit actually flipped, and saveRawStats round-trips through
 *     RawStats.parse;
 *   • determinism — identical inputs yield byte-identical overlay text.
 */
class OverlaySynthesizerTest {

    private static final String MONITOR_ON  = "http://example.org/was#SetZ1Monitor";
    private static final String LIGHT_URI   = "http://example.org/was#SetZ1Light";

    @AfterEach
    void clearSysProps() {
        System.clearProperty("stereotype.learner.flipConditioned");
    }

    // ── helpers ────────────────────────────────────────────────────────────

    private static OntModel model(String... classpathTtls) {
        return new StereotypeReasoner.ClasspathOntologyLoader(classpathTtls).load();
    }

    private static OverlaySynthesizer.RawStatRow row(String uri, boolean value, int slot,
                                                     long n, double mean, double sd) {
        OverlaySynthesizer.RawStatRow r = new OverlaySynthesizer.RawStatRow();
        r.wotActionUri = uri;
        r.actionValue = value;
        r.actionLabel = OverlaySynthesizer.localName(uri) + "=" + (value ? "ON" : "OFF");
        r.svBit = -1;
        r.expectedBit = -1;
        r.slot = slot;
        r.n = n;
        r.mean = mean;
        r.sd = sd;
        return r;
    }

    private static OverlaySynthesizer.RawStats stats(OverlaySynthesizer.RawStatRow... rows) {
        OverlaySynthesizer.RawStats st = new OverlaySynthesizer.RawStats();
        for (OverlaySynthesizer.RawStatRow r : rows) st.rows.add(r);
        return st;
    }

    private static OverlaySynthesizer.Provenance prov() {
        OverlaySynthesizer.Provenance p = new OverlaySynthesizer.Provenance();
        p.sourceRun = "test_run_1";
        p.sourceSeed = "7";
        p.sourceProfile = "labmon_nostereo";
        p.instrumentCommit = "deadbeef";
        p.synthesizedAt = "2026-07-13T00:00:00Z"; // pinned → deterministic output
        return p;
    }

    private static OverlaySynthesizer.Claim findClaim(
            List<OverlaySynthesizer.Claim> claims, String actionUri, int slot) {
        for (OverlaySynthesizer.Claim c : claims) {
            if (c.actionUri.equals(actionUri) && c.slot == slot) return c;
        }
        return null;
    }

    // ── emission ───────────────────────────────────────────────────────────

    @Test
    void gapKgMonitorEffectIsEmittedAsSameZoneClaim() {
        // Monitor gap KG: slot 0 = Z1Level. A strong, mirrored ON/OFF effect
        // on the undocumented monitor must survive every gate.
        OverlaySynthesizer.RawStats st = stats(
            row(MONITOR_ON, true,  0, 250,  1.9, 0.4),
            row(MONITOR_ON, false, 0, 250, -1.9, 0.4));
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());

        assertEquals(1, res.emittedCount, "exactly one claim must be emitted");
        OverlaySynthesizer.Claim c = findClaim(res.claims, MONITOR_ON, 0);
        assertNotNull(c);
        assertEquals("EMITTED", c.status);
        assertEquals("SZ", c.kind);
        assertEquals(1, c.targetZoneIdx1);
        assertEquals(1, c.sign);
        assertTrue(c.componentUri.endsWith("Monitor_Z1"));

        // The overlay must parse as Turtle and carry the enrichment surface
        // (stereotype link + Illuminance DV) plus the same-zone feeds arc.
        OntModel parsed = new StereotypeReasoner.InMemoryOntologyLoader(res.turtle).load();
        assertTrue(parsed.size() > 0, "overlay must be non-empty parseable Turtle");
        assertTrue(res.turtle.contains("elem:hasBehavioralStereotype learned:st_Monitor_Z1_z1"));
        assertTrue(res.turtle.contains("qudtqk:Illuminance"));
        assertTrue(res.turtle.contains("brick:feeds"));
        assertTrue(res.turtle.contains("learned:claimCount       \"1\"^^xsd:int"));
        // Provenance props (frozen contract).
        assertTrue(res.turtle.contains("learned:sourceRun"));
        assertTrue(res.turtle.contains("learned:sourceSeed"));
        assertTrue(res.turtle.contains("learned:sourceProfile"));
        assertTrue(res.turtle.contains("learned:instrumentCommit"));
        assertTrue(res.turtle.contains("learned:sampleCount"));
        assertTrue(res.turtle.contains("learned:meanDelta"));
        assertTrue(res.turtle.contains("learned:zScore"));
        assertTrue(res.turtle.contains("learned:synthesizedAt"));
    }

    // ── dedup / specificity control ────────────────────────────────────────

    @Test
    void parentKgSuppressesEverythingAsDuplicateAsserted() {
        // Same effects, but against the PARENT KG where lamp AND monitor are
        // fully documented → the overlay must be empty (specificity control).
        OverlaySynthesizer.RawStats st = stats(
            row(MONITOR_ON, true, 0, 250, 1.9, 0.4),
            row(LIGHT_URI,  true, 0, 300, 2.5, 0.3));
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor.ttl"), prov());

        assertEquals(0, res.emittedCount, "parent-KG overlay must be empty");
        assertEquals("duplicate_asserted", findClaim(res.claims, MONITOR_ON, 0).reason);
        assertEquals("duplicate_asserted", findClaim(res.claims, LIGHT_URI, 0).reason);
        assertTrue(res.turtle.contains("learned:claimCount       \"0\"^^xsd:int"));
        // Even the empty overlay must be parseable (placeholder shape).
        assertTrue(new StereotypeReasoner.InMemoryOntologyLoader(res.turtle).load().size() > 0);
    }

    @Test
    void negativeSignOnAssertedSurfaceIsFlaggedAsConflict() {
        // The parent KG asserts the lamp increases Z1 illuminance; a learned
        // NEGATIVE estimate on the same surface is a sign conflict, not a dup.
        OverlaySynthesizer.RawStats st = stats(
            row(LIGHT_URI, true, 0, 300, -2.5, 0.3));
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor.ttl"), prov());

        assertEquals(0, res.emittedCount);
        assertEquals("sign_conflict_asserted", findClaim(res.claims, LIGHT_URI, 0).reason);
    }

    // ── emission gates ─────────────────────────────────────────────────────

    @Test
    void gatesSuppressWeakEffectsWithTheRegisteredReasons() {
        OverlaySynthesizer.RawStats st = stats(
            row(MONITOR_ON, true, 0, 10, 1.9, 0.4));     // n < 30
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals("insufficient_samples", findClaim(res.claims, MONITOR_ON, 0).reason);

        st = stats(row(MONITOR_ON, true, 0, 100, 0.5, 10.0)); // z = 0.5 < 3
        res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals("z_below_cutoff", findClaim(res.claims, MONITOR_ON, 0).reason);

        st = stats(row(MONITOR_ON, true, 0, 100, 0.01, 0.001)); // z huge, |μ| < 0.05
        res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals("effect_below_min", findClaim(res.claims, MONITOR_ON, 0).reason);
    }

    @Test
    void significantSameSignedOffEstimateViolatesSignMirror() {
        // ON and OFF both significantly POSITIVE on the same slot → the effect
        // does not track the commanded state → suppressed.
        OverlaySynthesizer.RawStats st = stats(
            row(MONITOR_ON, true,  0, 100, 1.5, 0.2),
            row(MONITOR_ON, false, 0, 100, 1.5, 0.2));
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals(0, res.emittedCount);
        assertEquals("sign_mirror_violation", findClaim(res.claims, MONITOR_ON, 0).reason);

        // An INSIGNIFICANT same-signed OFF estimate cannot disconfirm.
        st = stats(
            row(MONITOR_ON, true,  0, 100, 1.5, 0.2),
            row(MONITOR_ON, false, 0,   5, 1.5, 0.2));
        res = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals(1, res.emittedCount);
    }

    // ── flip-conditioned admission + raw-stats round trip ──────────────────

    @Test
    void flipConditionedAdmissionCountsOnlyRealFlips() throws Exception {
        System.setProperty("stereotype.learner.flipConditioned", "true");
        StereotypeLearner learner = new StereotypeLearner();
        // Action 0 commands bit 1 (expected ON=1); action 1 has no bit.
        learner.initLearner(2, 2,
            new Object[]{MONITOR_ON, ""},
            new Object[]{true, false},
            new Object[]{"SetZ1Monitor=ON", "DO_NOTHING"},
            new Object[]{1, -1},
            new Object[]{1, -1});

        // Bit flips 0→1 as commanded → admitted (slot-0 Δ = +2 counted).
        learner.observe(new Object[]{0, 0}, 0, new Object[]{2, 1});
        // Bit already ON (no flip) → rejected (slot-0 Δ = +2 NOT counted).
        learner.observe(new Object[]{0, 1}, 0, new Object[]{2, 1});
        // Action without a commanded bit → always admitted.
        learner.observe(new Object[]{0, 0}, 1, new Object[]{1, 0});

        Path tmp = Files.createTempFile("raw_stats", ".csv");
        try {
            learner.saveRawStats(tmp.toString());
            OverlaySynthesizer.RawStats st;
            try (StringReader r = new StringReader(new String(Files.readAllBytes(tmp)))) {
                st = OverlaySynthesizer.RawStats.parse(r);
            }
            assertTrue(st.flipConditioned);
            assertEquals(2, st.admittedSamples);
            assertEquals(1, st.rejectedNoFlip);
            assertEquals(2 * 2, st.rows.size(), "one row per (action, slot) cell");

            OverlaySynthesizer.RawStatRow a0s0 = st.rows.get(0);
            assertEquals(0, a0s0.actionIdx);
            assertEquals(0, a0s0.slot);
            assertEquals(1, a0s0.n, "only the flipped sample is admitted");
            assertEquals(2.0, a0s0.mean, 1e-9, "mean Δ from the admitted sample only");
            assertEquals(1, a0s0.svBit);
            assertEquals(1, a0s0.expectedBit);
        } finally {
            Files.deleteIfExists(tmp);
        }
    }

    @Test
    void legacyInitAdmitsEverySampleEvenWhenGateEnabled() {
        // The gate needs svBit metadata: with the legacy 5-arg init it is
        // inert, preserving pre-Phase-5 behaviour bit for bit.
        System.setProperty("stereotype.learner.flipConditioned", "true");
        StereotypeLearner learner = new StereotypeLearner();
        learner.initLearner(1, 2,
            new Object[]{MONITOR_ON}, new Object[]{true}, new Object[]{"SetZ1Monitor=ON"});
        learner.observe(new Object[]{0, 1}, 0, new Object[]{2, 1}); // no flip anywhere

        Path tmp;
        try {
            tmp = Files.createTempFile("raw_stats_legacy", ".csv");
            learner.saveRawStats(tmp.toString());
            OverlaySynthesizer.RawStats st;
            try (StringReader r = new StringReader(new String(Files.readAllBytes(tmp)))) {
                st = OverlaySynthesizer.RawStats.parse(r);
            }
            Files.deleteIfExists(tmp);
            assertEquals(1, st.rows.get(0).n, "legacy init must admit the sample");
            assertEquals(-1, st.rows.get(0).svBit);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    // ── determinism ────────────────────────────────────────────────────────

    @Test
    void identicalInputsYieldByteIdenticalOverlays(@TempDir Path dir) {
        OverlaySynthesizer.RawStats st = stats(
            row(MONITOR_ON, true,  0, 250,  1.9, 0.4),
            row(MONITOR_ON, false, 0, 250, -1.9, 0.4),
            row(LIGHT_URI,  true,  0, 300,  2.5, 0.3));
        OverlaySynthesizer.Result a = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        OverlaySynthesizer.Result b = OverlaySynthesizer.synthesize(
            st, model("building_6_monitor_nostereo.ttl"), prov());
        assertEquals(a.turtle, b.turtle, "synthesis must be deterministic");
        assertFalse(a.turtle.isEmpty());
    }
}
