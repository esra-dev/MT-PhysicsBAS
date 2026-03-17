package tools;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.io.entity.EntityUtils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;

/**
 * LabStateReader artifact for reading the current state from the lab environment.
 * Works with both simulated and real lab environments through their REST API.
 */
public class LabStateReader extends Artifact {

    private String statusUrl = "http://127.0.0.1:1880/was/rl/status"; // Default, can be overridden by init

    static {
        System.setProperty("java.net.preferIPv4Stack", "true");
        System.setProperty("sun.net.http.allowRestrictedHeaders", "true");
    }

    @OPERATION
    public void init(String url) {
        if (url != null && !url.isEmpty()) {
            this.statusUrl = url;
            System.out.println("LabStateReader initialized with URL: " + this.statusUrl);
        } else {
            System.out.println("LabStateReader initialized with default URL: " + this.statusUrl);
        }
    }

    /**
     * Fetches the current state from the lab's status endpoint and parses the JSON.
     * 
     * @param z1Level      Illuminance level in Zone 1 (double)
     * @param z2Level      Illuminance level in Zone 2 (double)
     * @param z1Light      Light status in Zone 1 (boolean)
     * @param z2Light      Light status in Zone 2 (boolean)
     * @param z1Blinds     Blinds status in Zone 1 (boolean)
     * @param z2Blinds     Blinds status in Zone 2 (boolean)
     * @param sunshine     Sunshine value (double)
     */
    @OPERATION
    public void getCurrentState(OpFeedbackParam<Double> z1Level,
                               OpFeedbackParam<Double> z2Level,
                               OpFeedbackParam<Boolean> z1Light,
                               OpFeedbackParam<Boolean> z2Light,
                               OpFeedbackParam<Boolean> z1Blinds,
                               OpFeedbackParam<Boolean> z2Blinds,
                               OpFeedbackParam<Double> sunshine) {
        try {
            String jsonStr = tryFetchStatus();
            if (jsonStr == null) {
                throw new IOException("Failed to fetch status after multiple attempts using Apache HttpClient.");
            }

            ObjectMapper mapper = new ObjectMapper();
            JsonNode json = mapper.readTree(jsonStr);

            z1Level.set(json.get("Z1Level").asDouble());
            z2Level.set(json.get("Z2Level").asDouble());
            z1Light.set(json.get("Z1Light").asBoolean());
            z2Light.set(json.get("Z2Light").asBoolean());
            z1Blinds.set(json.get("Z1Blinds").asBoolean());
            z2Blinds.set(json.get("Z2Blinds").asBoolean());
            sunshine.set(json.get("Sunshine").asDouble());

        } catch (Exception e) {
            System.err.println("Error in getCurrentState: " + e.getMessage());
        }
    }

    private String tryFetchStatus() {
        int maxRetries = 3;
        // Configure timeouts (in milliseconds for Apache HttpClient 5)
        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectionRequestTimeout(5000, TimeUnit.MILLISECONDS)
                .setConnectTimeout(5000, TimeUnit.MILLISECONDS)
                .setResponseTimeout(5000, TimeUnit.MILLISECONDS)
                .build();

        for (int i = 0; i < maxRetries; i++) {
            System.out.println("Attempt " + (i + 1) + "/" + maxRetries + " to fetch status from " + statusUrl + " using Apache HttpClient");
            try (CloseableHttpClient httpClient = HttpClients.custom().setDefaultRequestConfig(requestConfig).build()) {
                HttpGet request = new HttpGet(statusUrl);
                
                try (CloseableHttpResponse response = httpClient.execute(request)) {
                    int statusCode = response.getCode();
                    if (statusCode >= 200 && statusCode < 300) {
                        String responseBody = EntityUtils.toString(response.getEntity());
                        System.out.println("Successfully fetched status. Status code: " + statusCode);
                        return responseBody;
                    } else {
                        System.err.println("HTTP Error: " + statusCode + " - " + response.getReasonPhrase());
                        EntityUtils.consume(response.getEntity());
                    }
                }
            } catch (Exception e) {
                System.err.println("Attempt " + (i + 1) + " failed: " + e.getClass().getSimpleName() + " - " + e.getMessage());
                if (i < maxRetries - 1) {
                    try {
                        Thread.sleep(1000); // Wait 1 second before retrying
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        System.err.println("Retry wait interrupted.");
                        return null;
                    }
                }
            }
        }
        System.err.println("All attempts to fetch status failed using Apache HttpClient.");
        return null;
    }
}
