package tools;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Smoke test that proves the JUnit 5 + Gradle test sourceSet wiring works.
 * Real fine-grained unit tests for {@code StereotypeReasoner},
 * {@code QLearner.classifyWeaknesses}, state encoding, and action prediction
 * are added in the follow-up DI refactor (Phase 12 #11) which makes those
 * components injectable / package-visible without changing their public API.
 */
class TestInfrastructureSmokeTest {

    @Test
    void junitPlatformIsWired() {
        assertEquals(4, 2 + 2);
    }

    @Test
    void canLoadBundledOntologyResource() {
        // Confirms Gradle's `src/resources` source set is on the test classpath
        // — a precondition for the upcoming StereotypeReasonerTest fixtures.
        var url = getClass().getClassLoader().getResource("lab-ontology.ttl");
        assertNotNull(url, "lab-ontology.ttl must be reachable from the test classpath");
    }
}
