package tools;

import java.util.Locale;

/** Deterministic Phase-1 instantaneous actuator power, sampled once per decision. */
public final class Phase1PolicyEnergy {
    private Phase1PolicyEnergy() { }

    public static double instantaneousCost(Object[] actuatorKeys, Object[] actuatorValues) {
        if (actuatorKeys == null || actuatorValues == null
                || actuatorKeys.length != actuatorValues.length) {
            throw new IllegalArgumentException("Actuator keys and values must be parallel arrays");
        }
        double cost = 0.0;
        for (int i = 0; i < actuatorKeys.length; i++) {
            if (!asBoolean(actuatorValues[i])) continue;
            String key = String.valueOf(actuatorKeys[i]).toLowerCase(Locale.ROOT);
            if (key.contains("spotlight")) {
                cost += 2.0;
            } else if (key.contains("light") && !key.contains("level")) {
                cost += 1.0;
            }
            // Motorised blinds are passive in the Phase-1 simulator model.
        }
        return cost;
    }

    private static boolean asBoolean(Object value) {
        if (value instanceof Boolean) return (Boolean) value;
        return Boolean.parseBoolean(String.valueOf(value));
    }
}
