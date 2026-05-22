package tools;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import ch.unisg.ics.interactions.wot.td.ThingDescription;
import ch.unisg.ics.interactions.wot.td.ThingDescription.TDFormat;
import ch.unisg.ics.interactions.wot.td.io.TDGraphReader;

/**
 * Tests for {@link WotInputValidator}. Loads the real interactions-lab-custom2 TD
 * from the classpath so the validator exercises a representative action / status
 * surface (multiple zones, mixed boolean + numeric status fields).
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class WotInputValidatorTest {

    private WotInputValidator validator;
    private String anyKnownAction;
    private String anyKnownBooleanProp;
    private String anyKnownNumericProp;

    @BeforeAll
    void loadTd() throws Exception {
        try (InputStream is = getClass().getClassLoader()
                .getResourceAsStream("interactions-lab-custom2.ttl")) {
            assertNotNull(is, "interactions-lab-custom2.ttl must be on the classpath");
            String content = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            if (!content.isEmpty() && content.charAt(0) == '\uFEFF') content = content.substring(1);
            ThingDescription td = TDGraphReader.readFromString(TDFormat.RDF_TURTLE, content);
            validator = new WotInputValidator(td);
        }
        assertFalse(validator.getKnownActionTypes().isEmpty(), "TD should expose actions");
        assertFalse(validator.getKnownPropertyNames().isEmpty(), "TD should expose status props");
        anyKnownAction      = validator.getKnownActionTypes().iterator().next();
        anyKnownBooleanProp = validator.getBooleanPropertyNames().stream().findFirst().orElse(null);
        anyKnownNumericProp = validator.getKnownPropertyNames().stream()
                .filter(n -> !validator.getBooleanPropertyNames().contains(n))
                .findFirst().orElse(null);
    }

    @Test
    void validateActionAcceptsKnownTypeWithBoolean() {
        assertDoesNotThrow(() -> validator.validateAction(anyKnownAction, Boolean.TRUE));
    }

    @Test
    void validateActionRejectsUnknownType() {
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateAction("http://example.org/was#TotallyMadeUp", true));
        assertEquals("unknown_action_type", ex.reason);
    }

    @Test
    void validateActionRejectsNullType() {
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateAction(null, true));
        assertEquals("missing_action_type", ex.reason);
    }

    @Test
    void validateActionRejectsNonBooleanPayload() {
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateAction(anyKnownAction, "yes"));
        assertEquals("non_boolean_action_value", ex.reason);
    }

    @Test
    void validateStateMapAcceptsKnownKeys() {
        if (anyKnownBooleanProp != null) {
            assertDoesNotThrow(() -> validator.validateStateMap(
                    new Object[]{anyKnownBooleanProp},
                    new Object[]{Boolean.FALSE}));
        }
        if (anyKnownNumericProp != null) {
            assertDoesNotThrow(() -> validator.validateStateMap(
                    new Object[]{anyKnownNumericProp},
                    new Object[]{Double.valueOf(100.0)}));
        }
    }

    @Test
    void validateStateMapRejectsUnknownKey() {
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateStateMap(
                        new Object[]{"Frobnicate"}, new Object[]{Boolean.TRUE}));
        assertEquals("unknown_state_key", ex.reason);
    }

    @Test
    void validateStateMapRejectsLengthMismatch() {
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateStateMap(
                        new Object[]{"a", "b"}, new Object[]{Boolean.TRUE}));
        assertEquals("length_mismatch", ex.reason);
    }

    @Test
    void validateStateMapRejectsNonBooleanForBooleanField() {
        if (anyKnownBooleanProp == null) return; // skip if TD has no boolean fields
        WotInputValidator.ValidationException ex = assertThrows(
                WotInputValidator.ValidationException.class,
                () -> validator.validateStateMap(
                        new Object[]{anyKnownBooleanProp},
                        new Object[]{Integer.valueOf(1)}));
        assertEquals("non_boolean_state_value", ex.reason);
    }
}
