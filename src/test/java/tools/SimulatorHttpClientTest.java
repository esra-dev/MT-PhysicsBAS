package tools;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.AfterEach;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

class SimulatorHttpClientTest {

    private HttpServer server;
    private int port;
    private SimulatorHttpClient client;

    @BeforeEach
    void setup() throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        port = server.getAddress().getPort();
        server.start();
        client = new SimulatorHttpClient();
        // Fast tests: tight timeouts and 1 ms backoff base.
        client.configure(500, 1000, 3, 1);
    }

    @AfterEach
    void teardown() {
        if (server != null) server.stop(0);
        if (client != null) client.close();
    }

    private void register(String path, HttpHandler handler) {
        server.createContext(path, handler);
    }

    private static void respond(HttpExchange ex, int code, String body) throws IOException {
        byte[] bytes = body.getBytes();
        ex.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(bytes); }
    }

    @Test
    void postJsonReturnsBodyOn200() throws Exception {
        register("/ok", ex -> respond(ex, 200, "hello"));
        SimulatorHttpClient.Result r = client.postJson("http://127.0.0.1:" + port + "/ok", "{}");
        assertEquals(200, r.code);
        assertEquals("hello", r.body);
    }

    @Test
    void postJsonDoesNotRetryOn4xx() throws Exception {
        AtomicInteger hits = new AtomicInteger();
        register("/bad", ex -> {
            hits.incrementAndGet();
            respond(ex, 400, "nope");
        });
        SimulatorHttpClient.Result r = client.postJson("http://127.0.0.1:" + port + "/bad", "{}");
        assertEquals(400, r.code);
        assertEquals(1, hits.get(), "4xx must not be retried");
    }

    @Test
    void postJsonRetriesOn5xxThenSucceeds() throws Exception {
        AtomicInteger hits = new AtomicInteger();
        register("/flaky", ex -> {
            int n = hits.incrementAndGet();
            if (n < 3) respond(ex, 503, "busy");
            else       respond(ex, 200, "ok");
        });
        SimulatorHttpClient.Result r = client.postJson("http://127.0.0.1:" + port + "/flaky", "{}");
        assertEquals(200, r.code);
        assertEquals(3, hits.get());
    }

    @Test
    void postJsonThrowsAfterExhaustingRetriesOnConnectionRefusal() {
        // Pick a port that's almost certainly closed.
        String url = "http://127.0.0.1:1/never";
        assertThrows(SimulatorHttpClient.SimulatorUnreachableException.class,
                () -> client.postJson(url, "{}"));
    }

    @Test
    void configureChangesRetryCount() throws Exception {
        AtomicInteger hits = new AtomicInteger();
        register("/always5xx", ex -> { hits.incrementAndGet(); respond(ex, 500, "x"); });
        client.configure(500, 1000, 0, 1); // zero retries
        SimulatorHttpClient.Result r = client.postJson("http://127.0.0.1:" + port + "/always5xx", "{}");
        assertEquals(500, r.code);
        assertEquals(1, hits.get(), "with maxRetries=0 expect exactly 1 attempt");
    }
}
