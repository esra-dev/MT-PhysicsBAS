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

        // ── Diagnostic: dump thread state on JVM exit ───────────────────
        // Several debugging sessions have observed the JVM ending cleanly
        // mid-training with no error trace. A shutdown hook writes the
        // state of every thread to log/shutdown-threaddump.txt so we can
        // see WHY waitEnd returned. Output goes to a file (NOT stderr) so
        // that PowerShell wrappers with $ErrorActionPreference=Stop are
        // not tripped by spurious stderr writes during JVM shutdown.
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                java.io.File dir = new java.io.File("log");
                if (!dir.exists()) dir.mkdirs();
                try (java.io.PrintWriter pw = new java.io.PrintWriter(
                        new java.io.FileWriter("log/shutdown-threaddump.txt", true))) {
                    pw.println("===== JVM SHUTDOWN HOOK FIRED at " + new java.util.Date() + " =====");
                    java.lang.management.ThreadInfo[] infos =
                            java.lang.management.ManagementFactory.getThreadMXBean()
                                    .dumpAllThreads(true, true);
                    for (java.lang.management.ThreadInfo ti : infos) {
                        pw.println(ti.toString());
                    }
                    pw.println("===== END THREAD DUMP =====");
                }
            } catch (Throwable t) {
                // swallow — diagnostic only
            }
        }, "shutdown-diag"));
    }
}
