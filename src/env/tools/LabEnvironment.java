package tools;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.logging.Logger;

import org.apache.hc.client5.http.impl.DefaultConnectionKeepAliveStrategy;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.http.impl.DefaultConnectionReuseStrategy;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;
import ch.unisg.ics.interactions.wot.td.ThingDescription;
import ch.unisg.ics.interactions.wot.td.ThingDescription.TDFormat;
import ch.unisg.ics.interactions.wot.td.affordances.ActionAffordance;
import ch.unisg.ics.interactions.wot.td.affordances.Form;
import ch.unisg.ics.interactions.wot.td.affordances.PropertyAffordance;
import ch.unisg.ics.interactions.wot.td.clients.TDHttpRequest;
import ch.unisg.ics.interactions.wot.td.clients.TDHttpResponse;
import ch.unisg.ics.interactions.wot.td.io.TDGraphReader;
import ch.unisg.ics.interactions.wot.td.schemas.DataSchema;
import ch.unisg.ics.interactions.wot.td.schemas.ObjectSchema;
import ch.unisg.ics.interactions.wot.td.vocabularies.TD;

/**
 * LabEnvironment artifact for interacting with the lab environment.
 * Provides operations to read the current state and perform actions
 * on the lights and blinds in both workstations.
 * 
 * Works with both simulated and real lab environments via W3C WoT Thing Descriptions.
 */
public class LabEnvironment extends Artifact {

    private ThingDescription td;
    private static final Logger LOGGER = Logger.getLogger(LabEnvironment.class.getName());

    /**
     * Initialize the artifact with a W3C WoT Thing Description URL.
     * 
     * @param tdUrl URL to the Thing Description (simulated or real lab)
     */
    @OPERATION
    public void init(String tdUrl) {
        try {
            CloseableHttpClient httpClient = HttpClients.custom()
                .setConnectionManager(new PoolingHttpClientConnectionManager())
                .setConnectionReuseStrategy(DefaultConnectionReuseStrategy.INSTANCE)
                .setKeepAliveStrategy(DefaultConnectionKeepAliveStrategy.INSTANCE)
                .build();

            this.td = TDGraphReader.readFromURL(TDFormat.RDF_TURTLE, tdUrl);
            LOGGER.info("LabEnvironment initialized with Thing Description from: " + tdUrl);
            
        } catch (IOException e) {
            LOGGER.severe("Failed to initialize LabEnvironment: " + e.getMessage());
        }
    }

    /**
     * Read the current state of the lab environment.
     * 
     * @param z1Level    Output: Illuminance level rank in Zone 1 (0-3)
     * @param z2Level    Output: Illuminance level rank in Zone 2 (0-3)
     * @param z1Light    Output: Light status in Zone 1 (true=on, false=off)
     * @param z2Light    Output: Light status in Zone 2 (true=on, false=off)
     * @param z1Blinds   Output: Blinds status in Zone 1 (true=up, false=down)
     * @param z2Blinds   Output: Blinds status in Zone 2 (true=up, false=down)
     * @param sunshine   Output: Sunshine level rank (0-3)
     */
    @OPERATION
    public void readState(OpFeedbackParam<Integer> z1Level,
                         OpFeedbackParam<Integer> z2Level,
                         OpFeedbackParam<Boolean> z1Light,
                         OpFeedbackParam<Boolean> z2Light,
                         OpFeedbackParam<Boolean> z1Blinds,
                         OpFeedbackParam<Boolean> z2Blinds,
                         OpFeedbackParam<Integer> sunshine) {
        
        Optional<PropertyAffordance> p = this.td.getFirstPropertyBySemanticType("https://example.org/was#Status");

        if (p.isPresent()) {
            Optional<Form> f = p.get().getFirstFormForOperationType(TD.readProperty);
            DataSchema ds = p.get().getDataSchema();

            if (f.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.readProperty);

                try {
                    TDHttpResponse response = request.execute();
                    Map<String, Object> status = response.getPayloadAsObject((ObjectSchema) ds);

                    // Parse and discretize values
                    int z1Lvl = discretizeLightLevel((Double) status.get("http://example.org/was#Z1Level"));
                    int z2Lvl = discretizeLightLevel((Double) status.get("http://example.org/was#Z2Level"));
                    boolean z1Lt = (Boolean) status.get("http://example.org/was#Z1Light");
                    boolean z2Lt = (Boolean) status.get("http://example.org/was#Z2Light");
                    boolean z1Bl = (Boolean) status.get("http://example.org/was#Z1Blinds");
                    boolean z2Bl = (Boolean) status.get("http://example.org/was#Z2Blinds");
                    int sun = discretizeSunshine((Double) status.get("http://example.org/was#Sunshine"));

                    // Set output parameters
                    z1Level.set(z1Lvl);
                    z2Level.set(z2Lvl);
                    z1Light.set(z1Lt);
                    z2Light.set(z2Lt);
                    z1Blinds.set(z1Bl);
                    z2Blinds.set(z2Bl);
                    sunshine.set(sun);

                    LOGGER.info("Read state: Z1Level=" + z1Lvl + ", Z2Level=" + z2Lvl + 
                               ", Z1Light=" + z1Lt + ", Z2Light=" + z2Lt +
                               ", Z1Blinds=" + z1Bl + ", Z2Blinds=" + z2Bl +
                               ", Sunshine=" + sun);

                } catch (IOException e) {
                    LOGGER.severe("Failed to read state: " + e.getMessage());
                }
            }
        }
    }

    /**
     * Read only the illuminance levels (shorthand operation).
     */
    @OPERATION
    public void readIlluminanceLevels(OpFeedbackParam<Integer> z1Level,
                                      OpFeedbackParam<Integer> z2Level) {
        
        Optional<PropertyAffordance> p = this.td.getFirstPropertyBySemanticType("https://example.org/was#Status");

        if (p.isPresent()) {
            Optional<Form> f = p.get().getFirstFormForOperationType(TD.readProperty);
            DataSchema ds = p.get().getDataSchema();

            if (f.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.readProperty);

                try {
                    TDHttpResponse response = request.execute();
                    Map<String, Object> status = response.getPayloadAsObject((ObjectSchema) ds);

                    int z1Lvl = discretizeLightLevel((Double) status.get("http://example.org/was#Z1Level"));
                    int z2Lvl = discretizeLightLevel((Double) status.get("http://example.org/was#Z2Level"));

                    z1Level.set(z1Lvl);
                    z2Level.set(z2Lvl);

                    LOGGER.info("Read illuminance levels: Z1=" + z1Lvl + ", Z2=" + z2Lvl);

                } catch (IOException e) {
                    LOGGER.severe("Failed to read illuminance levels: " + e.getMessage());
                }
            }
        }
    }

    /**
     * Set the light in Zone 1.
     * 
     * @param turnOn True to turn on, false to turn off
     */
    @OPERATION
    public void setZ1Light(boolean turnOn) {
        LOGGER.info("Setting Z1 Light: " + (turnOn ? "ON" : "OFF"));
        performBooleanAction("http://example.org/was#SetZ1Light", turnOn);
    }

    /**
     * Set the light in Zone 2.
     * 
     * @param turnOn True to turn on, false to turn off
     */
    @OPERATION
    public void setZ2Light(boolean turnOn) {
        LOGGER.info("Setting Z2 Light: " + (turnOn ? "ON" : "OFF"));
        performBooleanAction("http://example.org/was#SetZ2Light", turnOn);
    }

    /**
     * Set the blinds in Zone 1.
     * 
     * @param raiseUp True to raise up (open), false to lower down (close)
     */
    @OPERATION
    public void setZ1Blinds(boolean raiseUp) {
        LOGGER.info("Setting Z1 Blinds: " + (raiseUp ? "UP" : "DOWN"));
        performBooleanAction("http://example.org/was#SetZ1Blinds", raiseUp);
    }

    /**
     * Set the blinds in Zone 2.
     * 
     * @param raiseUp True to raise up (open), false to lower down (close)
     */
    @OPERATION
    public void setZ2Blinds(boolean raiseUp) {
        LOGGER.info("Setting Z2 Blinds: " + (raiseUp ? "UP" : "DOWN"));
        performBooleanAction("http://example.org/was#SetZ2Blinds", raiseUp);
    }

    /**
     * Helper method to perform a boolean action on the lab.
     * Gets the property name from the Thing Description schema.
     */
    private void performBooleanAction(String actionType, boolean value) {
        Optional<ActionAffordance> a = this.td.getFirstActionBySemanticType(actionType);

        if (a.isPresent()) {
            Optional<Form> f = a.get().getFirstFormForOperationType(TD.invokeAction);
            Optional<DataSchema> ds = a.get().getInputSchema();

            if (f.isPresent() && ds.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.invokeAction);
                
                // Get the property name from the schema (e.g., "Z1Light" not the full URI)
                Map<String, DataSchema> props = ((ObjectSchema) ds.get()).getProperties();
                Map<String, Object> payload = new HashMap<>();
                
                // Use the first property name from the schema
                for (String propName : props.keySet()) {
                    payload.put(propName, value);
                    LOGGER.info("Action payload: {" + propName + ": " + value + "}");
                }
                
                request.setObjectPayload((ObjectSchema) ds.get(), payload);

                try {
                    TDHttpResponse response = request.execute();
                    LOGGER.info("Action executed successfully. Response code: " + response.getStatusCode());
                } catch (IOException e) {
                    LOGGER.severe("Failed to perform action " + actionType + ": " + e.getMessage());
                }
            }
        } else {
            LOGGER.warning("Action not found in Thing Description: " + actionType);
        }
    }

    /**
     * Maps lux values to light levels:
     * lux < 50 -> level 0
     * lux in [50,100) -> level 1
     * lux in [100,300) -> level 2
     * lux >= 300 -> level 3
     */
    private int discretizeLightLevel(Double value) {
        if (value < 50) {
            return 0;
        } else if (value < 100) {
            return 1;
        } else if (value < 300) {
            return 2;
        }
        return 3;
    }

    /**
     * Maps sunshine values to levels:
     * lux < 50 -> level 0
     * lux in [50,200) -> level 1
     * lux in [200,700) -> level 2
     * lux >= 700 -> level 3
     */
    private int discretizeSunshine(Double value) {
        if (value < 50) {
            return 0;
        } else if (value < 200) {
            return 1;
        } else if (value < 700) {
            return 2;
        }
        return 3;
    }
}
