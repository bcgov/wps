package ca.bcgov.plugins.keycloak;

import static org.mockito.Mockito.*;

import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import java.util.Arrays;
import java.util.List;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/**
 * Parameterized tests for missing required authentication parameters
 * Using manual iteration instead of JUnit Parameterized runner to work with Robolectric
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 23)
public class KeycloakPluginAuthMissingParamsTest {
    @Mock
    private PluginCall mockCall;

    @Mock
    private Keycloak mockImplementation;

    private TestableKeycloakPlugin testablePlugin;

    /**
     * Test case data class
     */
    private static class TestCase {
        final String description;
        final String expectedError;
        final String clientId;
        final String authorizationBaseUrl;
        final String redirectUrl;
        final String accessTokenEndpoint;

        TestCase(String description, String expectedError, String clientId,
                 String authorizationBaseUrl, String redirectUrl, String accessTokenEndpoint) {
            this.description = description;
            this.expectedError = expectedError;
            this.clientId = clientId;
            this.authorizationBaseUrl = authorizationBaseUrl;
            this.redirectUrl = redirectUrl;
            this.accessTokenEndpoint = accessTokenEndpoint;
        }
    }

    private static List<TestCase> getTestCases() {
        return Arrays.asList(
            new TestCase("clientId missing", "clientId is required", null, "https://auth.example.com", "ca.bc.gov.asago://callback", "https://auth.example.com/token"),
            new TestCase("clientId empty", "clientId is required", "", "https://auth.example.com", "ca.bc.gov.asago://callback", "https://auth.example.com/token"),
            new TestCase("authorizationBaseUrl missing", "authorizationBaseUrl is required", "test-client", null, "ca.bc.gov.asago://callback", "https://auth.example.com/token"),
            new TestCase("redirectUrl missing", "redirectUrl is required", "test-client", "https://auth.example.com", null, "https://auth.example.com/token"),
            new TestCase("accessTokenEndpoint missing", "accessTokenEndpoint is required", "test-client", "https://auth.example.com", "ca.bc.gov.asago://callback", null)
        );
    }

    @Before
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        testablePlugin = new TestableKeycloakPlugin();
        testablePlugin.setTestImplementation(mockImplementation);
    }

    @Test
    public void testAuthenticate_rejectsWhenParametersMissing() {
        for (TestCase testCase : getTestCases()) {
            // Reset mocks for each iteration
            MockitoAnnotations.openMocks(this);
            testablePlugin = new TestableKeycloakPlugin();
            testablePlugin.setTestImplementation(mockImplementation);

            JSObject data = new JSObject();
            if (testCase.clientId != null && !testCase.clientId.isEmpty()) {
                data.put("clientId", testCase.clientId);
            } else if (testCase.clientId != null) {
                data.put("clientId", testCase.clientId);
            }
            if (testCase.authorizationBaseUrl != null) {
                data.put("authorizationBaseUrl", testCase.authorizationBaseUrl);
            }
            if (testCase.redirectUrl != null) {
                data.put("redirectUrl", testCase.redirectUrl);
            }
            if (testCase.accessTokenEndpoint != null) {
                data.put("accessTokenEndpoint", testCase.accessTokenEndpoint);
            }

            when(mockCall.getData()).thenReturn(data);

            testablePlugin.authenticate(mockCall);

            try {
                verify(mockCall).reject(testCase.expectedError);
            } catch (AssertionError e) {
                throw new AssertionError("Failed for test case: " + testCase.description + " - " + e.getMessage(), e);
            }
        }
    }
}
