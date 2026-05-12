package tools;

import java.util.logging.LogManager;

import org.slf4j.bridge.SLF4JBridgeHandler;

/**
 * One-shot bridge from {@code java.util.logging} to SLF4J (#4).
 *
 * Several classes in this project use {@code java.util.logging.Logger}
 * (LabEnvironment, StereotypeReasoner, …). Without this bridge those records
 * would bypass the Logback structured pipeline.
 *
 * Idempotent — safe to call multiple times.
 */
public final class LoggingBootstrap {

    private static volatile boolean installed = false;

    private LoggingBootstrap() {}

    /** Install the JUL → SLF4J bridge. Cheap on second and later calls. */
    public static synchronized void install() {
        if (installed) return;
        // Remove existing JUL handlers (otherwise they double-print).
        LogManager.getLogManager().reset();
        SLF4JBridgeHandler.removeHandlersForRootLogger();
        SLF4JBridgeHandler.install();
        installed = true;
    }
}
