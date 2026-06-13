package tools.jia;

import jason.asSemantics.DefaultInternalAction;
import jason.asSemantics.TransitionSystem;
import jason.asSemantics.Unifier;
import jason.asSyntax.NumberTerm;
import jason.asSyntax.NumberTermImpl;
import jason.asSyntax.StringTerm;
import jason.asSyntax.Term;

/**
 * Jason internal action: {@code tools.jia.system_prop_num(+Name, +DefaultNum, -Value)}.
 *
 * Numeric sibling of {@link SystemProp}. Reads {@code System.getProperty(Name)}
 * and unifies {@code Value} with it parsed as a number; if the property is unset
 * or cannot be parsed, unifies {@code Value} with {@code DefaultNum} instead.
 *
 * Lets ASL numeric beliefs (e.g. an episode budget) be parameterised at
 * launch-time via {@code -DName=value} without mutating {@code .asl} sources —
 * the Java-side params already do this through {@code System.getProperty}; this
 * extends the same capability to numbers consumed directly in AgentSpeak.
 *
 * Example:
 * <pre>
 *   tools.jia.system_prop_num("adapt.episodes", 2000, Budget);
 * </pre>
 */
public class system_prop_num extends DefaultInternalAction {

    private static final long serialVersionUID = 1L;

    @Override public int getMinArgs() { return 3; }
    @Override public int getMaxArgs() { return 3; }

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        if (!args[0].isString())
            throw new IllegalArgumentException("system_prop_num: arg 1 (name) must be a string");
        if (!args[1].isNumeric())
            throw new IllegalArgumentException("system_prop_num: arg 2 (default) must be a number");

        String name = ((StringTerm) args[0]).getString();
        double def  = ((NumberTerm) args[1]).solve();

        double val = def;
        String raw = System.getProperty(name);
        if (raw != null && !raw.trim().isEmpty()) {
            try {
                val = Double.parseDouble(raw.trim());
            } catch (NumberFormatException e) {
                val = def;
            }
        }
        return un.unifies(args[2], new NumberTermImpl(val));
    }
}
