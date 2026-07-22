package tools;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.logging.Logger;

import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntModelSpec;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.ModelFactory;

/**
 * OverlaySynthesizer — Phase 5 learned-KG-completion WRITER.
 *
 * Reads the RAW per-(action, state-slot) Welford statistics dumped by
 * {@link StereotypeLearner#saveRawStats} after a training run on a GAPPED
 * knowledge graph, applies the registered emission gates, maps each surviving
 * effect onto a canonical claim (componentURI, kind ∈ {SZ, XZ}, targetZone,
 * sign) via the base KG, and writes:
 *
 *   1. a learned-overlay Turtle file — self-contained {@code learned:}
 *      individuals plus ADD-only link triples on asserted subjects, shaped so
 *      the production {@link StereotypeReasoner} queries pick them up when the
 *      overlay is union-loaded after the gap KG:
 *        • SZ (same-zone) claim: learned:st_/pm_/mv_/dv_ stereotype chain with
 *          an Illuminance-quantity DV, linked via elem:hasBehavioralStereotype
 *          (→ ACTUATOR_DISCOVERY_QUERY enrichment: kgSilent=false, zone set),
 *          plus a brick:feeds arc to the zone's illuminance sensor.
 *        • XZ (cross-zone) claim: learned:st_/pm_/mv_ chain WITHOUT an
 *          Illuminance DV (a cross-zone claim must not imply a same-zone rank
 *          claim), plus brick:feeds to the TARGET zone's sensor and a reified
 *          elem:InternalConnection carrying elem:hasStructuralStereotype
 *          ws:WeakOpticalCoupling (→ CROSS_ZONE_FEEDS_QUERY sees SECONDARY).
 *   2. a claims CSV listing every candidate with its status
 *      (EMITTED / SUPPRESSED) and, where suppressed, the reason.
 *
 * Emission gates (same system properties as StereotypeLearner):
 *   n ≥ stereotype.learner.minSamples (30), z = |μ̂|/(σ̂/√n) ≥
 *   stereotype.learner.zCutoff (3.0), |μ̂| ≥ stereotype.learner.minEffect
 *   (0.05 rank units), ON/OFF sign-mirror consistency (a significant OFF
 *   estimate must carry the opposite sign of the ON estimate).
 *
 * Precedence rules (frozen): learned never overrides asserted. A claim the
 * base KG already makes is suppressed as {@code duplicate_asserted} — this is
 * why the overlay synthesized from a FULL (parent) KG run is expected to be
 * empty (specificity control). A claim whose sign contradicts the asserted
 * surface is suppressed and flagged as {@code sign_conflict_asserted}.
 *
 * Determinism: candidates are processed and emitted in a fixed sort order and
 * numeric formatting is locale-pinned, so the same stats + base KG yield a
 * byte-identical overlay body (idempotent, diffable). The synthesizedAt
 * timestamp lives only on the manifest individual and can be pinned via
 * -Dphase5.synthesizedAt for reproducible output.
 *
 * Multiplicity note: with ~(numActions−1) activation actions × #zone slots
 * z-tests per run at |z| ≥ 3, the expected number of false claims per seed is
 * bounded well below 1; the registered precision metric absorbs any residual.
 *
 * Usage (gradle task synthesizeOverlay):
 *   --stats  &lt;raw stats CSV from saveRawStats&gt;            (required)
 *   --ont    &lt;comma-separated TTLs of the gap profile&gt;     (required;
 *            each entry is tried as a filesystem path first, then classpath)
 *   --out    &lt;overlay TTL output path&gt;                     (required)
 *   --claims &lt;claims CSV output path&gt;                      (required)
 *   --run &lt;runId&gt; --seed &lt;seed&gt; --sourceProfile &lt;profile&gt; --commit &lt;sha&gt;
 */
public class OverlaySynthesizer {

    private static final Logger LOGGER = Logger.getLogger(OverlaySynthesizer.class.getName());

    private static final String PREFIXES =
        "PREFIX brick:  <https://brickschema.org/schema/Brick#>\n" +
        "PREFIX elem:   <http://w3id.org/elementary#>\n" +
        "PREFIX ws:     <http://example.org/was/lab/stereotypes#>\n" +
        "PREFIX lab:    <http://example.org/was/lab#>\n" +
        "PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>\n" +
        "PREFIX sosa:   <http://www.w3.org/ns/sosa/>\n" +
        "PREFIX qudt:   <http://qudt.org/schema/qudt/>\n" +
        "PREFIX qudtqk: <http://qudt.org/vocab/quantitykind/>\n";

    private static final String LEARNED_NS = "http://example.org/was/learned#";

    // -----------------------------------------------------------------------
    // Data structures
    // -----------------------------------------------------------------------

    /** One (action, slot) cell of the raw stats dump. */
    public static class RawStatRow {
        public int actionIdx;
        public String wotActionUri;
        public boolean actionValue;
        public String actionLabel;
        public int svBit;
        public int expectedBit;
        public int slot;
        public long n;
        public double mean;
        public double sd;
    }

    /** Parsed raw stats file (header metadata + rows). */
    public static class RawStats {
        public int numActions;
        public int stateVecLen;
        public boolean flipConditioned;
        public long admittedSamples;
        public long rejectedNoFlip;
        public List<RawStatRow> rows = new ArrayList<>();

        public static RawStats parse(Reader reader) throws IOException {
            RawStats st = new RawStats();
            try (BufferedReader br = new BufferedReader(reader)) {
                String line;
                while ((line = br.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) continue;
                    if (line.startsWith("#")) {
                        String kv = line.substring(1).trim();
                        int eq = kv.indexOf('=');
                        if (eq < 0) continue;
                        String k = kv.substring(0, eq).trim();
                        String v = kv.substring(eq + 1).trim();
                        switch (k) {
                            case "numActions":      st.numActions      = Integer.parseInt(v); break;
                            case "stateVecLen":     st.stateVecLen     = Integer.parseInt(v); break;
                            case "flipConditioned": st.flipConditioned = Boolean.parseBoolean(v); break;
                            case "admittedSamples": st.admittedSamples = Long.parseLong(v); break;
                            case "rejectedNoFlip":  st.rejectedNoFlip  = Long.parseLong(v); break;
                            default: break;
                        }
                        continue;
                    }
                    if (line.startsWith("actionIdx,")) continue; // column header
                    String[] f = line.split(",", -1);
                    if (f.length < 10) continue;
                    RawStatRow r = new RawStatRow();
                    r.actionIdx    = Integer.parseInt(f[0]);
                    r.wotActionUri = f[1];
                    r.actionValue  = Boolean.parseBoolean(f[2]);
                    r.actionLabel  = f[3];
                    r.svBit        = Integer.parseInt(f[4]);
                    r.expectedBit  = Integer.parseInt(f[5]);
                    r.slot         = Integer.parseInt(f[6]);
                    r.n            = Long.parseLong(f[7]);
                    r.mean         = Double.parseDouble(f[8]);
                    r.sd           = Double.parseDouble(f[9]);
                    st.rows.add(r);
                }
            }
            return st;
        }
    }

    /** Emission gates; defaults mirror StereotypeLearner's system properties. */
    public static class Gates {
        public int minSamples;
        public double zCutoff;
        public double minEffect;
        public Gates() {
            minSamples = Integer.parseInt(System.getProperty("stereotype.learner.minSamples", "30"));
            zCutoff    = Double.parseDouble(System.getProperty("stereotype.learner.zCutoff", "3.0"));
            minEffect  = Double.parseDouble(System.getProperty("stereotype.learner.minEffect", "0.05"));
        }
        public Gates(int minSamples, double zCutoff, double minEffect) {
            this.minSamples = minSamples;
            this.zCutoff = zCutoff;
            this.minEffect = minEffect;
        }
    }

    /** Provenance stamped into the overlay manifest. */
    public static class Provenance {
        public String sourceRun = "";
        public String sourceSeed = "";
        public String sourceProfile = "";
        public String instrumentCommit = "";
        public String synthesizedAt =
            System.getProperty("phase5.synthesizedAt",
                java.time.format.DateTimeFormatter.ISO_INSTANT
                    .format(java.time.Instant.now().truncatedTo(java.time.temporal.ChronoUnit.SECONDS)));
    }

    /** Canonical claim: one candidate (activation action × zone-level slot). */
    public static class Claim {
        public String status;        // EMITTED | SUPPRESSED
        public String reason;        // empty when EMITTED
        public String componentUri;
        public String kind;          // SZ | XZ ("" when unresolvable)
        public int targetZoneIdx1;   // 1-based ws:zoneIndex (-1 when unresolvable)
        public int sign;             // +1 / -1 (0 when below gates)
        public String actionUri;
        public int slot;
        public long n;
        public double mean;
        public double z;
    }

    /** Synthesis output: overlay Turtle text + full candidate claim list. */
    public static class Result {
        public String turtle;
        public List<Claim> claims = new ArrayList<>();
        public int emittedCount;
    }

    // Suppression reasons (claims CSV vocabulary).
    static final String R_INSUFFICIENT_SAMPLES  = "insufficient_samples";
    static final String R_Z_BELOW_CUTOFF        = "z_below_cutoff";
    static final String R_EFFECT_BELOW_MIN      = "effect_below_min";
    static final String R_SIGN_MIRROR_VIOLATION = "sign_mirror_violation";
    static final String R_DUPLICATE_ASSERTED    = "duplicate_asserted";
    static final String R_SIGN_CONFLICT         = "sign_conflict_asserted";
    static final String R_NO_COMPONENT_MAPPING  = "no_component_mapping";
    static final String R_NO_TARGET_SENSOR      = "no_target_sensor";

    private static final double EPS = 1e-9;

    // -----------------------------------------------------------------------
    // Base-KG surface extraction
    // -----------------------------------------------------------------------

    /** Everything the synthesizer needs to know about the base (gap) KG. */
    static class BaseSurface {
        Map<String, String>  actionUriToComp   = new TreeMap<>(); // wot action URI -> component URI
        Map<String, Integer> compZone          = new HashMap<>(); // component URI -> 1-based zone idx
        Map<Integer, Integer> slotToZone       = new TreeMap<>(); // sv slot -> 1-based zone idx
        Map<Integer, String> zoneSensor        = new TreeMap<>(); // 1-based zone idx -> sensor URI
        Set<String> assertedSz                 = new HashSet<>(); // compUri + "|" + zoneIdx1
        Set<String> assertedXz                 = new HashSet<>(); // compUri + "|" + targetZoneIdx1
    }

    static BaseSurface extractSurface(OntModel model) {
        BaseSurface s = new BaseSurface();

        // WoT action URI -> component + component zone. Deterministic: on a
        // shared action URI keep the lexicographically smallest component.
        String q1 = PREFIXES +
            "SELECT ?comp ?uri ?zoneIdx WHERE {\n" +
            "  ?comp ws:hasWoTActionSemanticType ?uri .\n" +
            "  OPTIONAL { ?comp brick:isLocatedIn ?zone . ?zone ws:zoneIndex ?zoneIdx . }\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(q1, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                if (!qs.get("comp").isResource()) continue;
                String comp = qs.getResource("comp").getURI();
                String uri  = qs.getLiteral("uri").getString();
                String prev = s.actionUriToComp.get(uri);
                if (prev == null || comp.compareTo(prev) < 0) s.actionUriToComp.put(uri, comp);
                if (qs.contains("zoneIdx")) s.compZone.put(comp, qs.getLiteral("zoneIdx").getInt());
            }
        }

        // Zone-level state slots (same registry the reasoner loads).
        String q2 = PREFIXES +
            "SELECT ?svIdx ?zoneIdx WHERE {\n" +
            "  ?slot ws:stateVecIndex ?svIdx ;\n" +
            "        ws:stateSlotRole \"zone_level\" ;\n" +
            "        ws:zoneIndex     ?zoneIdx .\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(q2, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                s.slotToZone.put(qs.getLiteral("svIdx").getInt(), qs.getLiteral("zoneIdx").getInt());
            }
        }

        // Per-zone illuminance sensor (feeds / conn target). Deterministic on
        // multiple sensors per zone: lexicographically smallest URI.
        String q3 = PREFIXES +
            "SELECT ?sensor ?zoneIdx WHERE {\n" +
            "  ?sensor brick:isLocatedIn ?zone .\n" +
            "  ?zone   ws:zoneIndex      ?zoneIdx .\n" +
            "  ?sensor sosa:observes     ?prop .\n" +
            "  ?prop   qudt:hasQuantityKind qudtqk:Illuminance .\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(q3, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                String sensor = qs.getResource("sensor").getURI();
                int zi = qs.getLiteral("zoneIdx").getInt();
                String prev = s.zoneSensor.get(zi);
                if (prev == null || sensor.compareTo(prev) < 0) s.zoneSensor.put(zi, sensor);
            }
        }

        // Asserted SAME-ZONE enrichment surface: components whose (asserted,
        // non-learned) behavioral stereotype already claims an Illuminance DV.
        // The learned: filter makes re-running on gap+overlay idempotent.
        String q4 = PREFIXES +
            "SELECT DISTINCT ?comp ?zoneIdx WHERE {\n" +
            "  ?comp brick:isLocatedIn ?zone .\n" +
            "  ?zone ws:zoneIndex      ?zoneIdx .\n" +
            "  ?comp elem:hasBehavioralStereotype ?st .\n" +
            "  ?st   elem:hasPhysicalMechanism    ?m .\n" +
            "  ?m    elem:hasManipulatedVariable  ?mv .\n" +
            "  ?m    elem:hasDependentVariable    ?dv .\n" +
            "  FILTER EXISTS { ?dv elem:hasQuantity qudtqk:Illuminance }\n" +
            "  FILTER (!STRSTARTS(STR(?st), \"" + LEARNED_NS + "\"))\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(q4, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                s.assertedSz.add(qs.getResource("comp").getURI() + "|" + qs.getLiteral("zoneIdx").getInt());
            }
        }

        // Asserted CROSS-ZONE surface: any feeds arc from a located component
        // into a different zone.
        String q5 = PREFIXES +
            "SELECT DISTINCT ?comp ?tIdx WHERE {\n" +
            "  ?comp brick:feeds       ?t .\n" +
            "  ?comp brick:isLocatedIn ?sz . ?sz ws:zoneIndex ?sIdx .\n" +
            "  ?t    brick:isLocatedIn ?tz . ?tz ws:zoneIndex ?tIdx .\n" +
            "  FILTER (?sIdx != ?tIdx)\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(q5, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                s.assertedXz.add(qs.getResource("comp").getURI() + "|" + qs.getLiteral("tIdx").getInt());
            }
        }
        return s;
    }

    // -----------------------------------------------------------------------
    // Synthesis
    // -----------------------------------------------------------------------

    /** Synthesize with gates read from system properties. */
    public static Result synthesize(RawStats stats, OntModel baseModel, Provenance prov) {
        return synthesize(stats, baseModel, prov, new Gates());
    }

    /**
     * Core pipeline: candidates = (activation action with a WoT URI) ×
     * (zone-level slot); each passes the emission gates, sign-mirror check and
     * asserted-surface dedup, then is rendered into the overlay Turtle.
     */
    public static Result synthesize(RawStats stats, OntModel baseModel, Provenance prov, Gates gates) {
        BaseSurface surface = extractSurface(baseModel);
        Result result = new Result();

        // Index OFF rows for the sign-mirror check: uri|slot -> row.
        Map<String, RawStatRow> offRows = new HashMap<>();
        for (RawStatRow r : stats.rows) {
            if (!r.actionValue && !r.wotActionUri.isEmpty()) {
                offRows.put(r.wotActionUri + "|" + r.slot, r);
            }
        }

        // Candidate rows: activation actions with a WoT URI, zone-level slots
        // only, in deterministic (uri, slot) order.
        List<RawStatRow> candidates = new ArrayList<>();
        for (RawStatRow r : stats.rows) {
            if (r.actionValue && !r.wotActionUri.isEmpty()
                    && surface.slotToZone.containsKey(r.slot)) {
                candidates.add(r);
            }
        }
        candidates.sort(Comparator.comparing((RawStatRow r) -> r.wotActionUri)
                                  .thenComparingInt(r -> r.slot));

        List<Claim> emitted = new ArrayList<>();
        for (RawStatRow r : candidates) {
            Claim c = new Claim();
            c.actionUri = r.wotActionUri;
            c.slot = r.slot;
            c.n = r.n;
            c.mean = r.mean;
            c.z = zScore(r);
            c.targetZoneIdx1 = surface.slotToZone.get(r.slot);
            c.sign = (r.mean > 0) ? 1 : (r.mean < 0 ? -1 : 0);
            c.kind = "";
            c.componentUri = surface.actionUriToComp.getOrDefault(r.wotActionUri, "");
            result.claims.add(c);

            // Gate pipeline, first failure wins.
            if (c.componentUri.isEmpty() || !surface.compZone.containsKey(c.componentUri)) {
                suppress(c, R_NO_COMPONENT_MAPPING); continue;
            }
            int compZone = surface.compZone.get(c.componentUri);
            c.kind = (compZone == c.targetZoneIdx1) ? "SZ" : "XZ";
            if (r.n < gates.minSamples)             { suppress(c, R_INSUFFICIENT_SAMPLES); continue; }
            if (c.z < gates.zCutoff)                { suppress(c, R_Z_BELOW_CUTOFF); continue; }
            if (Math.abs(r.mean) < gates.minEffect) { suppress(c, R_EFFECT_BELOW_MIN); continue; }

            // ON/OFF sign-mirror consistency: a significant OFF estimate on the
            // same slot must carry the OPPOSITE sign. An insignificant OFF
            // estimate cannot disconfirm (e.g. flip-conditioning admits few
            // OFF samples when the policy rarely turns the device off).
            RawStatRow off = offRows.get(r.wotActionUri + "|" + r.slot);
            if (off != null && off.n >= gates.minSamples
                    && zScore(off) >= gates.zCutoff
                    && Math.abs(off.mean) >= gates.minEffect
                    && Math.signum(off.mean) == Math.signum(r.mean)) {
                suppress(c, R_SIGN_MIRROR_VIOLATION); continue;
            }

            // Precedence: learned never overrides (or duplicates) asserted.
            boolean assertedHere = "SZ".equals(c.kind)
                ? surface.assertedSz.contains(c.componentUri + "|" + c.targetZoneIdx1)
                : surface.assertedXz.contains(c.componentUri + "|" + c.targetZoneIdx1);
            if (assertedHere) {
                // Asserted claims are positive (elem:increases convention); a
                // learned negative estimate on the same surface is a conflict.
                suppress(c, (c.sign > 0) ? R_DUPLICATE_ASSERTED : R_SIGN_CONFLICT);
                continue;
            }

            // XZ emission needs the target zone's sensor for feeds/connTarget.
            if ("XZ".equals(c.kind) && !surface.zoneSensor.containsKey(c.targetZoneIdx1)) {
                suppress(c, R_NO_TARGET_SENSOR); continue;
            }

            c.status = "EMITTED";
            c.reason = "";
            emitted.add(c);
        }

        emitted.sort(Comparator.comparing((Claim c) -> localName(c.componentUri))
                               .thenComparingInt(c -> c.targetZoneIdx1)
                               .thenComparing(c -> c.kind));
        result.emittedCount = emitted.size();
        result.turtle = renderTurtle(emitted, surface, stats, prov);
        return result;
    }

    private static void suppress(Claim c, String reason) {
        c.status = "SUPPRESSED";
        c.reason = reason;
    }

    private static double zScore(RawStatRow r) {
        if (r.n <= 0) return 0.0;
        double sem = r.sd / Math.sqrt(r.n);
        return Math.abs(r.mean) / Math.max(sem, EPS);
    }

    static String localName(String uri) {
        int h = Math.max(uri.lastIndexOf('#'), uri.lastIndexOf('/'));
        String local = (h >= 0) ? uri.substring(h + 1) : uri;
        return local.replaceAll("[^A-Za-z0-9_]", "_");
    }

    // -----------------------------------------------------------------------
    // Turtle rendering
    // -----------------------------------------------------------------------

    private static String renderTurtle(List<Claim> emitted, BaseSurface surface,
                                       RawStats stats, Provenance prov) {
        StringBuilder sb = new StringBuilder(4096);
        sb.append("@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n");
        sb.append("@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .\n");
        sb.append("@prefix owl:     <http://www.w3.org/2002/07/owl#> .\n");
        sb.append("@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .\n");
        sb.append("@prefix brick:   <https://brickschema.org/schema/Brick#> .\n");
        sb.append("@prefix elem:    <http://w3id.org/elementary#> .\n");
        sb.append("@prefix qudtqk:  <http://qudt.org/vocab/quantitykind/> .\n");
        sb.append("@prefix lab:     <http://example.org/was/lab#> .\n");
        sb.append("@prefix ws:      <http://example.org/was/lab/stereotypes#> .\n");
        sb.append("@prefix learned: <").append(LEARNED_NS).append("> .\n");
        sb.append("\n");
        sb.append("# Learned KG overlay — auto-generated by tools.OverlaySynthesizer.\n");
        sb.append("# Precedence: learned never overrides asserted; duplicates and sign\n");
        sb.append("# conflicts vs the base KG are suppressed at synthesis time (see the\n");
        sb.append("# companion learned_claims CSV for the full candidate audit).\n");
        sb.append("\n");

        // Manifest (file-level provenance). learned:-only vocabulary — inert
        // to every StereotypeReasoner query, so a claim-free overlay (or the
        // committed prefixes-only placeholder) never changes behaviour.
        sb.append("learned:overlay_manifest a owl:NamedIndividual, learned:OverlayManifest ;\n");
        sb.append("    learned:sourceRun        \"").append(escape(prov.sourceRun)).append("\" ;\n");
        sb.append("    learned:sourceSeed       ").append(intOrString(prov.sourceSeed)).append(" ;\n");
        sb.append("    learned:sourceProfile    \"").append(escape(prov.sourceProfile)).append("\" ;\n");
        sb.append("    learned:instrumentCommit \"").append(escape(prov.instrumentCommit)).append("\" ;\n");
        sb.append("    learned:flipConditioned  \"").append(stats.flipConditioned).append("\"^^xsd:boolean ;\n");
        sb.append("    learned:synthesizedAt    \"").append(escape(prov.synthesizedAt)).append("\"^^xsd:dateTime ;\n");
        sb.append("    learned:claimCount       \"").append(emitted.size()).append("\"^^xsd:int .\n");

        Set<String> emittedMvs = new LinkedHashSet<>();
        for (Claim c : emitted) {
            String comp = localName(c.componentUri);
            String suffix = comp + "_z" + c.targetZoneIdx1;
            String st = "learned:st_" + suffix;
            String pm = "learned:pm_" + suffix;
            String mv = "learned:mv_" + comp;
            String dv = "learned:dv_" + suffix;
            String sensorUri = surface.zoneSensor.get(c.targetZoneIdx1); // may be null for SZ
            String signWord = (c.sign > 0) ? "increases" : "decreases";

            sb.append("\n");
            sb.append("# ").append(c.kind).append(" claim: ").append(comp)
              .append(" ").append(signWord).append(" zone ").append(c.targetZoneIdx1)
              .append(" illuminance (n=").append(c.n)
              .append(", meanDelta=").append(fmt4(c.mean))
              .append(", z=").append(fmt2(c.z)).append(")\n");

            sb.append(st).append(" a owl:NamedIndividual, elem:Stereotype ;\n");
            sb.append("    rdfs:label \"Learned stereotype: ").append(comp)
              .append(" ").append(signWord).append(" zone ").append(c.targetZoneIdx1)
              .append(" illuminance\" ;\n");
            sb.append("    elem:hasPhysicalMechanism ").append(pm).append(" .\n");

            sb.append(pm).append(" a owl:NamedIndividual, elem:PhysicalMechanism ;\n");
            sb.append("    rdfs:label \"learned_pm_").append(suffix).append("\" ;\n");
            sb.append("    elem:hasManipulatedVariable ").append(mv).append(" ;\n");
            if ("SZ".equals(c.kind)) {
                // The Illuminance-quantity DV is what makes the enrichment
                // query annotate the component's own zone. XZ claims omit it:
                // their zone claim travels through the feeds arc + reified
                // weak coupling below, never through the component's location.
                sb.append("    elem:hasDependentVariable ").append(dv).append(" ;\n");
                sb.append("    elem:").append(signWord).append(" ").append(dv).append(" ;\n");
            }
            sb.append("    learned:sampleCount \"").append(c.n).append("\"^^xsd:int ;\n");
            sb.append("    learned:meanDelta   \"").append(fmt4(c.mean)).append("\"^^xsd:double ;\n");
            sb.append("    learned:zScore      \"").append(fmt2(c.z)).append("\"^^xsd:double ;\n");
            sb.append("    learned:sourceRun   \"").append(escape(prov.sourceRun)).append("\" ;\n");
            sb.append("    learned:sourceSeed  ").append(intOrString(prov.sourceSeed)).append(" .\n");

            if (emittedMvs.add(mv)) {
                sb.append(mv).append(" a owl:NamedIndividual, elem:ProcessVariable ;\n");
                sb.append("    rdfs:label \"Learned manipulated variable: commanded state of ")
                  .append(comp).append("\" .\n");
            }
            if ("SZ".equals(c.kind)) {
                sb.append(dv).append(" a owl:NamedIndividual, elem:ProcessVariable ;\n");
                sb.append("    rdfs:label \"Learned dependent variable: zone ")
                  .append(c.targetZoneIdx1).append(" illuminance\" ;\n");
                sb.append("    elem:hasQuantity qudtqk:Illuminance .\n");
            }

            // ADD-only link triples on asserted subjects.
            sb.append("<").append(c.componentUri).append("> elem:hasBehavioralStereotype ")
              .append(st).append(" .\n");
            if (sensorUri != null) {
                sb.append("<").append(c.componentUri).append("> brick:feeds <")
                  .append(sensorUri).append("> .\n");
            }
            if ("XZ".equals(c.kind)) {
                String conn = "learned:conn_" + comp + "_to_" + localName(sensorUri);
                sb.append(conn).append(" a owl:NamedIndividual, elem:InternalConnection ;\n");
                sb.append("    rdfs:label \"Learned cross-zone spill: ").append(comp)
                  .append(" -> ").append(localName(sensorUri)).append("\" ;\n");
                sb.append("    ws:connSource <").append(c.componentUri).append("> ;\n");
                sb.append("    ws:connTarget <").append(sensorUri).append("> ;\n");
                sb.append("    elem:hasStructuralStereotype ws:WeakOpticalCoupling .\n");
            }
        }
        return sb.toString();
    }

    private static String fmt4(double d) { return String.format(Locale.ROOT, "%.4f", d); }
    private static String fmt2(double d) { return String.format(Locale.ROOT, "%.2f", d); }

    private static String intOrString(String s) {
        if (s != null && s.matches("-?\\d+")) return "\"" + s + "\"^^xsd:int";
        return "\"" + escape(s == null ? "" : s) + "\"";
    }

    private static String escape(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
    }

    // -----------------------------------------------------------------------
    // Claims CSV
    // -----------------------------------------------------------------------

    public static void writeClaimsCsv(List<Claim> claims, PrintWriter pw) {
        pw.println("status,component,kind,target_zone,sign,action_uri,slot,n,mean_delta,z_score,reason");
        for (Claim c : claims) {
            pw.println(c.status + ","
                     + c.componentUri + ","
                     + c.kind + ","
                     + c.targetZoneIdx1 + ","
                     + (c.sign > 0 ? "+" : (c.sign < 0 ? "-" : "0")) + ","
                     + c.actionUri + ","
                     + c.slot + ","
                     + c.n + ","
                     + fmt4(c.mean) + ","
                     + fmt2(c.z) + ","
                     + c.reason);
        }
    }

    // -----------------------------------------------------------------------
    // CLI entry point
    // -----------------------------------------------------------------------

    /** Load each TTL from the filesystem when present, else the classpath. */
    static OntModel loadBaseModel(String[] paths) {
        OntModel model = ModelFactory.createOntologyModel(OntModelSpec.OWL_MEM_MICRO_RULE_INF);
        for (String path : paths) {
            File f = new File(path);
            if (f.isFile()) {
                model.read(f.toURI().toString(), "TURTLE");
                LOGGER.info("OverlaySynthesizer: loaded ontology from file " + path);
            } else {
                InputStream is = OverlaySynthesizer.class.getClassLoader().getResourceAsStream(path);
                if (is == null) {
                    throw new RuntimeException(
                        "OverlaySynthesizer: ontology not found as file or classpath resource: " + path);
                }
                model.read(is, null, "TURTLE");
                LOGGER.info("OverlaySynthesizer: loaded ontology from classpath " + path);
            }
        }
        return model;
    }

    public static void main(String[] args) throws Exception {
        Map<String, String> opt = new HashMap<>();
        for (int i = 0; i + 1 < args.length; i += 2) {
            if (!args[i].startsWith("--")) {
                throw new IllegalArgumentException("Unexpected argument: " + args[i]);
            }
            opt.put(args[i].substring(2), args[i + 1]);
        }
        for (String required : new String[]{"stats", "ont", "out", "claims"}) {
            if (!opt.containsKey(required)) {
                System.err.println("Usage: tools.OverlaySynthesizer --stats <raw_stats.csv>"
                    + " --ont <a.ttl[,b.ttl…]> --out <overlay.ttl> --claims <claims.csv>"
                    + " [--run <id>] [--seed <n>] [--sourceProfile <p>] [--commit <sha>]");
                throw new IllegalArgumentException("Missing required option --" + required);
            }
        }

        RawStats stats;
        try (Reader r = new FileReader(opt.get("stats"))) {
            stats = RawStats.parse(r);
        }
        OntModel base = loadBaseModel(opt.get("ont").split(","));
        Provenance prov = new Provenance();
        prov.sourceRun        = opt.getOrDefault("run", "");
        prov.sourceSeed       = opt.getOrDefault("seed", "");
        prov.sourceProfile    = opt.getOrDefault("sourceProfile", "");
        prov.instrumentCommit = opt.getOrDefault("commit", "");

        Result result = synthesize(stats, base, prov);
        base.close();

        File outFile = new File(opt.get("out"));
        if (outFile.getParentFile() != null) outFile.getParentFile().mkdirs();
        try (PrintWriter pw = new PrintWriter(new FileWriter(outFile))) {
            pw.print(result.turtle);
        }
        File claimsFile = new File(opt.get("claims"));
        if (claimsFile.getParentFile() != null) claimsFile.getParentFile().mkdirs();
        try (PrintWriter pw = new PrintWriter(new FileWriter(claimsFile))) {
            writeClaimsCsv(result.claims, pw);
        }

        int suppressed = result.claims.size() - result.emittedCount;
        System.out.println("OverlaySynthesizer: " + result.emittedCount + " claim(s) emitted, "
            + suppressed + " suppressed -> " + outFile.getPath()
            + " (claims: " + claimsFile.getPath() + ")");
    }
}
