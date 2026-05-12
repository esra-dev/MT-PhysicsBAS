package tools.jia;

import org.junit.jupiter.api.AfterEach;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.Test;

import jason.asSemantics.Unifier;
import jason.asSyntax.NumberTermImpl;
import jason.asSyntax.StringTermImpl;
import jason.asSyntax.Term;
import jason.asSyntax.VarTerm;

class SystemPropTest {

    private static final String KEY = "mt.esra.test.sysprop";

    @AfterEach
    void clearProp() { System.clearProperty(KEY); }

    @Test
    void returnsDefaultWhenPropertyAbsent() throws Exception {
        SystemProp ia = new SystemProp();
        Unifier un = new Unifier();
        VarTerm out = new VarTerm("V");
        ia.execute(null, un, new Term[]{
                new StringTermImpl(KEY),
                new StringTermImpl("fallback"),
                out
        });
        assertEquals("fallback", ((jason.asSyntax.StringTerm) un.get(out)).getString());
    }

    @Test
    void returnsPropertyValueWhenSet() throws Exception {
        System.setProperty(KEY, "override-value");
        SystemProp ia = new SystemProp();
        Unifier un = new Unifier();
        VarTerm out = new VarTerm("V");
        ia.execute(null, un, new Term[]{
                new StringTermImpl(KEY),
                new StringTermImpl("fallback"),
                out
        });
        assertEquals("override-value", ((jason.asSyntax.StringTerm) un.get(out)).getString());
    }

    @Test
    void rejectsNonStringName() {
        SystemProp ia = new SystemProp();
        Unifier un = new Unifier();
        VarTerm out = new VarTerm("V");
        assertThrows(IllegalArgumentException.class, () -> ia.execute(null, un, new Term[]{
                new NumberTermImpl(1.0),
                new StringTermImpl("fallback"),
                out
        }));
    }
}
