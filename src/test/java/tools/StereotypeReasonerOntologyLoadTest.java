package tools;

import java.util.Arrays;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

/**
 * Loads the production lab-ontology.ttl + wot-mappings.ttl from the classpath
 * via {@link StereotypeReasoner.ClasspathOntologyLoader} (the default DI loader)
 * and asserts the reasoner produces a non-trivial, internally consistent action
 * registry and state-vector layout.
 *
 * Acts as a regression gate: structural changes to the bundled ontology that
 * silently break action discovery, the slot registry, or cross-zone topology
 * fail the build here rather than in a benchmark run.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class StereotypeReasonerOntologyLoadTest {

    private StereotypeReasoner reasoner;

    @BeforeAll
    void setUp() {
        reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "lab-ontology.ttl", "wot-mappings.ttl" }),
            0.5);
    }

    @Test
    void discoversActions() {
        assertTrue(reasoner.getNumActions() > 0,
            "Expected the reasoner to discover at least one action from the bundled ontology");
    }

    @Test
    void buildsStateSlotRegistry() {
        int[] domains = reasoner.getStateDomainSizes();
        assertNotNull(domains, "domainSizes[] must be populated");
        assertTrue(domains.length > 0, "domainSizes[] must be non-empty");
        for (int i = 0; i < domains.length; i++) {
            assertTrue(domains[i] > 0,
                "domainSizes[" + i + "] must be > 0, got " + domains[i] + " (full: " + Arrays.toString(domains) + ")");
        }
        assertTrue(reasoner.getStateVecLength() == domains.length,
            "getStateVecLength() must equal domainSizes.length");
    }

    @Test
    void buildsZoneLevelIndices() {
        int[] zones = reasoner.getZoneLevelIndices();
        assertNotNull(zones, "zoneLevelIndices[] must be populated");
        assertTrue(zones.length >= 2,
            "Expected at least 2 zone-level slots in the bundled ontology, got " + zones.length);
    }

    @Test
    void buildsWotStateToSvIndexMap() {
        var map = reasoner.getWotStateToSvIndexMap();
        assertNotNull(map);
        assertFalse(map.isEmpty(),
            "wotStateToSvIndex must be populated from ws:stateVecIndex triples");
        // Every mapped index must be a valid slot in domainSizes[].
        int n = reasoner.getStateDomainSizes().length;
        map.forEach((stateType, idx) -> {
            assertTrue(idx >= 0 && idx < n,
                "wotStateToSvIndex[" + stateType + "] = " + idx + " is out of range [0, " + n + ")");
        });
    }
}
