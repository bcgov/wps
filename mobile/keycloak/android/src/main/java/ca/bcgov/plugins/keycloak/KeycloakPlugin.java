package ca.bcgov.plugins.keycloak;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import android.Manifest;
import android.util.Log;
import java.util.concurrent.CompletableFuture;

@CapacitorPlugin(
    name = "Keycloak",
    permissions = {
        @Permission(strings = {Manifest.permission.INTERNET}, alias = "internet")
    }
)
public class KeycloakPlugin extends Plugin {
    private static final String TAG = "KeycloakPlugin";
    private Keycloak implementation;

    @Override
    public void load() {
        super.load();
        implementation = new Keycloak(getContext());
    }

    @PluginMethod
    public void authenticate(PluginCall call) {
        JSObject options = call.getData();
        
        // Validate required parameters
        String clientId = options.getString("clientId");
        String authorizationBaseUrl = options.getString("authorizationBaseUrl");
        String redirectUrl = options.getString("redirectUrl");
        String accessTokenEndpoint = options.getString("accessTokenEndpoint");

        if (clientId == null || clientId.isEmpty()) {
            call.reject("clientId is required");
            return;
        }
        if (authorizationBaseUrl == null || authorizationBaseUrl.isEmpty()) {
            call.reject("authorizationBaseUrl is required");
            return;
        }
        if (redirectUrl == null || redirectUrl.isEmpty()) {
            call.reject("redirectUrl is required");
            return;
        }
        if (accessTokenEndpoint == null || accessTokenEndpoint.isEmpty()) {
            call.reject("accessTokenEndpoint is required");
            return;
        }

        CompletableFuture<JSObject> authFuture = implementation.authenticate(options);
        
        authFuture.thenAccept(result -> {
            Log.d(TAG, "Authentication completed");
            call.resolve(result);
        }).exceptionally(throwable -> {
            Log.e(TAG, "Authentication failed", throwable);
            call.reject("Authentication failed: " + throwable.getMessage());
            return null;
        });
    }

    @PluginMethod
    public void addListener(PluginCall call) {
        // This method is automatically handled by Capacitor for event listeners
        // The actual listener registration happens on the JavaScript side
        // We just need to acknowledge the call
        call.resolve();
    }
}
