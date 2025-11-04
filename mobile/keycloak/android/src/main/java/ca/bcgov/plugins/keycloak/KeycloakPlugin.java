package ca.bcgov.plugins.keycloak;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import java.util.List;
import androidx.browser.customtabs.CustomTabsIntent;
import net.openid.appauth.*;
import net.openid.appauth.browser.AnyBrowserMatcher;

@CapacitorPlugin(
    name = "Keycloak",
    permissions = {
        @Permission(strings = {Manifest.permission.INTERNET}, alias = "internet")
    }
)
public class KeycloakPlugin extends Plugin {
    private static final String TAG = "KeycloakPlugin";
    private Keycloak implementation;

    private static KeycloakPlugin instance;

    @Override
    public void load() {
        super.load();
        implementation = new Keycloak(getContext());
        instance = this;
        Log.d(TAG, "KeycloakPlugin loaded and initialized");
    }

    public static KeycloakPlugin getInstance() {
        return instance;
    }

    public void handleAuthCallback(Uri callbackUri) {
        Log.d(TAG, "handleAuthCallback called with URI: " + callbackUri.toString());

        // Create intent from URI for proper AppAuth handling
        Intent intent = new Intent();
        intent.setData(callbackUri);
        implementation.handleAuthorizationResponse(intent);
    }

    public void handleAuthorizationResponse(Intent intent) {
        Log.d(TAG, "handleAuthorizationResponse called from MainActivity");
        implementation.handleAuthorizationResponse(intent);
    }

    @Override
    protected void handleOnResume() {
        super.handleOnResume();
        Log.d(TAG, "App resumed - checking for authorization response");
        
        // Check if this is a completion from AppAuth performAuthorizationRequest
        Intent intent = getActivity().getIntent();
        if (intent != null) {
            Log.d(TAG, "=== Intent Analysis on Resume ===");
            Log.d(TAG, "Intent action: " + intent.getAction());
            Log.d(TAG, "Intent data: " + intent.getData());
            Log.d(TAG, "Intent categories: " + intent.getCategories());
            Log.d(TAG, "Intent extras keys: " + (intent.getExtras() != null ? intent.getExtras().keySet() : "null"));
            
            // Try to extract AppAuth response from the completion intent
            AuthorizationResponse authResponse = AuthorizationResponse.fromIntent(intent);
            AuthorizationException authException = AuthorizationException.fromIntent(intent);
            
            if (authResponse != null || authException != null) {
                Log.d(TAG, "Found AppAuth response data in completion intent");
                Log.d(TAG, "Auth response present: " + (authResponse != null));
                Log.d(TAG, "Auth exception present: " + (authException != null));
                implementation.handleAuthorizationResponse(intent);
                // Clear the intent to prevent re-processing
                getActivity().setIntent(new Intent());
                return;
            }
            
            // Also check for custom scheme redirect (fallback)
            Uri uri = intent.getData();
            if (uri != null) {
                Log.d(TAG, "=== URI Analysis ===");
                Log.d(TAG, "URI scheme: " + uri.getScheme());
                Log.d(TAG, "URI host: " + uri.getHost());
                Log.d(TAG, "URI path: " + uri.getPath());
                Log.d(TAG, "URI query: " + uri.getQuery());

                Log.d(TAG, "Checking bundle extras");
                Bundle extras = intent.getExtras();
                if (extras != null) {
                    for (String key : extras.keySet()) {
                        Log.d(TAG, "Intent extra: " + key + " = " + extras.get(key));
                    }
                }


                if ("ca.bc.gov.asago".equals(uri.getScheme()) && "auth".equals(uri.getHost())) {
                    Log.d(TAG, "Handling custom scheme authorization response on resume");
                    implementation.handleAuthorizationResponse(intent);
                    // Clear the intent to prevent re-processing
                    getActivity().setIntent(new Intent());
                    return;
                }
            }
            
            Log.d(TAG, "No authorization response found on resume");
            Log.d(TAG, "Calling handleAuthorizationResponse anyway to check state");
            implementation.handleAuthorizationResponse(intent);
        } else {
            Log.d(TAG, "No intent found on resume");
        }
    }

    @Override
    protected void handleOnNewIntent(Intent intent) {
        super.handleOnNewIntent(intent);
        Log.d(TAG, "New intent received");
        
        if (intent != null) {
            Log.d(TAG, "=== New Intent Analysis ===");
            Log.d(TAG, "Intent action: " + intent.getAction());
            Log.d(TAG, "Intent data: " + intent.getData());
            Log.d(TAG, "Intent categories: " + intent.getCategories());
            Log.d(TAG, "Intent extras keys: " + (intent.getExtras() != null ? intent.getExtras().keySet() : "null"));
            
            // Try to extract AppAuth response from the new intent
            AuthorizationResponse authResponse = AuthorizationResponse.fromIntent(intent);
            AuthorizationException authException = AuthorizationException.fromIntent(intent);
            
            if (authResponse != null || authException != null) {
                Log.d(TAG, "Found AppAuth response data in new intent");
                Log.d(TAG, "Auth response present: " + (authResponse != null));
                Log.d(TAG, "Auth exception present: " + (authException != null));
                implementation.handleAuthorizationResponse(intent);
                return;
            }
            
            // Also check for custom scheme redirect (fallback)
            Uri uri = intent.getData();
            if (uri != null) {
                Log.d(TAG, "=== New Intent URI Analysis ===");
                Log.d(TAG, "URI scheme: " + uri.getScheme());
                Log.d(TAG, "URI host: " + uri.getHost());
                Log.d(TAG, "URI path: " + uri.getPath());
                Log.d(TAG, "URI query: " + uri.getQuery());
                
                if ("ca.bc.gov.asago".equals(uri.getScheme()) && "auth".equals(uri.getHost())) {
                    Log.d(TAG, "Handling custom scheme authorization response on new intent");
                    implementation.handleAuthorizationResponse(intent);
                    return;
                }
            }
            
            Log.d(TAG, "No authorization response found in new intent");
            Log.d(TAG, "Calling handleAuthorizationResponse anyway to check state");
            implementation.handleAuthorizationResponse(intent);
        } else {
            Log.d(TAG, "New intent is null");
        }
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

        try {
            // Create service configuration
            AuthorizationServiceConfiguration serviceConfig = new AuthorizationServiceConfiguration(
                    Uri.parse(authorizationBaseUrl),
                    Uri.parse(accessTokenEndpoint)
            );

            // Build authorization request
            AuthorizationRequest.Builder authRequestBuilder = new AuthorizationRequest.Builder(
                    serviceConfig,
                    clientId,
                    ResponseTypeValues.CODE,
                    Uri.parse(redirectUrl)
            );

            authRequestBuilder
                    .setScope("openid profile")
                    .setCodeVerifier(CodeVerifierUtil.generateRandomCodeVerifier());

            AuthorizationRequest authRequest = authRequestBuilder.build();

            Log.d(TAG, "=== OAuth Configuration Debug ===");
            Log.d(TAG, "Client ID: " + clientId);
            Log.d(TAG, "Authorization URL: " + authorizationBaseUrl);
            Log.d(TAG, "Token Endpoint: " + accessTokenEndpoint);
            Log.d(TAG, "Redirect URL: " + redirectUrl);
            Log.d(TAG, "Scope: openid profile");

            // Store the call and request for later completion
            implementation.setCurrentCall(call);
            implementation.setAuthorizationRequest(authRequest);

            // Log the final authorization URL for debugging
            Uri authUri = authRequest.toUri();
            Log.d(TAG, "=== Final Authorization URL ===");
            Log.d(TAG, authUri.toString());
            Log.d(TAG, "=== URL Components ===");
            Log.d(TAG, "Scheme: " + authUri.getScheme());
            Log.d(TAG, "Host: " + authUri.getHost());
            Log.d(TAG, "Path: " + authUri.getPath());
            Log.d(TAG, "Query: " + authUri.getQuery());

            // Create authorization service
            AppAuthConfiguration.Builder appAuthConfigBuilder = new AppAuthConfiguration.Builder();
            // Force to use any available browser, don't let the system intercept
            appAuthConfigBuilder.setBrowserMatcher(AnyBrowserMatcher.INSTANCE);
            
            AuthorizationService authService = new AuthorizationService(getContext(), appAuthConfigBuilder.build());
            
            // Debug: Check what browsers are available
            Intent testIntent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com"));
            testIntent.addCategory(Intent.CATEGORY_BROWSABLE);
            PackageManager packageManager = getContext().getPackageManager();
            List<ResolveInfo> activities = packageManager.queryIntentActivities(testIntent, PackageManager.MATCH_DEFAULT_ONLY);

            Log.d(TAG, "=== Available Browsers Debug ===");
            Log.d(TAG, "Found " + activities.size() + " browser activities:");
            for (ResolveInfo activity : activities) {
                Log.d(TAG, "Browser: " + activity.activityInfo.packageName + " / " + activity.activityInfo.name);
            }

            // Create CustomTabsIntent for proper browser handling
            CustomTabsIntent.Builder customTabsBuilder = authService.createCustomTabsIntentBuilder(authRequest.toUri());
            
            // Force external browser handling to prevent app interception
            customTabsBuilder.setShowTitle(true);
            customTabsBuilder.setUrlBarHidingEnabled(false);
            
            CustomTabsIntent customTabsIntent = customTabsBuilder.build();
            
            // Debug: Check what the CustomTabsIntent is targeting
            Log.d(TAG, "CustomTabs intent package: " + customTabsIntent.intent.getPackage());
            Log.d(TAG, "CustomTabs intent action: " + customTabsIntent.intent.getAction());
            Log.d(TAG, "CustomTabs intent data: " + customTabsIntent.intent.getData());
            
            // Ensure the intent doesn't get intercepted by our own app
            customTabsIntent.intent.setPackage(null); // Don't restrict to a specific browser package
            customTabsIntent.intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            customTabsIntent.intent.addFlags(Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS);
            
            Log.d(TAG, "CustomTabs intent created successfully with external browser forcing");

            Log.d(TAG, "=== Launching Browser ===");
            Log.d(TAG, "About to call performAuthorizationRequest");
            Log.d(TAG, "Auth request state: " + authRequest.state);

            // Create PendingIntent for RedirectUriReceiverActivity
            // This activity will receive the OAuth callback and forward to MainActivity
            Intent completionIntent = new Intent(getContext(), getActivity().getClass());
            completionIntent.setAction(Intent.ACTION_VIEW);
            completionIntent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);

            android.app.PendingIntent completionPendingIntent = android.app.PendingIntent.getActivity(
                getContext(),
                authRequest.hashCode(),
                completionIntent,
                android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_MUTABLE
            );

            Log.d(TAG, "Created PendingIntent for completion: " + completionPendingIntent);
            Log.d(TAG, "RedirectUriReceiverActivity will forward to MainActivity via manifest meta-data");

            try {
                // Use AppAuth's performAuthorizationRequest
                // The RedirectUriReceiverActivity will receive the callback and forward to our completion intent
                authService.performAuthorizationRequest(
                    authRequest,
                    completionPendingIntent,
                    null,  // canceledIntent - use default behavior
                    customTabsIntent
                );
                Log.d(TAG, "performAuthorizationRequest completed successfully");
            } catch (Exception authException) {
                Log.e(TAG, "Error in performAuthorizationRequest: " + authException.getMessage(), authException);
                throw authException;
            }
            
            Log.d(TAG, "AppAuth authorization request initiated - browser should have launched");

        } catch (Exception e) {
            Log.e(TAG, "Error initiating authentication", e);
            call.reject("Authentication failed: " + e.getMessage());
        }
    }

    @PluginMethod
    public void addListener(PluginCall call) {
        // This method is automatically handled by Capacitor for event listeners
        // The actual listener registration happens on the JavaScript side
        // We just need to acknowledge the call
        call.resolve();
    }
}
