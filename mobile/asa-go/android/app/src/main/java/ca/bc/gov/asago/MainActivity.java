package ca.bc.gov.asago;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import com.getcapacitor.BridgeActivity;
import net.openid.appauth.AuthorizationResponse;
import net.openid.appauth.AuthorizationException;

import ca.bcgov.plugins.keycloak.KeycloakPlugin;

public class MainActivity extends BridgeActivity {
    private static final String TAG = "MainActivity";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(KeycloakPlugin.class);
        super.onCreate(savedInstanceState);

        // Check if this activity was started with an intent containing auth data
        handleAuthIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleAuthIntent(intent);
    }

    private void handleAuthIntent(Intent intent) {
        if (intent == null) {
            return;
        }

        Log.d(TAG, "=== Handling Intent ===");
        Log.d(TAG, "Intent action: " + intent.getAction());
        Log.d(TAG, "Intent data: " + intent.getData());

        // First, check if this intent contains AppAuth response data in extras
        // This is how AppAuth's RedirectUriReceiverActivity forwards the response
        AuthorizationResponse authResponse = AuthorizationResponse.fromIntent(intent);
        AuthorizationException authException = AuthorizationException.fromIntent(intent);

        if (authResponse != null || authException != null) {
            Log.d(TAG, "Found AppAuth response in intent extras");
            Log.d(TAG, "Auth response present: " + (authResponse != null));
            Log.d(TAG, "Auth exception present: " + (authException != null));

            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            if (plugin != null) {
                // Forward the full intent with AppAuth extras to the plugin
                plugin.handleAuthorizationResponse(intent);
                // Clear the intent to prevent re-processing
                setIntent(new Intent());
            } else {
                Log.e(TAG, "KeycloakPlugin instance is null");
            }
            return;
        }

        // Fallback: check for custom scheme redirect in URI data
        // This handles the case where the redirect comes directly without RedirectUriReceiverActivity
        Uri data = intent.getData();
        if (data != null && "ca.bc.gov.asago".equals(data.getScheme())) {
            Log.d(TAG, "Found custom scheme redirect in URI: " + data.toString());
            KeycloakPlugin plugin = KeycloakPlugin.getInstance();
            if (plugin != null) {
                plugin.handleAuthCallback(data);
                // Clear the intent to prevent re-processing
                setIntent(new Intent());
            } else {
                Log.e(TAG, "KeycloakPlugin instance is null");
            }
        }
    }
}
