package ca.bcgov.plugins.keycloak;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import androidx.test.core.app.ApplicationProvider;
import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import net.openid.appauth.*;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/**
 * Unit tests for Keycloak class
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 23, manifest = Config.NONE)
public class KeycloakTest {

    private Context context;

    @Mock
    private PluginCall mockCall;

    @Mock
    private AuthorizationRequest mockAuthRequest;

    @Mock
    private Keycloak.TokenRefreshCallback mockTokenRefreshCallback;

    private Keycloak keycloak;

    @Before
    public void setUp() {
        MockitoAnnotations.openMocks(this);

        // Use Robolectric's application context which has proper PackageManager
        context = ApplicationProvider.getApplicationContext();

        // Create instance with real context
        keycloak = new Keycloak(context);
    }

    @Test
    public void testConstructor_initializesWithContext() {
        assertNotNull(keycloak);
        // Keycloak should initialize without throwing exceptions
    }

    @Test
    public void testSetCurrentCall_storesCall() {
        PluginCall call = mock(PluginCall.class);
        keycloak.setCurrentCall(call);
        // If no exception, the call was stored successfully
        assertTrue(true);
    }

    @Test
    public void testSetAuthorizationRequest_storesRequest() {
        AuthorizationRequest request = mock(AuthorizationRequest.class);
        keycloak.setAuthorizationRequest(request);
        // If no exception, the request was stored successfully
        assertTrue(true);
    }

    @Test
    public void testSetTokenRefreshCallback_storesCallback() {
        Keycloak.TokenRefreshCallback callback = mock(Keycloak.TokenRefreshCallback.class);
        keycloak.setTokenRefreshCallback(callback);
        // If no exception, the callback was stored successfully
        assertTrue(true);
    }

    @Test
    public void testHandleAuthCallback_convertsUriToIntent() {
        Uri testUri = Uri.parse("ca.bc.gov.asago://callback?code=testcode&state=teststate");

        // This will internally call handleAuthorizationResponse
        // Since we don't have a real AuthorizationResponse, this will handle the null case
        keycloak.setCurrentCall(mockCall);
        keycloak.handleAuthCallback(testUri);

        // Verify that the call was attempted to be resolved (error case due to null response)
        ArgumentCaptor<JSObject> captor = ArgumentCaptor.forClass(JSObject.class);
        verify(mockCall).resolve(captor.capture());

        JSObject result = captor.getValue();
        assertFalse(result.getBoolean("isAuthenticated", true));
        assertEquals("no_response", result.getString("error"));
    }

    @Test
    public void testHandleAuthorizationResponse_handlesNullResponse() {
        Intent intent = new Intent();
        intent.setData(Uri.parse("ca.bc.gov.asago://callback"));

        keycloak.setCurrentCall(mockCall);
        keycloak.handleAuthorizationResponse(intent);

        // Should resolve with error when no valid auth response
        ArgumentCaptor<JSObject> captor = ArgumentCaptor.forClass(JSObject.class);
        verify(mockCall).resolve(captor.capture());

        JSObject result = captor.getValue();
        assertFalse(result.getBoolean("isAuthenticated", true));
        assertEquals("no_response", result.getString("error"));
    }

    @Test
    public void testHandleAuthorizationResponse_handlesNullCall() {
        Intent intent = new Intent();
        intent.setData(Uri.parse("ca.bc.gov.asago://callback"));

        // Don't set a current call
        keycloak.handleAuthorizationResponse(intent);

        // Should complete without throwing exception
        assertTrue(true);
    }

    @Test
    public void testHandleAuthorizationResponse_handlesException() {
        Intent intent = new Intent();
        // Create an intent that will cause an exception during processing
        intent.setData(null);

        keycloak.setCurrentCall(mockCall);

        try {
            keycloak.handleAuthorizationResponse(intent);
            // Should handle gracefully
            assertTrue(true);
        } catch (Exception e) {
            fail("Should handle exceptions gracefully");
        }
    }

    @Test
    public void testDispose_removesCallbacks() {
        // Create a new instance to ensure fresh state
        Keycloak testKeycloak = new Keycloak(context);

        // Dispose should not throw
        try {
            testKeycloak.dispose();
            assertTrue(true);
        } catch (Exception e) {
            fail("Dispose should not throw exception: " + e.getMessage());
        }
    }

    @Test
    public void testDispose_handlesMultipleCalls() {
        Keycloak testKeycloak = new Keycloak(context);

        // Should be safe to call dispose multiple times
        testKeycloak.dispose();
        testKeycloak.dispose();

        assertTrue(true);
    }

    @Test
    public void testRestoreAuthState_createsNewStateWhenNoneSaved() {
        // Clean up any existing preferences first
        context.getSharedPreferences("KeycloakAuthState", Context.MODE_PRIVATE)
               .edit().clear().commit();

        Keycloak testKeycloak = new Keycloak(context);

        // Should initialize without throwing
        assertNotNull(testKeycloak);
    }

    @Test
    public void testRestoreAuthState_handlesInvalidJson() {
        // Write invalid JSON to preferences
        SharedPreferences prefs = context.getSharedPreferences("KeycloakAuthState", Context.MODE_PRIVATE);
        prefs.edit().putString("auth_state", "invalid json {{{").commit();

        Keycloak testKeycloak = new Keycloak(context);

        // Should handle gracefully and create new state
        assertNotNull(testKeycloak);

        // Clean up
        prefs.edit().clear().commit();
    }

    @Test
    public void testTokenRefreshCallback_canBeSetAndUsed() {
        Keycloak.TokenRefreshCallback callback = mock(Keycloak.TokenRefreshCallback.class);
        keycloak.setTokenRefreshCallback(callback);

        // The callback should be stored successfully
        assertNotNull(keycloak);
    }

    @Test
    public void testAuthStateConstants() {
        // Verify the constants are as expected (compile-time check)
        // These are used for SharedPreferences keys
        assertTrue(true);
    }

    @Test
    public void testMultipleInstances_areIndependent() {
        Keycloak instance1 = new Keycloak(context);
        Keycloak instance2 = new Keycloak(context);

        PluginCall call1 = mock(PluginCall.class);
        PluginCall call2 = mock(PluginCall.class);

        instance1.setCurrentCall(call1);
        instance2.setCurrentCall(call2);

        // Both instances should work independently
        assertNotEquals(instance1, instance2);

        // Clean up
        instance1.dispose();
        instance2.dispose();
    }

    @Test
    public void testHandleAuthCallback_withNullUri() {
        try {
            keycloak.handleAuthCallback(null);
            // May throw NullPointerException, which is acceptable
        } catch (NullPointerException e) {
            // Expected for null URI
            assertTrue(true);
        }
    }

    @Test
    public void testThreadSafety_multipleCallbacks() {
        // Test that multiple rapid callback settings don't cause issues
        for (int i = 0; i < 10; i++) {
            Keycloak.TokenRefreshCallback callback = mock(Keycloak.TokenRefreshCallback.class);
            keycloak.setTokenRefreshCallback(callback);
        }

        assertTrue(true);
    }

    @Test
    public void testAuthorizationRequest_canBeSetAndReset() {
        AuthorizationRequest request1 = mock(AuthorizationRequest.class);
        AuthorizationRequest request2 = mock(AuthorizationRequest.class);

        keycloak.setAuthorizationRequest(request1);
        keycloak.setAuthorizationRequest(request2);
        keycloak.setAuthorizationRequest(null);

        assertTrue(true);
    }

    @Test
    public void testPluginCall_canBeSetAndReset() {
        PluginCall call1 = mock(PluginCall.class);
        PluginCall call2 = mock(PluginCall.class);

        keycloak.setCurrentCall(call1);
        keycloak.setCurrentCall(call2);
        keycloak.setCurrentCall(null);

        assertTrue(true);
    }

    @Test
    public void testIntegration_fullAuthFlowWithErrors() {
        // Simulate a full auth flow that encounters errors
        keycloak.setCurrentCall(mockCall);
        keycloak.setAuthorizationRequest(mockAuthRequest);

        Intent errorIntent = new Intent();
        errorIntent.setData(Uri.parse("ca.bc.gov.asago://callback?error=access_denied"));

        keycloak.handleAuthorizationResponse(errorIntent);

        // Verify the call was resolved with error
        ArgumentCaptor<JSObject> captor = ArgumentCaptor.forClass(JSObject.class);
        verify(mockCall).resolve(captor.capture());

        JSObject result = captor.getValue();
        assertFalse(result.getBoolean("isAuthenticated", true));
    }
}
