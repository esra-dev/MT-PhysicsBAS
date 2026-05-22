package tools;

import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;

import java.io.File;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Standalone Turtle validator invoked from the Gradle {@code validateTurtle}
 * task. Walks one or more directories supplied as CLI arguments, parses every
 * {@code *.ttl} file with Apache Jena, and exits with a non-zero status if
 * any file fails to parse.
 *
 * <p>Run via Gradle (preferred) or directly:
 * <pre>{@code
 *   ./gradlew validateTurtle
 *   java -cp <classpath> tools.TurtleValidator src/resources
 * }</pre>
 */
public final class TurtleValidator {
    private TurtleValidator() {}

    public static void main(String[] args) throws Exception {
        List<String> roots = (args.length == 0)
                ? List.of("src/resources")
                : Arrays.asList(args);

        List<Path> ttlFiles = new ArrayList<>();
        for (String root : roots) {
            Path p = Paths.get(root);
            if (!Files.exists(p)) continue;
            try (var stream = Files.walk(p)) {
                ttlFiles.addAll(stream
                        .filter(f -> f.toString().toLowerCase(Locale.ROOT).endsWith(".ttl"))
                        .collect(Collectors.toList()));
            }
        }

        if (ttlFiles.isEmpty()) {
            System.out.println("validateTurtle: no .ttl files found under " + roots);
            return;
        }

        List<String> errors = new ArrayList<>();
        for (Path f : ttlFiles) {
            try {
                Model model = ModelFactory.createDefaultModel();
                model.read(f.toUri().toString(), "TTL");
                System.out.println(" OK   " + f);
            } catch (Throwable t) {
                String msg = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
                System.out.println(" FAIL " + f + " - " + msg);
                errors.add(f + ": " + msg);
            }
        }

        if (!errors.isEmpty()) {
            System.err.println("validateTurtle: " + errors.size() + " file(s) failed to parse.");
            System.exit(1);
        }
    }
}
