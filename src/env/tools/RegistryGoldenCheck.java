package tools;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

/**
 * Golden test for the ontology-discovered action registries.
 *
 * For every ontology set in {@link ActionRegistryDump#ONTOLOGY_SETS} the LIVE
 * registry (computed by the current StereotypeReasoner code) is compared to
 * the golden CSV in the given directory (default {@code config/golden_registry}).
 *
 * CONTRACT (must match, else exit 1):
 *   - identical action-key sets (wotActionType|ON/OFF + DO_NOTHING),
 *   - identical per-key metadata: label, wotStateType, state-vector bit,
 *     expected bit, affected zones, IV binding (hasIV/ivIdx/ivMinRank),
 *     energyCost, kgSilent.
 *
 * EXPLICITLY NOT part of the contract: the numeric action INDEX. Persisted
 * per-action artifacts (Q-tables, visit/trust/IV sidecars) are label-remapped
 * on load, so an index permutation is behaviour-preserving for warm loads.
 * Permutations are still REPORTED so ordering changes are visible in CI logs
 * and can be cited in the audit trail.
 *
 * Run:  gradlew verifyActionRegistry
 *       gradlew verifyActionRegistry -PregistryGolden=config/golden_registry/pre_inversion
 */
public final class RegistryGoldenCheck {

    public static void main(String[] args) throws IOException {
        Path goldenDir = Paths.get(args.length > 0 ? args[0] : "config/golden_registry");
        boolean allOk = true;
        int checked = 0, permuted = 0;

        for (Map.Entry<String, String[]> e : ActionRegistryDump.ONTOLOGY_SETS.entrySet()) {
            String name = e.getKey();
            Path golden = goldenDir.resolve("registry_" + name + ".csv");
            if (!Files.exists(golden)) {
                System.out.println("[FAIL] " + name + ": golden file missing: " + golden);
                allOk = false;
                continue;
            }
            Map<String, String> goldenMeta = new LinkedHashMap<>();
            Map<String, Integer> goldenIdx = new LinkedHashMap<>();
            parse(Files.readAllLines(golden, StandardCharsets.UTF_8), goldenMeta, goldenIdx);

            Map<String, String> liveMeta = new LinkedHashMap<>();
            Map<String, Integer> liveIdx = new LinkedHashMap<>();
            parse(ActionRegistryDump.liveRows(e.getValue()), liveMeta, liveIdx);

            boolean ok = true;
            for (String k : new TreeSet<>(goldenMeta.keySet())) {
                if (!liveMeta.containsKey(k)) {
                    System.out.println("[FAIL] " + name + ": action MISSING from live registry: " + k);
                    ok = false;
                }
            }
            for (String k : new TreeSet<>(liveMeta.keySet())) {
                if (!goldenMeta.containsKey(k)) {
                    System.out.println("[FAIL] " + name + ": EXTRA action in live registry: " + k);
                    ok = false;
                }
            }
            for (String k : new TreeSet<>(goldenMeta.keySet())) {
                String g = goldenMeta.get(k), l = liveMeta.get(k);
                if (l != null && !g.equals(l)) {
                    System.out.println("[FAIL] " + name + ": metadata mismatch for " + k);
                    System.out.println("         golden: " + g);
                    System.out.println("         live  : " + l);
                    ok = false;
                }
            }
            List<String> perm = new ArrayList<>();
            for (String k : new TreeSet<>(goldenIdx.keySet())) {
                Integer gi = goldenIdx.get(k), li = liveIdx.get(k);
                if (li != null && !gi.equals(li)) perm.add(k + " " + gi + "->" + li);
            }
            if (ok) {
                if (perm.isEmpty()) {
                    System.out.println("[OK]   " + name + ": " + liveMeta.size()
                        + " actions, metadata identical, indices identical");
                } else {
                    permuted++;
                    System.out.println("[OK]   " + name + ": " + liveMeta.size()
                        + " actions, metadata identical; INDEX PERMUTATION (informational, "
                        + perm.size() + " moved):");
                    for (String p : perm) System.out.println("         " + p);
                }
            }
            allOk &= ok;
            checked++;
        }

        System.out.println();
        System.out.println("RegistryGoldenCheck: " + checked + " ontology set(s) checked against "
            + goldenDir + " — " + (allOk ? "CONTRACT HOLDS" : "CONTRACT VIOLATED")
            + (permuted > 0 ? " (" + permuted + " set(s) index-permuted; label-remap makes this safe)" : ""));
        if (!allOk) System.exit(1);
    }

    /** Parses canonical rows into metadata (all columns except actionIndex) and index maps. */
    private static void parse(List<String> lines, Map<String, String> meta, Map<String, Integer> idx) {
        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#") || line.startsWith("key,")) continue;
            int lastComma = line.lastIndexOf(',');
            String metaPart = line.substring(0, lastComma);
            int actionIndex = Integer.parseInt(line.substring(lastComma + 1).trim());
            String key = metaPart.substring(0, metaPart.indexOf(','));
            meta.put(key, metaPart);
            idx.put(key, actionIndex);
        }
    }

    private RegistryGoldenCheck() { }
}
