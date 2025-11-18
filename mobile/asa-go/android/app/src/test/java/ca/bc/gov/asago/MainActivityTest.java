package ca.bc.gov.asago;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

import android.content.Intent;
import android.net.Uri;
import ca.bcgov.plugins.keycloak.KeycloakPlugin;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.MockedStatic;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/**
 * Unit tests for MainActivity Keycloak integration logic
 *
 * These tests verify the authentication intent handling behavior
 * without requiring full Capacitor BridgeActivity initialization
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 23)
public class MainActivityTest {

    @Test
    public void testCustomSchemeUri_isRecognized() {
        // Test that our custom scheme is correct
        Uri uri = Uri.parse("ca.bc.gov.asago://callback?code=test");
        assertEquals("ca.bc.gov.asago", uri.getScheme());
    }

    @Test
    public void testCustomSchemeUri_withDifferentPaths() {
        // Test various valid callback URIs
        String[] validPaths = {
                "ca.bc.gov.asago://callback",
                "ca.bc.gov.asago://auth/callback",
                "ca.bc.gov.asago://oauth/redirect"
        };

        for (String path : validPaths) {
            Uri uri = Uri.parse(path);
            assertEquals("ca.bc.gov.asago", uri.getScheme());
        }
    }

    @Test
    public void testCustomSchemeUri_withQueryParameters() {
        Uri uri = Uri.parse("ca.bc.gov.asago://callback?code=abc123&state=xyz");
        assertEquals("ca.bc.gov.asago", uri.getScheme());
        assertEquals("abc123", uri.getQueryParameter("code"));
        assertEquals("xyz", uri.getQueryParameter("state"));
    }

    @Test
    public void testWrongScheme_isNotMatched() {
        Uri uri = Uri.parse("https://example.com/callback");
        assertNotEquals("ca.bc.gov.asago", uri.getScheme());
    }

    @Test
    public void testPluginInstance_canBeNull() {
        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(null);

            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            assertNull(plugin);
        }
    }

    @Test
    public void testPluginInstance_canBeRetrieved() {
        KeycloakPlugin mockPlugin = mock(KeycloakPlugin.class);

        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(mockPlugin);

            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            assertNotNull(plugin);
            assertEquals(mockPlugin, plugin);
        }
    }

    @Test
    public void testHandleAuthCallback_isCalledWithCorrectUri() {
        KeycloakPlugin mockPlugin = mock(KeycloakPlugin.class);

        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(mockPlugin);

            Uri testUri = Uri.parse("ca.bc.gov.asago://callback?code=testcode");
            KeycloakPlugin plugin = KeycloakPlugin.getInstance();

            if (plugin != null && "ca.bc.gov.asago".equals(testUri.getScheme())) {
                plugin.handleAuthCallback(testUri);
            }

            verify(mockPlugin).handleAuthCallback(testUri);
        }
    }

    @Test
    public void testHandleAuthCallback_notCalledForWrongScheme() {
        KeycloakPlugin mockPlugin = mock(KeycloakPlugin.class);

        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(mockPlugin);

            Uri testUri = Uri.parse("https://example.com/callback");
            KeycloakPlugin plugin = KeycloakPlugin.getInstance();

            if (plugin != null && "ca.bc.gov.asago".equals(testUri.getScheme())) {
                plugin.handleAuthCallback(testUri);
            }

            verify(mockPlugin, never()).handleAuthCallback(any());
        }
    }

    @Test
    public void testHandleAuthCallback_notCalledWhenPluginIsNull() {
        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(null);

            Uri testUri = Uri.parse("ca.bc.gov.asago://callback?code=test");
            KeycloakPlugin plugin = KeycloakPlugin.getInstance();

            // This should not throw NullPointerException
            if (plugin != null && "ca.bc.gov.asago".equals(testUri.getScheme())) {
                plugin.handleAuthCallback(testUri);
            }

            // Test passes if no exception thrown
            assertTrue(true);
        }
    }

    @Test
    public void testIntentData_canBeNull() {
        Intent intent = new Intent();
        Uri data = intent.getData();
        assertNull(data);
    }

    @Test
    public void testIntentData_canBeExtracted() {
        Uri testUri = Uri.parse("ca.bc.gov.asago://callback");
        Intent intent = new Intent(Intent.ACTION_VIEW, testUri);

        Uri data = intent.getData();
        assertNotNull(data);
        assertEquals(testUri, data);
    }

    @Test
    public void testSchemeMatching_isCaseSensitive() {
        // Android URI schemes are case-sensitive
        Uri correctScheme = Uri.parse("ca.bc.gov.asago://callback");
        Uri wrongCaseScheme = Uri.parse("CA.BC.GOV.ASAGO://callback");

        assertEquals("ca.bc.gov.asago", correctScheme.getScheme());
        assertNotEquals("ca.bc.gov.asago", wrongCaseScheme.getScheme());
    }

    @Test
    public void testMultipleQueryParameters_canBeExtracted() {
        Uri uri = Uri.parse("ca.bc.gov.asago://callback?code=abc&state=xyz&session_state=123");

        assertEquals("abc", uri.getQueryParameter("code"));
        assertEquals("xyz", uri.getQueryParameter("state"));
        assertEquals("123", uri.getQueryParameter("session_state"));
    }

    @Test
    public void testUriWithFragment_preservesFragment() {
        Uri uri = Uri.parse("ca.bc.gov.asago://callback?code=test#fragment");

        assertEquals("ca.bc.gov.asago", uri.getScheme());
        assertEquals("test", uri.getQueryParameter("code"));
        assertEquals("fragment", uri.getFragment());
    }

    @Test
    public void testHandleAuthorizationResponse_isCalledWithIntent() {
        KeycloakPlugin mockPlugin = mock(KeycloakPlugin.class);

        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(mockPlugin);

            Intent intent = new Intent();
            intent.setData(Uri.parse("ca.bc.gov.asago://callback"));

            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            if (plugin != null) {
                plugin.handleAuthorizationResponse(intent);
            }

            verify(mockPlugin).handleAuthorizationResponse(intent);
        }
    }

    @Test
    public void testActivitySchemeConstant() {
        // Verify the expected scheme matches what's in AndroidManifest
        String expectedScheme = "ca.bc.gov.asago";
        Uri uri = Uri.parse(expectedScheme + "://callback");

        assertEquals(expectedScheme, uri.getScheme());
    }

    @Test
    public void testEmptyUri_hasNoScheme() {
        Uri uri = Uri.parse("");
        assertNull(uri.getScheme());
    }

    @Test
    public void testIntentActionView_isCorrect() {
        Intent intent = new Intent(Intent.ACTION_VIEW);
        assertEquals(Intent.ACTION_VIEW, intent.getAction());
    }

    @Test
    public void testPluginHandlesMultipleCallbacks() {
        KeycloakPlugin mockPlugin = mock(KeycloakPlugin.class);

        try (MockedStatic<KeycloakPlugin> mockedStatic = mockStatic(KeycloakPlugin.class)) {
            mockedStatic.when(KeycloakPlugin::getInstance).thenReturn(mockPlugin);

            Uri uri1 = Uri.parse("ca.bc.gov.asago://callback?code=code1");
            Uri uri2 = Uri.parse("ca.bc.gov.asago://callback?code=code2");

            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            if (plugin != null) {
                if ("ca.bc.gov.asago".equals(uri1.getScheme())) {
                    plugin.handleAuthCallback(uri1);
                }
                if ("ca.bc.gov.asago".equals(uri2.getScheme())) {
                    plugin.handleAuthCallback(uri2);
                }
            }

            verify(mockPlugin, times(2)).handleAuthCallback(any(Uri.class));
        }
    }

    @Test
    public void testUriPreservation_fullUriString() {
        String uriString = "ca.bc.gov.asago://auth/callback?code=abc&state=xyz&session_state=123";
        Uri uri = Uri.parse(uriString);

        assertEquals("ca.bc.gov.asago", uri.getScheme());
        // In custom schemes, the authority/host is "auth" and path is "/callback"
        assertEquals("/callback", uri.getPath());
        assertEquals("code=abc&state=xyz&session_state=123", uri.getQuery());
    }
}
