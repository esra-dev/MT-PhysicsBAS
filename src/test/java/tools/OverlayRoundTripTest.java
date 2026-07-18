package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;

import org.junit.jupiter.api.Test;

/**
 * Phase 5 LOADER-side round-trip tests: an overlay synthesized by
 * {@link OverlaySynthesizer} from a gap-KG training run, union-loaded AFTER
 * the gap KG through the production {@link StereotypeReasoner} loading path
 * (the profile {@code ont([...])} list is a plain union — no loader change),
 * must restore exactly the knowledge the gap deleted:
 *
 *   • monitor cell (missing stereotype): the KG-silent monitor action becomes
 *     enriched (kgSilent=false, correct zone), and the completed registry
 *     projection equals the hand-authored parent KG's projection;
 *   • spill cell (missing cross-zone structure): the learned feeds arc +
 *     reified weak connection surface as SECONDARY entries in
 *     {@code getCrossZoneEffects()} — which the action registry is verifiably
 *     blind to — while the registry projection stays unchanged;
 *   • a claim-free overlay (the committed placeholder shape) is inert: the
 *     completed profile is behaviourally identical to the gap profile.
 */
class OverlayRoundTripTest {

    private static final String MONITOR_GAP    = "building_6_monitor_nostereo.ttl";
    private static final String MONITOR_PARENT = "building_6_monitor.ttl";
    private static final String NOSPILL_FIXTURE = "phase5_test_nospill_lab.ttl";

    private static final String MONITOR_ON = "http://example.org/was#SetZ1Monitor";
    private static final String Z1LIGHT    = "http://example.org/was#SetZ1Light";
    private static final String Z2LIGHT    = "http://example.org/was#SetZ2Light";

    // ── helpers ────────────────────────────────────────────────────────────

    private static String resourceText(String name) {
        try (InputStream is = OverlayRoundTripTest.class.getClassLoader().getResourceAsStream(name)) {
            if (is == null) throw new IllegalStateException("resource not found: " + name);
            java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = is.read(buf)) > 0) bos.write(buf, 0, n);
            return new String(bos.toByteArray(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }

    private static StereotypeReasoner reasoner(String... turtleSources) {
        return new StereotypeReasoner(
            new StereotypeReasoner.InMemoryOntologyLoader(turtleSources), 0.75);
    }

    /**
     * Registry projection on the equivalence-instrument columns:
     * key = wotActionType|value → (zones, hasIV, ivIdx, ivMinRank, kgSilent).
     */
    private static Map<String, String> projection(StereotypeReasoner r) {
        Map<String, String> proj = new TreeMap<>();
        for (StereotypeReasoner.ActionInfo ai : r.getAllActions()) {
            if (ai.wotActionType == null) continue; // DO_NOTHING
            proj.put(ai.wotActionType + "|" + ai.wotValue,
                "zones=" + new TreeSet<>(ai.affectedZones)
                + " hasIV=" + ai.hasIV
                + " ivIdx=" + ai.ivStateVecIndex
                + " ivMinRank=" + ai.ivMinRank
                + " kgSilent=" + ai.kgSilent);
        }
        return proj;
    }

    private static StereotypeReasoner.ActionInfo onAction(StereotypeReasoner r, String uri) {
        for (StereotypeReasoner.ActionInfo ai : r.getAllActions()) {
            if (uri.equals(ai.wotActionType) && ai.wotValue) return ai;
        }
        return null;
    }

    private static OverlaySynthesizer.RawStatRow row(String uri, boolean value, int slot,
                                                     long n, double mean, double sd) {
        OverlaySynthesizer.RawStatRow r = new OverlaySynthesizer.RawStatRow();
        r.wotActionUri = uri;
        r.actionValue = value;
        r.actionLabel = OverlaySynthesizer.localName(uri);
        r.svBit = -1;
        r.expectedBit = -1;
        r.slot = slot;
        r.n = n;
        r.mean = mean;
        r.sd = sd;
        return r;
    }

    private static String synthesizeOverlay(String baseTtlText,
                                            OverlaySynthesizer.RawStatRow... rows) {
        OverlaySynthesizer.RawStats st = new OverlaySynthesizer.RawStats();
        for (OverlaySynthesizer.RawStatRow r : rows) st.rows.add(r);
        OverlaySynthesizer.Provenance prov = new OverlaySynthesizer.Provenance();
        prov.sourceRun = "roundtrip_test";
        prov.sourceSeed = "1";
        prov.sourceProfile = "unit_test";
        prov.instrumentCommit = "deadbeef";
        prov.synthesizedAt = "2026-07-13T00:00:00Z";
        OverlaySynthesizer.Result res = OverlaySynthesizer.synthesize(
            st, new StereotypeReasoner.InMemoryOntologyLoader(baseTtlText).load(), prov);
        return res.turtle;
    }

    // ── monitor cell: missing stereotype → enrichment restored ─────────────

    @Test
    void monitorOverlayMakesTheKgSilentActionEnriched() {
        String gap = resourceText(MONITOR_GAP);
        String overlay = synthesizeOverlay(gap,
            row(MONITOR_ON, true,  0, 250,  1.9, 0.4),
            row(MONITOR_ON, false, 0, 250, -1.9, 0.4));

        // Before completion: the monitor is KG-silent (no illuminance claim).
        StereotypeReasoner.ActionInfo before = onAction(reasoner(gap), MONITOR_ON);
        assertNotNull(before);
        assertTrue(before.kgSilent, "gap KG must leave the monitor KG-silent");
        assertTrue(before.affectedZones.isEmpty());

        // After union-loading the overlay: enriched, correct zone, no IV.
        StereotypeReasoner.ActionInfo after = onAction(reasoner(gap, overlay), MONITOR_ON);
        assertNotNull(after);
        assertFalse(after.kgSilent, "overlay must lift KG-silence on the monitor");
        assertEquals(new TreeSet<>(List.of(0)), new TreeSet<>(after.affectedZones),
            "monitor must claim zone 1 (0-based 0) only");
        assertFalse(after.hasIV, "a learned Causes claim must not invent an IV gate");
    }

    @Test
    void completedMonitorRegistryProjectionEqualsTheParentKg() {
        String gap = resourceText(MONITOR_GAP);
        String overlay = synthesizeOverlay(gap,
            row(MONITOR_ON, true,  0, 250,  1.9, 0.4),
            row(MONITOR_ON, false, 0, 250, -1.9, 0.4));

        Map<String, String> completed = projection(reasoner(gap, overlay));
        Map<String, String> parent    = projection(reasoner(resourceText(MONITOR_PARENT)));

        assertEquals(parent, completed,
            "gap+overlay registry projection must equal the hand-authored parent KG");
    }

    // ── spill cell: missing cross-zone structure → SECONDARY arcs restored ──

    @Test
    void spillOverlayRestoresSecondaryCrossZoneEffects() {
        String gap = resourceText(NOSPILL_FIXTURE);

        // The gap KG has no cross-zone knowledge at all.
        assertTrue(reasoner(gap).getCrossZoneEffects().isEmpty(),
            "nospill fixture must start with zero cross-zone effects");

        // Learned: each lamp also moves the NEIGHBOUR zone's level slot
        // (slot 0 = Z1Level, slot 1 = Z2Level), mirrored on OFF. The same-zone
        // effect is also seen but is already asserted (dedup exercises there).
        String overlay = synthesizeOverlay(gap,
            row(Z1LIGHT, true,  0, 300,  2.0, 0.3),   // same-zone → duplicate_asserted
            row(Z1LIGHT, true,  1, 200,  0.4, 0.3),   // cross-zone → XZ claim
            row(Z1LIGHT, false, 1, 200, -0.4, 0.3),
            row(Z2LIGHT, true,  0, 200,  0.4, 0.3),   // cross-zone → XZ claim
            row(Z2LIGHT, false, 0, 200, -0.4, 0.3),
            row(Z2LIGHT, true,  1, 300,  2.0, 0.3));  // same-zone → duplicate_asserted

        StereotypeReasoner completed = reasoner(gap, overlay);
        List<StereotypeReasoner.CrossZoneEffect> effects = completed.getCrossZoneEffects();
        assertEquals(2, effects.size(),
            "overlay must restore exactly the two lamp spill arcs");

        for (StereotypeReasoner.CrossZoneEffect cz : effects) {
            assertEquals(StereotypeReasoner.CrossZoneEffect.CouplingClass.SECONDARY,
                cz.couplingClass,
                "learned spill arcs must be WEAK (SECONDARY) — no rank claim");
        }
        StereotypeReasoner.ActionInfo z1On = onAction(completed, Z1LIGHT);
        StereotypeReasoner.ActionInfo z2On = onAction(completed, Z2LIGHT);
        boolean z1ToZ2 = false, z2ToZ1 = false;
        for (StereotypeReasoner.CrossZoneEffect cz : effects) {
            if (cz.actionIndex == z1On.actionIndex
                    && cz.sourceZoneIdx == 0 && cz.targetZoneIdx == 1) z1ToZ2 = true;
            if (cz.actionIndex == z2On.actionIndex
                    && cz.sourceZoneIdx == 1 && cz.targetZoneIdx == 0) z2ToZ1 = true;
        }
        assertTrue(z1ToZ2, "CeilingLight_Z1 must spill into zone 2");
        assertTrue(z2ToZ1, "CeilingLight_Z2 must spill into zone 1");
    }

    @Test
    void spillOverlayLeavesTheRegistryProjectionUntouched() {
        // Cross-zone lives in crossZoneEffects, NOT in ActionInfo: an XZ-only
        // overlay must not move the registry projection (the reason the spill
        // cell needs its own equivalence instrument).
        String gap = resourceText(NOSPILL_FIXTURE);
        String overlay = synthesizeOverlay(gap,
            row(Z1LIGHT, true,  1, 200,  0.4, 0.3),
            row(Z1LIGHT, false, 1, 200, -0.4, 0.3),
            row(Z2LIGHT, true,  0, 200,  0.4, 0.3),
            row(Z2LIGHT, false, 0, 200, -0.4, 0.3));

        assertEquals(projection(reasoner(gap)), projection(reasoner(gap, overlay)),
            "an XZ-only overlay must leave the action registry projection unchanged");
    }

    // ── placeholder-inertness surrogate ─────────────────────────────────────

    @Test
    void claimFreeOverlayIsBehaviourallyInert() {
        // Stats below every gate → zero claims → the overlay contains only
        // learned:-namespace manifest triples, exactly the committed
        // placeholder shape. Union-loading it must change nothing.
        String gap = resourceText(MONITOR_GAP);
        String emptyOverlay = synthesizeOverlay(gap,
            row(MONITOR_ON, true, 0, 5, 0.01, 5.0));
        assertTrue(emptyOverlay.contains("learned:claimCount       \"0\"^^xsd:int"));

        assertEquals(projection(reasoner(gap)), projection(reasoner(gap, emptyOverlay)),
            "a claim-free overlay must be registry-inert");
        assertTrue(onAction(reasoner(gap, emptyOverlay), MONITOR_ON).kgSilent,
            "the monitor must stay KG-silent under a claim-free overlay");
        assertTrue(reasoner(gap, emptyOverlay).getCrossZoneEffects().isEmpty());
    }
}
