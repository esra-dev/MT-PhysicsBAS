package tools;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Logger;

import ch.unisg.ics.interactions.wot.td.ThingDescription;
import ch.unisg.ics.interactions.wot.td.affordances.ActionAffordance;
import ch.unisg.ics.interactions.wot.td.affordances.PropertyAffordance;
import ch.unisg.ics.interactions.wot.td.schemas.BooleanSchema;
import ch.unisg.ics.interactions.wot.td.schemas.DataSchema;
import ch.unisg.ics.interactions.wot.td.schemas.ObjectSchema;

/**
 * Validates inputs to {@code LabEnvironment} action / state-setting operations
 * against the bound {@link ThingDescription} (#8).
 *
 * Built once at artifact init from the parsed TD; subsequent calls perform
 * cheap set / map lookups. Failures throw {@link ValidationException}
 * carrying a structured reason code suitable for {@code failed("invalid_input", ...)}.
 */
public class WotInputValidator {

    private static final Logger LOGGER = Logger.getLogger(WotInputValidator.class.getName());

    /** Recognised actuator property names extracted from the Status object schema. */
    private final Set<String> knownPropertyNames;
    /** Recognised WoT action @type URIs (e.g. http://example.org/was#SetZ1Light). */
    private final Set<String> knownActionTypes;
    /** Property names whose Status schema field is a boolean. */
    private final Set<String> booleanPropertyNames;

    public static class ValidationException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        public final String reason;
        public final String actuator;
        public final String expected;
        public final String actual;
        public ValidationException(String reason, String actuator, String expected, String actual) {
            super(reason + ": actuator=" + actuator + " expected=" + expected + " actual=" + actual);
            this.reason   = reason;
            this.actuator = actuator;
            this.expected = expected;
            this.actual   = actual;
        }
    }

    public WotInputValidator(ThingDescription td) {
        Set<String> props        = new HashSet<>();
        Set<String> actionTypes  = new HashSet<>();
        Set<String> booleanProps = new HashSet<>();

        if (td != null) {
            // Status property: enumerate the object-schema field names + types
            for (PropertyAffordance pa : td.getProperties()) {
                DataSchema ds = pa.getDataSchema();
                if (ds instanceof ObjectSchema) {
                    ObjectSchema os = (ObjectSchema) ds;
                    for (var entry : os.getProperties().entrySet()) {
                        String name = entry.getKey();
                        props.add(name);
                        if (entry.getValue() instanceof BooleanSchema) {
                            booleanProps.add(name);
                        }
                    }
                }
            }
            // Action affordances: collect their @type semantic URIs
            for (ActionAffordance aa : td.getActions()) {
                actionTypes.addAll(aa.getSemanticTypes());
            }
        }

        this.knownPropertyNames    = Collections.unmodifiableSet(props);
        this.knownActionTypes      = Collections.unmodifiableSet(actionTypes);
        this.booleanPropertyNames  = Collections.unmodifiableSet(booleanProps);

        LOGGER.info("WotInputValidator built: " + props.size() + " status props ("
                + booleanProps.size() + " boolean), " + actionTypes.size() + " action types");
    }

    /** Validate a WoT action invocation. */
    public void validateAction(String wotSemanticType, Object value) {
        if (wotSemanticType == null || wotSemanticType.isEmpty()) {
            throw new ValidationException("missing_action_type", "(null)", "non-empty URI", "null");
        }
        if (!knownActionTypes.isEmpty() && !knownActionTypes.contains(wotSemanticType)) {
            throw new ValidationException("unknown_action_type",
                    wotSemanticType, "one of " + knownActionTypes.size() + " TD actions", wotSemanticType);
        }
        if (!(value instanceof Boolean)) {
            throw new ValidationException("non_boolean_action_value",
                    wotSemanticType, "Boolean",
                    value == null ? "null" : value.getClass().getSimpleName());
        }
    }

    /** Validate a setLabState key/value map. */
    public void validateStateMap(Object[] keys, Object[] values) {
        if (keys == null || values == null) {
            throw new ValidationException("null_state_map", "(state)",
                    "non-null keys[] and values[]", "null");
        }
        if (keys.length != values.length) {
            throw new ValidationException("length_mismatch", "(state)",
                    "keys.length == values.length",
                    "keys=" + keys.length + " values=" + values.length);
        }
        for (int i = 0; i < keys.length; i++) {
            Object k = keys[i];
            if (k == null) {
                throw new ValidationException("null_key", "(state[" + i + "])", "non-null key", "null");
            }
            String name = String.valueOf(k);
            if (!knownPropertyNames.isEmpty() && !knownPropertyNames.contains(name)) {
                throw new ValidationException("unknown_state_key", name,
                        "one of " + knownPropertyNames.size() + " TD status fields", name);
            }
            Object v = values[i];
            if (v != null && booleanPropertyNames.contains(name) && !(v instanceof Boolean)) {
                throw new ValidationException("non_boolean_state_value", name,
                        "Boolean", v.getClass().getSimpleName());
            }
        }
    }

    // Accessors used by tests.
    Set<String> getKnownPropertyNames()   { return knownPropertyNames; }
    Set<String> getKnownActionTypes()     { return knownActionTypes; }
    Set<String> getBooleanPropertyNames() { return booleanPropertyNames; }
}
