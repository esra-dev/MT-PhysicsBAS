package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

/**
 * Phase 1b Stage-0 regression gate for the three-valued relevance
 * classification, the generic qualitative-direction model with multi-IV
 * gates, and the two new default-off consumers (Rule 7 irrelevance prior,
 * Rule 8 band mirror). Mandated by the Phase-1b plan:
 *
 * <ul>
 *   <li>an incomplete stereotype is UNKNOWN, never EXPLICIT_OTHER_DV;</li>
 *   <li>only a complete non-target-DV stereotype receives the irrelevance
 *       prior; UNKNOWN and kgSilent alone never trigger it (verified on the
 *       real monitor information-only / no-stereotype ontologies);</li>
 *   <li>direct/inverse proportionality resolves per action polarity; the
 *       legacy elem:increases shortcut maps to positive direction;</li>
 *   <li>IV-gated negative actions are evaluated only when every gate is
 *       satisfied;</li>
 *   <li>observed positive, negative, and null effects are compared honestly
 *       with their expected signs (gated observations never recorded);</li>
 *   <li>with all knobs at their 0.0 defaults every new channel is inert.</li>
 * </ul>
 */
class Phase1bRelevanceDirectionTest {

    /** Band-style fixture: [Z1Level, Lamp, Blind, Awning, Sunshine]. */
    private static final String BAND_FIXTURE = String.join("\n",
        "@prefix owl:    <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix ws:     <http://example.org/was/lab/stereotypes#> .",
        "@prefix lab:    <http://example.org/was/lab#> .",
        "@prefix elem:   <http://w3id.org/elementary#> .",
        "@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .",
        "@prefix brick:  <https://brickschema.org/schema/Brick#> .",
        "@prefix ex:     <http://example.org/fixture#> .",
        "",
        "# ---- state-slot registry -------------------------------------------",
        "ex:Z1LevelSlot ws:stateVecIndex 0 ; ws:stateDomainSize 4 ;",
        "    ws:stateSlotRole \"zone_level\" ; ws:zoneIndex 1 .",
        "ex:SunshineSlot ws:stateVecIndex 4 ; ws:stateDomainSize 4 ;",
        "    ws:stateSlotRole \"sunshine\" .",
        "",
        "ex:Z1 a lab:Workstation ; ws:zoneIndex 1 .",
        "",
        "ex:dv_illum a elem:DependentVariable ; rdfs:label \"luminescence\" ;",
        "    elem:hasQuantity qudtqk:Illuminance .",
        "",
        "# ---- Lamp: direct proportionality, no IV ---------------------------",
        "ex:lamp_mv a elem:ManipulatedVariable ; elem:directProportion ex:dv_illum .",
        "ex:lamp_mech a elem:PhysicalMechanism ;",
        "    elem:hasManipulatedVariable ex:lamp_mv ;",
        "    elem:hasDependentVariable ex:dv_illum .",
        "ex:lamp_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:lamp_mech ;",
        "    ws:behavioralDescriptionComplete true .",
        "ex:lamp_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:lamp_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Lamp brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:lamp_stereo ;",
        "    elem:hasComponentAction ex:lamp_on, ex:lamp_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetLamp\" ;",
        "    ws:hasWoTStateSemanticType  \"http://example.org/was#Lamp\" ;",
        "    ws:stateVecIndex 1 ; ws:stateDomainSize 2 ; ws:stateSlotRole \"boolean_actuator\" .",
        "",
        "# ---- Blind: direct proportionality, legacy sun IV ------------------",
        "ex:blind_mv a elem:ManipulatedVariable ; elem:directProportion ex:dv_illum .",
        "ex:blind_iv a elem:IndependentVariable ; rdfs:label \"outdoor sun\" .",
        "ex:blind_mech a elem:PhysicalMechanism ;",
        "    elem:hasManipulatedVariable ex:blind_mv ;",
        "    elem:hasDependentVariable ex:dv_illum ;",
        "    elem:hasIndependentVariable ex:blind_iv ;",
        "    ws:ivMinRank 1 .",
        "ex:blind_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:blind_mech ;",
        "    ws:behavioralDescriptionComplete true .",
        "ex:blind_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:blind_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Blind brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:blind_stereo ;",
        "    elem:hasComponentAction ex:blind_on, ex:blind_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetBlind\" ;",
        "    ws:hasWoTStateSemanticType  \"http://example.org/was#Blind\" ;",
        "    ws:stateVecIndex 2 ; ws:stateDomainSize 2 ; ws:stateSlotRole \"boolean_actuator\" .",
        "",
        "# ---- Awning: INVERSE proportionality, TWO IV gates -----------------",
        "#   gate 1 (explicit): daylight path open  -> Blind slot >= 1",
        "#   gate 2 (legacy):   sufficient sun      -> Sunshine slot >= ivMinRank 1",
        "ex:awn_mv a elem:ManipulatedVariable ; elem:inverseProportion ex:dv_illum .",
        "ex:awn_iv_path a elem:IndependentVariable ;",
        "    ws:gateWoTStateSemanticType \"http://example.org/was#Blind\" ;",
        "    ws:gateMinValue 1 .",
        "ex:awn_iv_sun a elem:IndependentVariable ; rdfs:label \"outdoor sun\" .",
        "ex:awn_mech a elem:PhysicalMechanism ;",
        "    elem:hasManipulatedVariable ex:awn_mv ;",
        "    elem:hasDependentVariable ex:dv_illum ;",
        "    elem:hasIndependentVariable ex:awn_iv_path, ex:awn_iv_sun ;",
        "    ws:ivMinRank 1 .",
        "ex:awn_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:awn_mech ;",
        "    ws:behavioralDescriptionComplete true .",
        "ex:awn_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:awn_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Awning brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:awn_stereo ;",
        "    elem:hasComponentAction ex:awn_on, ex:awn_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetAwning\" ;",
        "    ws:hasWoTStateSemanticType  \"http://example.org/was#Awning\" ;",
        "    ws:stateVecIndex 3 ; ws:stateDomainSize 2 ; ws:stateSlotRole \"boolean_actuator\" .",
        "",
        "# ---- Fan: COMPLETE non-target-DV stereotype => EXPLICIT_OTHER_DV ---",
        "ex:dv_air a elem:DependentVariable ; rdfs:label \"airflow\" ;",
        "    elem:hasQuantity qudtqk:VolumeFlowRate .",
        "ex:fan_mv a elem:ManipulatedVariable ; elem:directProportion ex:dv_air .",
        "ex:fan_mech a elem:PhysicalMechanism ;",
        "    elem:hasManipulatedVariable ex:fan_mv ;",
        "    elem:hasDependentVariable ex:dv_air .",
        "ex:fan_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:fan_mech ;",
        "    ws:behavioralDescriptionComplete true .",
        "ex:fan_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:fan_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Fan brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:fan_stereo ;",
        "    elem:hasComponentAction ex:fan_on, ex:fan_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetFan\" .",
        "",
        "# ---- Gadget: PARTIAL stereotype (no DV) => UNKNOWN -----------------",
        "ex:gadget_mv a elem:ManipulatedVariable .",
        "ex:gadget_mech a elem:PhysicalMechanism ;",
        "    elem:hasManipulatedVariable ex:gadget_mv .",
        "ex:gadget_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:gadget_mech ;",
        "    ws:behavioralDescriptionComplete true .",
        "ex:gadget_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:gadget_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Gadget brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:gadget_stereo ;",
        "    elem:hasComponentAction ex:gadget_on, ex:gadget_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetGadget\" .",
        "",
        "# ---- Widget: COMPLETE-LOOKING but marker ABSENT => UNKNOWN ---------",
        "ex:dv_noise a elem:DependentVariable ; rdfs:label \"sound\" ;",
        "    elem:hasQuantity qudtqk:SoundPressureLevel .",
        "ex:widget_mech a elem:PhysicalMechanism ;",
        "    elem:hasDependentVariable ex:dv_noise .",
        "ex:widget_stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:widget_mech .",
        "ex:widget_on  a elem:ComponentAction ; ws:actionValue true .",
        "ex:widget_off a elem:ComponentAction ; ws:actionValue false .",
        "ex:Widget brick:isLocatedIn ex:Z1 ;",
        "    elem:hasBehavioralStereotype ex:widget_stereo ;",
        "    elem:hasComponentAction ex:widget_on, ex:widget_off ;",
        "    ws:hasWoTActionSemanticType \"http://example.org/was#SetWidget\" .",
        "");

    private static StereotypeReasoner bandReasoner() {
        return new StereotypeReasoner(
            new StereotypeReasoner.InMemoryOntologyLoader(BAND_FIXTURE), 0.75);
    }

    private static StereotypeReasoner.ActionInfo find(
            StereotypeReasoner r, String fragment, boolean on) {
        for (StereotypeReasoner.ActionInfo ai : r.getAllActions()) {
            if (ai.wotActionType != null && ai.wotActionType.endsWith("#" + fragment)
                    && ai.wotValue == on) {
                return ai;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------
    // Relevance classification
    // ------------------------------------------------------------------

    @Test
    void relevanceClassifiesAllThreeValues() {
        StereotypeReasoner r = bandReasoner();
        assertEquals(StereotypeReasoner.Relevance.EXPLICIT_RELEVANT,
            find(r, "SetLamp", true).relevance, "Illuminance DV => EXPLICIT_RELEVANT");
        assertEquals(StereotypeReasoner.Relevance.EXPLICIT_OTHER_DV,
            find(r, "SetFan", true).relevance,
            "declared-complete airflow-only stereotype => EXPLICIT_OTHER_DV");
        assertEquals(StereotypeReasoner.Relevance.EXPLICIT_OTHER_DV,
            find(r, "SetFan", false).relevance, "both polarities classified");
        assertEquals(StereotypeReasoner.Relevance.UNKNOWN,
            find(r, "SetGadget", true).relevance,
            "partial stereotype (no DV) must be UNKNOWN, never EXPLICIT_OTHER_DV");
        assertEquals(StereotypeReasoner.Relevance.UNKNOWN,
            find(r, "SetWidget", true).relevance,
            "non-target DV WITHOUT the completeness marker must stay UNKNOWN"
                + " (open-world contract)");
        assertTrue(find(r, "SetFan", true).kgSilent,
            "EXPLICIT_OTHER_DV actions stay kgSilent (no Illuminance claim)");
    }

    // ------------------------------------------------------------------
    // Direction resolution
    // ------------------------------------------------------------------

    @Test
    void directionResolvesPerPolarityAndInverse() {
        StereotypeReasoner r = bandReasoner();
        assertEquals(+1, find(r, "SetLamp", true).illumDirection);
        assertEquals(-1, find(r, "SetLamp", false).illumDirection,
            "reversing a direct-proportion actuator predicts a negative response");
        assertEquals(-1, find(r, "SetAwning", true).illumDirection,
            "activating an inverse-proportion actuator predicts a negative response");
        assertEquals(+1, find(r, "SetAwning", false).illumDirection);
        assertEquals(0, find(r, "SetFan", true).illumDirection,
            "no Illuminance claim => unknown direction");
    }

    @Test
    void legacyIncreasesShortcutMapsToPositiveDirection() {
        String legacy = String.join("\n",
            "@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix ws:     <http://example.org/was/lab/stereotypes#> .",
            "@prefix lab:    <http://example.org/was/lab#> .",
            "@prefix elem:   <http://w3id.org/elementary#> .",
            "@prefix qudtqk: <http://qudt.org/vocab/quantitykind/> .",
            "@prefix brick:  <https://brickschema.org/schema/Brick#> .",
            "@prefix ex:     <http://example.org/fixture#> .",
            "ex:Z1LevelSlot ws:stateVecIndex 0 ; ws:stateDomainSize 4 ;",
            "    ws:stateSlotRole \"zone_level\" ; ws:zoneIndex 1 .",
            "ex:Z1 a lab:Workstation ; ws:zoneIndex 1 .",
            "ex:dv a elem:DependentVariable ; rdfs:label \"luminescence\" ;",
            "    elem:hasQuantity qudtqk:Illuminance .",
            "ex:mech a elem:PhysicalMechanism ;",
            "    elem:hasDependentVariable ex:dv ;",
            "    elem:increases elem:luminiscence .",
            "ex:stereo a elem:Stereotype ; elem:hasPhysicalMechanism ex:mech .",
            "ex:on  a elem:ComponentAction ; ws:actionValue true .",
            "ex:off a elem:ComponentAction ; ws:actionValue false .",
            "ex:OldLamp brick:isLocatedIn ex:Z1 ;",
            "    elem:hasBehavioralStereotype ex:stereo ;",
            "    elem:hasComponentAction ex:on, ex:off ;",
            "    ws:hasWoTActionSemanticType \"http://example.org/was#SetOldLamp\" ;",
            "    ws:hasWoTStateSemanticType  \"http://example.org/was#OldLamp\" ;",
            "    ws:stateVecIndex 1 ; ws:stateDomainSize 2 ; ws:stateSlotRole \"boolean_actuator\" .",
            "");
        StereotypeReasoner r = new StereotypeReasoner(
            new StereotypeReasoner.InMemoryOntologyLoader(legacy), 0.75);
        assertEquals(+1, find(r, "SetOldLamp", true).illumDirection,
            "legacy elem:increases maps to positive direction during discovery");
        assertEquals(-1, find(r, "SetOldLamp", false).illumDirection);
    }

    // ------------------------------------------------------------------
    // Multi-IV gates
    // ------------------------------------------------------------------

    @Test
    void awningCollectsBothIvGatesAndEvaluatesThemAll() {
        StereotypeReasoner r = bandReasoner();
        StereotypeReasoner.ActionInfo awnOn = find(r, "SetAwning", true);
        assertNotNull(awnOn);
        assertEquals(2, awnOn.ivGates.size(),
            "awning must carry BOTH gates (daylight path + sun), got " + awnOn.ivGates);
        assertEquals(2, awnOn.ivGates.get(0).slot, "gate 1 binds the Blind slot");
        assertEquals(4, awnOn.ivGates.get(1).slot, "gate 2 binds the Sunshine slot");
        assertEquals(2, find(r, "SetAwning", false).ivGates.size(),
            "gates attach to BOTH polarities");

        int a = awnOn.actionIndex;
        //                        [Z1, Lamp, Blind, Awning, Sun]
        assertTrue(r.areIvGatesSatisfied(new int[] {0, 0, 1, 0, 2}, a),
            "blind open + sun rank 2 satisfies both gates");
        assertFalse(r.areIvGatesSatisfied(new int[] {0, 0, 0, 0, 2}, a),
            "closed daylight path must fail the gate set even in full sun");
        assertFalse(r.areIvGatesSatisfied(new int[] {0, 0, 1, 0, 0}, a),
            "no sun must fail the gate set even with the path open");
    }

    @Test
    void legacySingleIvActionsGetExactlyTheirLegacyGate() {
        StereotypeReasoner r = bandReasoner();
        StereotypeReasoner.ActionInfo blindOn = find(r, "SetBlind", true);
        assertEquals(1, blindOn.ivGates.size());
        assertEquals(4, blindOn.ivGates.get(0).slot, "legacy IV binds the sunshine slot");
        assertEquals(1, blindOn.ivGates.get(0).minValue);
        assertTrue(find(r, "SetLamp", true).ivGates.isEmpty(),
            "no-IV mechanisms collect no gates");
    }

    // ------------------------------------------------------------------
    // Rule 7 — irrelevance prior (default-off; EXPLICIT_OTHER_DV only)
    // ------------------------------------------------------------------

    @Test
    void irrelevancePriorFiresOnlyForExplicitOtherDv() {
        StereotypeReasoner r = bandReasoner();
        int[] goal = {3};
        int[] state = {0, 0, 0, 0, 0}; // everything off/dark: nothing redundant for ON actions
        int fanOn = find(r, "SetFan", true).actionIndex;
        int gadgetOn = find(r, "SetGadget", true).actionIndex;
        int widgetOn = find(r, "SetWidget", true).actionIndex;

        // Knob OFF (default): channel fully inert.
        assertEquals(0.0, r.getInitPenaltyForZone(state, fanOn, 0, goal), 1e-12,
            "default-off: EXPLICIT_OTHER_DV receives no init prior");

        StereotypeReasoner.setIrrelevantDvPriorForTest(2.0);
        try {
            assertEquals(-1.0, r.getInitPenaltyForZone(state, fanOn, 0, goal), 1e-12,
                "knob 2.0 * initPenaltyScale 0.5 => -1.0 for EXPLICIT_OTHER_DV");
            assertEquals(0.0, r.getInitPenaltyForZone(state, gadgetOn, 0, goal), 1e-12,
                "UNKNOWN (partial stereotype) must NEVER be penalised");
            assertEquals(0.0, r.getInitPenaltyForZone(state, widgetOn, 0, goal), 1e-12,
                "UNKNOWN (no completeness marker) must NEVER be penalised");
        } finally {
            StereotypeReasoner.setIrrelevantDvPriorForTest(0.0);
        }
    }

    @Test
    void monitorIncompleteOntologiesStayUnknownAndUnpenalised() {
        // The real Phase-2.6 monitor variants: information-only (stereotype
        // whose description omits the light side-effect, NOT declared
        // complete) and no-stereotype. Both must classify UNKNOWN and stay
        // unpenalised even with the irrelevance knob ON.
        StereotypeReasoner.setIrrelevantDvPriorForTest(2.0);
        try {
            for (String ttl : new String[] {
                    "building_6_monitor_infoonly.ttl",
                    "building_6_monitor_nostereo.ttl" }) {
                StereotypeReasoner r = new StereotypeReasoner(
                    new StereotypeReasoner.ClasspathOntologyLoader(new String[] {ttl}), 0.75);
                StereotypeReasoner.ActionInfo monOn = find(r, "SetZ1Monitor", true);
                assertNotNull(monOn, ttl + ": monitor action must exist (WoT contract)");
                assertTrue(monOn.kgSilent, ttl + ": monitor stays KG-silent");
                assertEquals(StereotypeReasoner.Relevance.UNKNOWN, monOn.relevance,
                    ttl + ": incomplete KG must classify UNKNOWN");
                // state [Z1Level, Z1Light, Z1Monitor] all-zero: monitor ON not redundant
                assertEquals(0.0,
                    r.getInitPenaltyForZone(new int[] {0, 0, 0}, monOn.actionIndex, 0,
                        new int[] {3}), 1e-12,
                    ttl + ": UNKNOWN action must receive zero init prior");
            }
        } finally {
            StereotypeReasoner.setIrrelevantDvPriorForTest(0.0);
        }
    }

    // ------------------------------------------------------------------
    // Rule 8 — band mirror (default-off)
    // ------------------------------------------------------------------

    @Test
    void bandMirrorPrefersDirectionTowardTheTarget() {
        StereotypeReasoner r = bandReasoner();
        StereotypeReasoner.setBandMirrorInitForTest(5.0);
        try {
            int awnOn  = find(r, "SetAwning", true).actionIndex;
            int awnOff = find(r, "SetAwning", false).actionIndex;
            int lampOn = find(r, "SetLamp", true).actionIndex;

            // ABOVE target (level 3, target 1), gates satisfied (blind open, sun 2):
            int[] above = {3, 0, 1, 0, 2};
            assertEquals(+5.0, r.getInitPenaltyForZone(above, awnOn, 0, new int[] {1}), 1e-12,
                "above target: negative-direction action preferred (+5*|gap 2|*0.5)");
            assertEquals(-5.0, r.getInitPenaltyForZone(above, lampOn, 0, new int[] {1}), 1e-12,
                "above target: positive-direction action softly discouraged");

            // BELOW target: retracting the deployed awning predicts positive.
            int[] below = {0, 0, 1, 1, 2};
            assertEquals(+7.5, r.getInitPenaltyForZone(below, awnOff, 0, new int[] {3}), 1e-12,
                "below target: positive-direction deactivation preferred (+5*3*0.5)");

            // AT target: no direction bonus.
            int[] atTarget = {1, 0, 1, 0, 2};
            assertEquals(0.0, r.getInitPenaltyForZone(atTarget, awnOn, 0, new int[] {1}), 1e-12,
                "at target: no band-mirror term");

            // Gates NOT satisfied (daylight path closed): no direction term.
            int[] gated = {3, 0, 0, 0, 2};
            assertEquals(0.0, r.getInitPenaltyForZone(gated, awnOn, 0, new int[] {1}), 1e-12,
                "IV-gated negative action evaluated only when every gate is satisfied");
        } finally {
            StereotypeReasoner.setBandMirrorInitForTest(0.0);
        }
    }

    @Test
    void bandMirrorLeavesFrozenRulesUntouched() {
        StereotypeReasoner r = bandReasoner();
        int lampOn = find(r, "SetLamp", true).actionIndex;
        int[] below = {0, 0, 0, 0, 0};
        double frozen = r.getInitPenaltyForZone(below, lampOn, 0, new int[] {3});
        assertEquals(15.0 * 3 * 0.5, frozen, 1e-12,
            "Rule 5 constructive endorsement (initBonus 15 * gap 3 * scale 0.5)");
        StereotypeReasoner.setBandMirrorInitForTest(5.0);
        try {
            assertEquals(frozen,
                r.getInitPenaltyForZone(below, lampOn, 0, new int[] {3}), 1e-12,
                "Rule 5's early return preempts the band mirror for aligned"
                    + " below-target activations — frozen values unchanged");
        } finally {
            StereotypeReasoner.setBandMirrorInitForTest(0.0);
        }
    }

    // ------------------------------------------------------------------
    // Honest direction-outcome recording
    // ------------------------------------------------------------------

    @Test
    void directionOutcomesRecordedOnlyWhenEveryGateSatisfied() {
        StereotypeReasoner r = bandReasoner();
        StereotypeReasoner.ActionInfo awnOn = find(r, "SetAwning", true);
        int a = awnOn.actionIndex;

        // GATED observation (daylight path closed): never recorded.
        r.recordActionOutcome(a, new int[] {2, 0, 0, 0, 2}, new int[] {2, 0, 0, 1, 2});
        assertEquals(0, r.getDirectionOutcomeStats(a)[0],
            "a gated observation is not evidence and must not be recorded");

        // Gates satisfied, level fell: MATCH for the inverse mechanism.
        r.recordActionOutcome(a, new int[] {2, 0, 1, 0, 2}, new int[] {1, 0, 1, 1, 2});
        // Gates satisfied, no rank change: NULL observation.
        r.recordActionOutcome(a, new int[] {2, 0, 1, 0, 2}, new int[] {2, 0, 1, 1, 2});
        // Gates satisfied, level ROSE: MISMATCH.
        r.recordActionOutcome(a, new int[] {2, 0, 1, 0, 2}, new int[] {3, 0, 1, 1, 2});

        int[] stats = r.getDirectionOutcomeStats(a);
        assertEquals(3, stats[0], "three gate-satisfied observations");
        assertEquals(1, stats[1], "one observed-sign match");
        assertEquals(1, stats[2], "one honest mismatch");
        assertEquals(1, stats[3], "one null observation (recorded, distinct from mismatch)");
    }

    // ------------------------------------------------------------------
    // Runtime priors (fading channel)
    // ------------------------------------------------------------------

    @Test
    void runtimePriorsInertAtDefaultsAndCorrectWhenEnabled() {
        StereotypeReasoner r = bandReasoner();
        r.setZoneTargets(new int[] {1});
        int awnOn = find(r, "SetAwning", true).actionIndex;
        int fanOn = find(r, "SetFan", true).actionIndex;
        int[] above = {3, 0, 1, 0, 2};

        assertEquals(0.0, r.getActionPriors(above)[awnOn], 1e-12,
            "band-mirror runtime prior inert at knob default");
        assertEquals(0.0, r.getActionPriors(above)[fanOn], 1e-12,
            "irrelevance runtime prior inert at knob default");

        StereotypeReasoner.setBandMirrorPriorForTest(2.0);
        StereotypeReasoner.setIrrelevantDvPriorForTest(1.5);
        try {
            double[] priors = r.getActionPriors(above);
            assertEquals(+2.0, priors[awnOn], 1e-12,
                "above target: negative-direction action gets +bandMirrorPrior");
            assertEquals(-1.5, priors[fanOn], 1e-12,
                "EXPLICIT_OTHER_DV gets -irrelevantDvPrior at runtime");
        } finally {
            StereotypeReasoner.setBandMirrorPriorForTest(0.0);
            StereotypeReasoner.setIrrelevantDvPriorForTest(0.0);
        }
    }
}
