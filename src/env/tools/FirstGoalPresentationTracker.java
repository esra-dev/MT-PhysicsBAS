package tools;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Scenario-level time-to-first-success tracker for Phase 1 protocol v2. */
public final class FirstGoalPresentationTracker {
    public static final class Record {
        public final int scenarioId;
        public int presentations;
        public Integer firstSuccessPresentation;
        public int terminalAtStartPresentations;

        private Record(int scenarioId) {
            this.scenarioId = scenarioId;
        }

        public boolean censored() {
            return firstSuccessPresentation == null;
        }

        /** Restricted presentation time; never-solved scenarios are censored at N+1. */
        public int analysisValue() {
            return firstSuccessPresentation == null
                    ? presentations + 1 : firstSuccessPresentation;
        }
    }

    private final Map<Integer, Record> records = new LinkedHashMap<>();
    private Integer currentScenarioId;

    public void configure(List<Integer> orderedScenarioIds) {
        records.clear();
        for (Integer id : orderedScenarioIds) {
            if (id == null || records.containsKey(id)) {
                throw new IllegalArgumentException("Scenario IDs must be non-null and unique: " + id);
            }
            records.put(id, new Record(id));
        }
        if (records.isEmpty()) {
            throw new IllegalArgumentException("At least one training scenario is required");
        }
        currentScenarioId = null;
    }

    public void begin(int scenarioId, boolean terminalAtStart) {
        Record record = records.get(scenarioId);
        if (record == null) {
            throw new IllegalArgumentException("Episode used undeclared scenario id " + scenarioId);
        }
        record.presentations++;
        if (terminalAtStart) record.terminalAtStartPresentations++;
        currentScenarioId = scenarioId;
    }

    public void end(boolean successful) {
        if (currentScenarioId == null) {
            throw new IllegalStateException("No scenario-aware episode is active");
        }
        Record record = records.get(currentScenarioId);
        if (successful && record.firstSuccessPresentation == null) {
            record.firstSuccessPresentation = record.presentations;
        }
        currentScenarioId = null;
    }

    public List<Record> records() {
        return Collections.unmodifiableList(new ArrayList<>(records.values()));
    }
}
