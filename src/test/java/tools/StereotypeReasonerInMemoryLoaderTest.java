package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

/**
 * Pins down the {@link StereotypeReasoner.InMemoryOntologyLoader} DI hook
 * (#11 refactor). Verifies that a synthetic Turtle fixture containing only
 * the slot registry produces a usable reasoner without touching the
 * classpath, which is the foundation for further fine-grained unit tests.
 */
class StereotypeReasonerInMemoryLoaderTest {

    /**
     * Minimal slot-registry fixture: two zone-level slots + one sunshine slot.
     * No actuators, no actions — just the state-vector layout.
     */
    private static final String SLOT_REGISTRY_TTL = String.join("\n",
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix ws:   <http://example.org/was/lab/stereotypes#> .",
        "@prefix lab:  <http://example.org/was/lab#> .",
        "@prefix ex:   <http://example.org/fixture#> .",
        "",
        "ex:Z1LevelSlot",
        "    ws:stateVecIndex   0 ;",
        "    ws:stateDomainSize 4 ;",
        "    ws:stateSlotRole   \"zone_level\" ;",
        "    ws:zoneIndex       1 .",
        "",
        "ex:Z2LevelSlot",
        "    ws:stateVecIndex   1 ;",
        "    ws:stateDomainSize 4 ;",
        "    ws:stateSlotRole   \"zone_level\" ;",
        "    ws:zoneIndex       2 .",
        "",
        "ex:SunshineSlot",
        "    ws:stateVecIndex   2 ;",
        "    ws:stateDomainSize 4 ;",
        "    ws:stateSlotRole   \"sunshine\" .",
        "");

    @Test
    void inMemoryLoaderProducesExpectedStateLayout() {
        StereotypeReasoner r = new StereotypeReasoner(
            new StereotypeReasoner.InMemoryOntologyLoader(SLOT_REGISTRY_TTL),
            0.5);

        int[] domains = r.getStateDomainSizes();
        assertNotNull(domains, "domainSizes[] must be populated from in-memory fixture");
        assertTrue(domains.length >= 3,
            "Expected at least 3 slots (Z1Level, Z2Level, Sunshine), got " + domains.length);

        assertEquals(4, domains[0], "Z1 level slot domain size");
        assertEquals(4, domains[1], "Z2 level slot domain size");
        assertEquals(4, domains[2], "Sunshine slot domain size");

        int[] zones = r.getZoneLevelIndices();
        assertEquals(2, zones.length, "Expected exactly 2 zone-level slots");

        assertEquals(2, r.getSunshineIndex(), "Sunshine slot must be at index 2");

        // No actuators in the fixture — only the implicit DO_NOTHING action.
        assertEquals(1, r.getNumActions(),
            "Slot-only fixture must produce exactly the implicit DO_NOTHING action");
    }

    @Test
    void inMemoryLoaderAndClasspathLoaderShareInterface() {
        // Smoke test confirming the DI contract: both implementations satisfy
        // OntologyLoader and can be passed to the same constructor.
        StereotypeReasoner.OntologyLoader inMem =
            new StereotypeReasoner.InMemoryOntologyLoader(SLOT_REGISTRY_TTL);
        StereotypeReasoner.OntologyLoader cp =
            new StereotypeReasoner.ClasspathOntologyLoader(new String[] {});
        assertNotNull(inMem);
        assertNotNull(cp);
    }
}
