package tools;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Dumps the ontology-discovered action registry of every registered lab
 * ontology set to a canonical, diff-friendly CSV (one file per set under the
 * given output directory; default {@code config/golden_registry}).
 *
 * Purpose (action-space inversion audit): the CSVs are the GOLDEN contract for
 * {@link RegistryGoldenCheck}. The contract is LABEL-KEYED — one row per
 * action key ({@code wotActionType|ON/OFF}, or {@code DO_NOTHING}) with its
 * full metadata (zones, IV binding, energy cost, KG-silent flag, state-vector
 * bit). Rows are sorted by key, so the files are INDEPENDENT of the discovery
 * ordering; the numeric {@code actionIndex} column is recorded for
 * informational permutation reports only and is NOT part of the contract
 * (all persisted per-action artifacts are label-remapped on load).
 *
 * Run:  gradlew dumpActionRegistry            (writes config/golden_registry)
 *       gradlew dumpActionRegistry -PregistryOut=some/dir
 */
public final class ActionRegistryDump {

    /** Every distinct ont([...]) set registered in lab_profiles.asl, keyed by
     *  a representative profile name. Faulty/adapt profiles reuse these exact
     *  sets, so this list covers the full discovery surface of the project. */
    static final Map<String, String[]> ONTOLOGY_SETS = new LinkedHashMap<>();
    static {
        ONTOLOGY_SETS.put("custom",   new String[]{"lab-ontology.ttl", "wot-mappings.ttl"});
        ONTOLOGY_SETS.put("custom2",  new String[]{"lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"});
        ONTOLOGY_SETS.put("lab1",     new String[]{"building_1_trivial.ttl"});
        ONTOLOGY_SETS.put("lab2",     new String[]{"building_2_intermediate.ttl"});
        ONTOLOGY_SETS.put("lab3",     new String[]{"building_3_complex.ttl"});
        ONTOLOGY_SETS.put("lab2_slow", new String[]{"building_2_slow.ttl"});
        ONTOLOGY_SETS.put("lab3_slow", new String[]{"building_3_slow.ttl"});
        ONTOLOGY_SETS.put("lab4",     new String[]{"building_4_smartplug.ttl"});
        ONTOLOGY_SETS.put("lab5",     new String[]{"building_5_energy.ttl"});
        // Phase-4 dependency-ladder extension (2026-07-12): parallel and
        // chained power-gate variants of lab4.
        ONTOLOGY_SETS.put("lab4dual",  new String[]{"building_8_dualplug.ttl"});
        ONTOLOGY_SETS.put("lab4chain", new String[]{"building_9_chainplug.ttl"});
        ONTOLOGY_SETS.put("labmon",            new String[]{"building_6_monitor.ttl"});
        ONTOLOGY_SETS.put("labmon_infoonly",   new String[]{"building_6_monitor_infoonly.ttl"});
        ONTOLOGY_SETS.put("labmon_nostereo",   new String[]{"building_6_monitor_nostereo.ttl"});
        ONTOLOGY_SETS.put("labmon2",           new String[]{"building_7_dualmonitor.ttl"});
        ONTOLOGY_SETS.put("labmon2_infoonly",  new String[]{"building_7_dualmonitor_infoonly.ttl"});
        ONTOLOGY_SETS.put("labmon2_nostereo",  new String[]{"building_7_dualmonitor_nostereo.ttl"});
        // Phase 1B (branch phase1b-labs-2026-07): relevance ladder,
        // statefulness comparison, exact-band control, depth-3 chain.
        ONTOLOGY_SETS.put("labrel0",    new String[]{"building_10_labrel0.ttl"});
        ONTOLOGY_SETS.put("labrel4",    new String[]{"building_10_labrel4.ttl"});
        ONTOLOGY_SETS.put("labrel8",    new String[]{"building_10_labrel8.ttl"});
        ONTOLOGY_SETS.put("labrel16",   new String[]{"building_10_labrel16.ttl"});
        ONTOLOGY_SETS.put("labrel8s",   new String[]{"building_10_labrel8s.ttl"});
        ONTOLOGY_SETS.put("labband",    new String[]{"building_11_labband.ttl"});
        ONTOLOGY_SETS.put("lab4chain3", new String[]{"building_12_chain3.ttl"});
    }

    // Phase 1b: the golden contract is intentionally EXTENDED with the
    // three-valued relevance classification, the qualitative Illuminance
    // direction, and the multi-IV gate collection. Old columns retain their
    // old semantic values on every pre-1b profile (regeneration diff must
    // touch only the new columns for existing rows).
    static final String HEADER =
        "key,label,wotStateType,svBit,expectedBit,zones,hasIV,ivIdx,ivMinRank,energyCost,kgSilent,relevance,illumDirection,ivGates,actionIndex";

    /** Stable identity of an action independent of discovery order. */
    static String key(StereotypeReasoner.ActionInfo ai) {
        if (ai.wotActionType == null) return "DO_NOTHING";
        return ai.wotActionType + "|" + (ai.wotValue ? "ON" : "OFF");
    }

    /** Canonical CSV row for an action (metadata + informational index). */
    static String row(StereotypeReasoner.ActionInfo ai) {
        List<Integer> zs = new ArrayList<>(ai.affectedZones);
        Collections.sort(zs);
        StringBuilder zones = new StringBuilder();
        for (int i = 0; i < zs.size(); i++) {
            if (i > 0) zones.append('|');
            zones.append(zs.get(i));
        }
        StringBuilder gates = new StringBuilder();
        for (int i = 0; i < ai.ivGates.size(); i++) {
            if (i > 0) gates.append('|');
            gates.append(ai.ivGates.get(i)); // "slot>=min"
        }
        return key(ai) + "," + ai.label + ","
             + (ai.wotStateType == null ? "" : ai.wotStateType) + ","
             + ai.stateVecBitIndex + "," + ai.expectedBitValue + ","
             + zones + "," + ai.hasIV + "," + ai.ivStateVecIndex + ","
             + ai.ivMinRank + "," + ai.energyCost + "," + ai.kgSilent + ","
             + ai.relevance + "," + ai.illumDirection + "," + gates + ","
             + ai.actionIndex;
    }

    static List<String> liveRows(String[] onts) {
        StereotypeReasoner r = new StereotypeReasoner(onts, 0.75);
        List<String> rows = new ArrayList<>();
        for (StereotypeReasoner.ActionInfo ai : r.getAllActions()) rows.add(row(ai));
        Collections.sort(rows); // key-sorted → file content is order-independent
        return rows;
    }

    public static void main(String[] args) throws IOException {
        Path outDir = Paths.get(args.length > 0 ? args[0] : "config/golden_registry");
        Files.createDirectories(outDir);
        for (Map.Entry<String, String[]> e : ONTOLOGY_SETS.entrySet()) {
            Path f = outDir.resolve("registry_" + e.getKey() + ".csv");
            try (BufferedWriter w = Files.newBufferedWriter(f, StandardCharsets.UTF_8)) {
                w.write("# action registry golden — ontology set '" + e.getKey()
                      + "' = " + String.join(" + ", e.getValue()));
                w.newLine();
                w.write("# contract = key-set + metadata columns; actionIndex is informational only");
                w.newLine();
                w.write(HEADER);
                w.newLine();
                for (String row : liveRows(e.getValue())) {
                    w.write(row);
                    w.newLine();
                }
            }
            System.out.println("[dump] " + f);
        }
        System.out.println("[dump] " + ONTOLOGY_SETS.size() + " registries written to " + outDir);
    }

    private ActionRegistryDump() { }
}
