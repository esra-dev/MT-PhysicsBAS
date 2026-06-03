package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
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
        // Audit Step 2 / S2-1: a slot-only fixture (no actuator triples) now
        // triggers the fail-loud guard in StereotypeReasoner.discoverActuators
        // because production code should never run with zero actuators (it
        // collapses the agent to a single DO_NOTHING action). We assert the
        // guard fires AND inspect the slot layout the partially-constructed
        // reasoner exposes via the exception path: the slot registry is
        // queried before discoverActuators, so the layout-side-effects on the
        // reasoner instance are still observable inside the constructor's
        // try-block. We therefore split the test in two: (a) verify the guard,
        // (b) cover the layout via the actuator-bearing fixture below.
        IllegalStateException ex = assertThrows(
            IllegalStateException.class,
            () -> new StereotypeReasoner(
                new StereotypeReasoner.InMemoryOntologyLoader(SLOT_REGISTRY_TTL),
                0.5),
            "S2-1: slot-only fixture must fail-loud, not silently produce a 1-action agent");
        assertTrue(ex.getMessage().contains("0 actuator actions"),
            "Exception message should mention the actuator discovery failure, got: "
                + ex.getMessage());
    }

    /**
     * Augments the slot-only fixture with a minimal actuator chain so the
     * S2-1 guard does not fire, and verifies the slot layout the reasoner
     * exposes once construction completes. This is the layout assertion
     * that {@link #inMemoryLoaderProducesExpectedStateLayout()} previously
     * covered before the fail-loud guard was added.
     */
    @Test
    void inMemoryLoaderWithMinimalActuatorProducesExpectedStateLayout() {
        String fixture = SLOT_REGISTRY_TTL + String.join("\n",
            "@prefix elem:    <http://w3id.org/elementary#> .",
            "@prefix qudtqk:  <http://qudt.org/vocab/quantitykind/> .",
            "@prefix brick:   <https://brickschema.org/schema/Brick#> .",
            "@prefix lab:     <http://example.org/was/lab#> .",
            "",
            "ex:Z1Zone a lab:Workstation ;",
            "    ws:zoneIndex 1 .",
            "",
            "ex:LumOutput a elem:DependentVariable ;",
            "    rdfs:label \"luminescence\" ;",
            "    elem:hasQuantity qudtqk:Illuminance .",
            "",
            "ex:MV a elem:ManipulatedVariable .",
            "",
            "ex:Mech a elem:PhysicalMechanism ;",
            "    elem:hasDependentVariable ex:LumOutput ;",
            "    elem:hasManipulatedVariable ex:MV .",
            "",
            "ex:Stereo a elem:Stereotype ;",
            "    elem:hasPhysicalMechanism ex:Mech .",
            "",
            "ex:ActOn a elem:ComponentAction ;",
            "    ws:actionValue true .",
            "",
            "ex:ActOff a elem:ComponentAction ;",
            "    ws:actionValue false .",
            "",
            "ex:Lamp brick:isLocatedIn ex:Z1Zone ;",
            "    elem:hasBehavioralStereotype ex:Stereo ;",
            "    elem:hasComponentAction ex:ActOn ;",
            "    elem:hasComponentAction ex:ActOff ;",
            "    ws:hasWoTActionSemanticType \"http://example.org/was#SetZ1Light\" .",
            "");
        StereotypeReasoner r = new StereotypeReasoner(
            new StereotypeReasoner.InMemoryOntologyLoader(fixture),
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

        assertTrue(r.getNumActions() >= 2,
            "Fixture with one actuator + DO_NOTHING must produce ≥2 actions, got "
                + r.getNumActions());
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
