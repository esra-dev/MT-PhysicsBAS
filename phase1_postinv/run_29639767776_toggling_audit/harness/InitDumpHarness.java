package tools;

import java.io.File;
import java.io.PrintWriter;
import java.util.Map;

/**
 * Headless regeneration of the training-start initial Q-table dump
 * (THESIS_STATE_REPORT Addendum 2026-07-18c, Test A, gate G3).
 *
 * Drives the exact code path the training agent uses at startup
 * (illuminance_controller_agent_ql.asl @start):
 *   configureQLearner(goal, useStereotypes=true, ontPaths, sunProb)
 *     -> initWithStereotypes()
 *   saveQTable("qtable_initial_stereotypes_true_lab3.csv")
 * with the lab3 profile constants from lab_profiles.asl:
 *   zone_targets [3,3], ont ["building_3_complex.ttl"], sunshine_prob 0.75.
 * No CArtAgO runtime and no simulator are involved; the init landscape is a
 * deterministic, seed-independent function of KG + goal + config.
 *
 * Also dumps the reasoner's state-slot registry and action metadata to
 * state_layout.json so the offline audit can reconstruct encodeState()
 * indices and map bench-step-log ActionLabels onto Q-table columns.
 */
public final class InitDumpHarness {

    public static void main(String[] args) throws Exception {
        String outDir = args.length > 0 ? args[0] : "initdump_out";
        new File(outDir).mkdirs();

        QLearner ql = new QLearner();
        ql.configureQLearner(new Object[]{3, 3}, true,
                             new Object[]{"building_3_complex.ttl"}, 0.75);
        ql.saveQTable(outDir + "/qtable_initial_stereotypes_true_lab3.csv");

        StereotypeReasoner r =
            new StereotypeReasoner(new String[]{"building_3_complex.ttl"}, 0.75);
        try (PrintWriter pw = new PrintWriter(
                new File(outDir, "state_layout.json"), "UTF-8")) {
            pw.println("{");
            pw.println("  \"profile\": \"lab3\",");
            pw.println("  \"goal\": [3, 3],");
            pw.println("  \"ontology\": [\"building_3_complex.ttl\"],");
            pw.println("  \"sunshineProb\": 0.75,");
            pw.print("  \"domainSizes\": ");   printIntArr(pw, r.getStateDomainSizes());
            pw.println(",");
            pw.print("  \"zoneLevelIndices\": "); printIntArr(pw, r.getZoneLevelIndices());
            pw.println(",");
            pw.println("  \"sunshineIndex\": " + r.getSunshineIndex() + ",");
            pw.println("  \"numActions\": " + r.getNumActions() + ",");
            pw.println("  \"wotStateToSvIndex\": {");
            Map<String, Integer> m = r.getWotStateToSvIndexMap();
            int i = 0;
            for (Map.Entry<String, Integer> e : m.entrySet()) {
                pw.println("    \"" + e.getKey() + "\": " + e.getValue()
                           + (++i < m.size() ? "," : ""));
            }
            pw.println("  },");
            pw.println("  \"actions\": [");
            StereotypeReasoner.ActionInfo[] acts = r.getAllActions();
            for (int a = 0; a < acts.length; a++) {
                StereotypeReasoner.ActionInfo ai = acts[a];
                pw.println("    {\"index\": " + a
                    + ", \"label\": \"" + ai.label + "\""
                    + ", \"wotActionType\": \""
                    + (ai.wotActionType == null ? "" : ai.wotActionType) + "\""
                    + ", \"wotValue\": " + ai.wotValue
                    + ", \"stateVecBitIndex\": " + ai.stateVecBitIndex
                    + ", \"hasIV\": " + ai.hasIV + "}"
                    + (a < acts.length - 1 ? "," : ""));
            }
            pw.println("  ]");
            pw.println("}");
        }
        System.out.println("InitDumpHarness: wrote " + outDir);
    }

    private static void printIntArr(PrintWriter pw, int[] arr) {
        pw.print("[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) pw.print(", ");
            pw.print(arr[i]);
        }
        pw.print("]");
    }
}
