package tools.jia;

import jason.asSemantics.DefaultInternalAction;
import jason.asSemantics.TransitionSystem;
import jason.asSemantics.Unifier;
import jason.asSyntax.StringTerm;
import jason.asSyntax.StringTermImpl;
import jason.asSyntax.Term;

/**
 * Jason internal action: {@code tools.jia.system_prop(+Name, +Default, -Value)} (#7).
 *
 * Reads {@code System.getProperty(Name, Default)} and unifies the result with
 * {@code Value} as a string term. Lets ASL beliefs be parameterised at
 * launch-time via {@code -DName=value} instead of relying on Gradle / PS1
 * file-mutation patches over {@code .asl} sources.
 *
 * Example:
 * <pre>
 *   tools.jia.system_prop("bench.mode", "rule_based", Mode);
 *   +bench_mode(Mode).
 * </pre>
 */
public class SystemProp extends DefaultInternalAction {

    private static final long serialVersionUID = 1L;

    @Override public int getMinArgs() { return 3; }
    @Override public int getMaxArgs() { return 3; }

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        if (!args[0].isString())
            throw new IllegalArgumentException("system_prop: arg 1 (name) must be a string");
        if (!args[1].isString())
            throw new IllegalArgumentException("system_prop: arg 2 (default) must be a string");

        String name = ((StringTerm) args[0]).getString();
        String def  = ((StringTerm) args[1]).getString();
        String val  = System.getProperty(name, def);
        return un.unifies(args[2], new StringTermImpl(val));
    }
}
