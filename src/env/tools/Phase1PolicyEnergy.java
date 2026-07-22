package tools;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Deterministic instantaneous actuator power, sampled once per decision.
 *
 * Default behaviour (no override property) is the frozen Phase-1 v2 rule:
 * substring "spotlight" costs 2, other "light" keys cost 1, everything else
 * (blinds, plugs, monitors) costs 0. The archived Phase-1 corrected results
 * depend on this default staying byte-identical.
 *
 * Phase-4 protocol v2: the run-mode profile may supply an ORDERED token→weight
 * override list via -Pphase1.policyEnergyWeights (forwarded as a system
 * property), e.g. "ineff:4,eff:1,spotlight:2,plug:0,masterswitch:0,light:1,
 * blind:0". For each active actuator the FIRST matching token decides the
 * weight (order matters: "ineff" must precede "eff", "spotlight" must precede
 * "light"); a key matching no token falls through to the Phase-1 default rule.
 * The lab5 weights mirror the run_config phase4.power_formula / the KG's
 * ws:energyCost declarations (Eff=1, Ineff=4, Spotlight=2).
 */
public final class Phase1PolicyEnergy {
    private Phase1PolicyEnergy() { }

    public static final String WEIGHTS_PROPERTY = "phase1.policyEnergyWeights";

    private static volatile List<Map.Entry<String, Double>> cachedOverrides;

    /** Parse an ordered "token:weight,token:weight" spec (empty → no overrides). */
    static List<Map.Entry<String, Double>> parseWeights(String spec) {
        List<Map.Entry<String, Double>> parsed = new ArrayList<>();
        if (spec == null || spec.isBlank()) return parsed;
        for (String part : spec.split(",")) {
            String trimmed = part.trim();
            if (trimmed.isEmpty()) continue;
            int colon = trimmed.indexOf(':');
            if (colon <= 0 || colon == trimmed.length() - 1) {
                throw new IllegalArgumentException(
                        "Invalid policy-energy weight entry: '" + trimmed + "'");
            }
            String token = trimmed.substring(0, colon).trim().toLowerCase(Locale.ROOT);
            double weight = Double.parseDouble(trimmed.substring(colon + 1).trim());
            parsed.add(Map.entry(token, weight));
        }
        return parsed;
    }

    private static List<Map.Entry<String, Double>> activeOverrides() {
        List<Map.Entry<String, Double>> local = cachedOverrides;
        if (local == null) {
            local = parseWeights(System.getProperty(WEIGHTS_PROPERTY, ""));
            cachedOverrides = local;
        }
        return local;
    }

    public static double instantaneousCost(Object[] actuatorKeys, Object[] actuatorValues) {
        return instantaneousCost(actuatorKeys, actuatorValues, activeOverrides());
    }

    /** Package-visible for tests: explicit override list, no property lookup. */
    static double instantaneousCost(Object[] actuatorKeys, Object[] actuatorValues,
                                    List<Map.Entry<String, Double>> overrides) {
        if (actuatorKeys == null || actuatorValues == null
                || actuatorKeys.length != actuatorValues.length) {
            throw new IllegalArgumentException("Actuator keys and values must be parallel arrays");
        }
        double cost = 0.0;
        for (int i = 0; i < actuatorKeys.length; i++) {
            if (!asBoolean(actuatorValues[i])) continue;
            String key = String.valueOf(actuatorKeys[i]).toLowerCase(Locale.ROOT);
            boolean overridden = false;
            for (Map.Entry<String, Double> entry : overrides) {
                if (key.contains(entry.getKey())) {
                    cost += entry.getValue();
                    overridden = true;
                    break;
                }
            }
            if (overridden) continue;
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
