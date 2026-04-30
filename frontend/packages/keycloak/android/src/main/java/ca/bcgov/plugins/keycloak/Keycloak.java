package ca.bcgov.plugins.keycloak;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import androidx.annotation.Nullable;
import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import net.openid.appauth.*;
import org.json.JSONException;

public class Keycloak {
    private static final String TAG = "Keycloak";
    private static final long TOKEN_REFRESH_CHECK_INTERVAL = 60000; // Check every 60 seconds
    private static final long TOKEN_EXPIRY_BUFFER = 60000; // Refresh 1 minute before expiry
    private static final String PREFS_NAME = "KeycloakAuthState";
    private static final String KEY_AUTH_STATE = "auth_state";

    private Context context;
    private AuthorizationService authService;
    private PluginCall currentCall;
    private AuthorizationRequest currentAuthRequest;
    private AuthState authState;
    private Handler refreshHandler;
    private Runnable refreshCheckRunnable;
    private TokenRefreshCallback tokenRefreshCallback;

    public interface TokenRefreshCallback {
        void onTokenRefreshed(JSObject tokens);
    }

    public Keycloak(Context context) {
        this.context = context;
        this.authService = new AuthorizationService(context);
        this.authState = restoreAuthState();
        this.refreshHandler = new Handler(Looper.getMainLooper());
        setupAutomaticRefresh();
    }

    private AuthState restoreAuthState() {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String stateJson = prefs.getString(KEY_AUTH_STATE, null);

        if (stateJson != null) {
            try {
                AuthState restored = AuthState.jsonDeserialize(stateJson);
                Log.d(TAG, "Restored auth state from storage");
                return restored;
            } catch (JSONException e) {
                Log.e(TAG, "Failed to restore auth state", e);
            }
        }

        Log.d(TAG, "No saved auth state, creating new");
        return new AuthState();
    }

    private void persistAuthState() {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        prefs.edit()
            .putString(KEY_AUTH_STATE, authState.jsonSerializeString())
            .apply();
        Log.d(TAG, "Auth state persisted");
    }

    public void setTokenRefreshCallback(TokenRefreshCallback callback) {
        this.tokenRefreshCallback = callback;
    }

    private void setupAutomaticRefresh() {
        refreshCheckRunnable = new Runnable() {
            @Override
            public void run() {
                checkAndRefreshToken();
                // Schedule next check
                refreshHandler.postDelayed(this, TOKEN_REFRESH_CHECK_INTERVAL);
            }
        };
        // Start checking after initial delay
        refreshHandler.postDelayed(refreshCheckRunnable, TOKEN_REFRESH_CHECK_INTERVAL);
    }

    private void checkAndRefreshToken() {
        if (!authState.isAuthorized()) {
            return;
        }

        Long expiresAt = authState.getAccessTokenExpirationTime();
        if (expiresAt == null) {
            return;
        }

        long currentTime = System.currentTimeMillis();
        long timeUntilExpiry = expiresAt - currentTime;

        // Refresh if token expires within the buffer time (1 minute)
        if (timeUntilExpiry < TOKEN_EXPIRY_BUFFER) {
            Log.d(TAG, "Token expiring soon, refreshing automatically");
            performTokenRefresh();
        }
    }

    private void performTokenRefresh() {
        authState.performActionWithFreshTokens(authService, new AuthState.AuthStateAction() {
            @Override
            public void execute(@Nullable String accessToken, @Nullable String idToken,
                              @Nullable AuthorizationException exception) {
                if (exception != null) {
                    Log.e(TAG, "Automatic token refresh failed: " + exception.getMessage());
                    return;
                }

                Log.d(TAG, "Token automatically refreshed");

                // Persist the updated auth state
                persistAuthState();

                // Notify JavaScript about the refresh
                if (tokenRefreshCallback != null) {
                    JSObject tokens = new JSObject();
                    tokens.put("accessToken", accessToken);
                    tokens.put("idToken", idToken);
                    tokens.put("refreshToken", authState.getRefreshToken());
                    tokens.put("tokenType", "Bearer");
                    if (authState.getAccessTokenExpirationTime() != null) {
                        tokens.put("expiresAt", authState.getAccessTokenExpirationTime());
                    }
                    tokenRefreshCallback.onTokenRefreshed(tokens);
                }
            }
        });
    }

    /**
     * Set the current plugin call for async completion
     */
    public void setCurrentCall(PluginCall call) {
        this.currentCall = call;
    }

    /**
     * Set the current authorization request
     */
    public void setAuthorizationRequest(AuthorizationRequest request) {
        this.currentAuthRequest = request;
    }


    /**
     * Handle the authorization response from intent
     */
    public void handleAuthorizationResponse(Intent intent) {
        Log.d(TAG, "handleAuthorizationResponse called");
        
        Log.d(TAG, "=== Authorization State Check ===");
        Log.d(TAG, "Current call present: " + (currentCall != null));
        Log.d(TAG, "Current auth request present: " + (currentAuthRequest != null));
        if (currentAuthRequest != null) {
            Log.d(TAG, "Current auth request state: " + currentAuthRequest.state);
        }
        
        if (currentCall == null) {
            Log.w(TAG, "No current call to complete - this might be due to app restart");
            // Don't return immediately, still try to process the response
            // in case we need to handle it differently for app restarts
        }

        if (currentAuthRequest == null) {
            Log.w(TAG, "No current authorization request - this might be due to app restart");
            // Don't return immediately, still try to extract response data
        }

        try {
            Log.d(TAG, "=== Intent Response Extraction ===");
            AuthorizationResponse authResponse = AuthorizationResponse.fromIntent(intent);
            AuthorizationException authException = AuthorizationException.fromIntent(intent);

            Log.d(TAG, "Auth response: " + (authResponse != null ? "present" : "null"));
            if (authResponse != null) {
                Log.d(TAG, "Auth response state: " + authResponse.state);
                Log.d(TAG, "Auth response authorization code: " + (authResponse.authorizationCode != null ? "present" : "null"));
            }
            Log.d(TAG, "Auth exception: " + (authException != null ? authException.getMessage() : "null"));

            if (authException != null) {
                Log.e(TAG, "Authorization failed: " + authException.getMessage());
                if (currentCall != null) {
                    JSObject errorResponse = new JSObject();
                    errorResponse.put("isAuthenticated", false);
                    errorResponse.put("error", authException.error);
                    errorResponse.put("errorDescription", authException.getLocalizedMessage());
                    currentCall.resolve(errorResponse);
                    currentCall = null;
                }
                return;
            }

            if (authResponse == null) {
                Log.e(TAG, "No authorization response received from intent");
                if (currentCall != null) {
                    JSObject errorResponse = new JSObject();
                    errorResponse.put("isAuthenticated", false);
                    errorResponse.put("error", "no_response");
                    errorResponse.put("errorDescription", "No authorization response received");
                    currentCall.resolve(errorResponse);
                    currentCall = null;
                }
                return;
            }

            // Update auth state
            authState.update(authResponse, authException);

            Log.d(TAG, "Authorization successful, exchanging code for tokens");

            // Exchange authorization code for tokens
            TokenRequest tokenRequest = authResponse.createTokenExchangeRequest();
            
            authService.performTokenRequest(tokenRequest, new AuthorizationService.TokenResponseCallback() {
                @Override
                public void onTokenRequestCompleted(@Nullable TokenResponse tokenResponse, 
                                                  @Nullable AuthorizationException exception) {
                    if (exception != null) {
                        Log.e(TAG, "Token exchange failed: " + exception.getMessage());
                        JSObject errorResponse = new JSObject();
                        errorResponse.put("isAuthenticated", false);
                        errorResponse.put("error", exception.error);
                        errorResponse.put("errorDescription", exception.getLocalizedMessage());
                        if (currentCall != null) {
                            currentCall.resolve(errorResponse);
                            currentCall = null;
                        }
                        return;
                    }

                    if (tokenResponse == null) {
                        Log.e(TAG, "Token response is null");
                        JSObject errorResponse = new JSObject();
                        errorResponse.put("isAuthenticated", false);
                        errorResponse.put("error", "no_token_response");
                        errorResponse.put("errorDescription", "No token response received");
                        if (currentCall != null) {
                            currentCall.resolve(errorResponse);
                            currentCall = null;
                        }
                        return;
                    }

                    // Update auth state with tokens
                    authState.update(tokenResponse, exception);

                    // Persist auth state for future app restarts
                    persistAuthState();

                    Log.d(TAG, "Token exchange successful");
                    JSObject successResponse = new JSObject();
                    successResponse.put("isAuthenticated", true);
                    successResponse.put("accessToken", tokenResponse.accessToken);
                    successResponse.put("refreshToken", tokenResponse.refreshToken);
                    successResponse.put("idToken", tokenResponse.idToken);
                    successResponse.put("tokenType", tokenResponse.tokenType);
                    if (tokenResponse.accessTokenExpirationTime != null) {
                        successResponse.put("expiresAt", tokenResponse.accessTokenExpirationTime);
                    }

                    if (currentCall != null) {
                        currentCall.resolve(successResponse);
                        currentCall = null;
                    }
                }
            });

        } catch (Exception e) {
            Log.e(TAG, "Error handling authorization response", e);
            JSObject errorResponse = new JSObject();
            errorResponse.put("isAuthenticated", false);
            errorResponse.put("error", "response_error");
            errorResponse.put("errorDescription", e.getMessage());
            currentCall.resolve(errorResponse);
            currentCall = null;
        }
    }

    /**
     * Handle the redirect URI callback (for compatibility)
     */
    public void handleAuthCallback(Uri callbackUri) {
        Log.d(TAG, "handleAuthCallback called with URI: " + callbackUri.toString());
        
        // Create intent from URI for proper AppAuth handling
        Intent intent = new Intent();
        intent.setData(callbackUri);
        handleAuthorizationResponse(intent);
    }

    /**
     * Clean up resources
     */
    public void dispose() {
        // Stop automatic refresh checking
        if (refreshHandler != null && refreshCheckRunnable != null) {
            refreshHandler.removeCallbacks(refreshCheckRunnable);
            Log.d(TAG, "Stopped automatic token refresh");
        }

        if (authService != null) {
            authService.dispose();
        }
    }
}
