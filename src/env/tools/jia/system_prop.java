package tools.jia;

/**
 * Jason resolves fully-qualified internal actions by exact class name.
 *
 * The ASL source calls {@code tools.jia.system_prop(...)}, so this lowercase
 * adapter keeps that stable action name while reusing the tested implementation
 * in {@link SystemProp}.
 */
public class system_prop extends SystemProp {
    private static final long serialVersionUID = 1L;
}
