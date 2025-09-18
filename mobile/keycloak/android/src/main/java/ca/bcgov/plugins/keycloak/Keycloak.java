package ca.bcgov.plugins.keycloak;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import androidx.annotation.Nullable;
import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import net.openid.appauth.*;

public class Keycloak {
    private static final String TAG = "Keycloak";
    
    private Context context;
    private AuthorizationService authService;
    private PluginCall currentCall;
    private AuthorizationRequest currentAuthRequest;
    private AuthState authState;

    public Keycloak(Context context) {
        this.context = context;
        this.authService = new AuthorizationService(context);
        this.authState = new AuthState();
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
     * Get the current authorization request
     */
    public AuthorizationRequest getPendingAuthRequest() {
        return currentAuthRequest;
    }

    /**
     * Get current auth state
     */
    public AuthState getAuthState() {
        return authState;
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
     * Refresh access token if needed
     */
    public java.util.concurrent.CompletableFuture<JSObject> refreshTokenIfNeeded() {
        java.util.concurrent.CompletableFuture<JSObject> future = new java.util.concurrent.CompletableFuture<>();
        
        if (!authState.isAuthorized()) {
            JSObject errorResponse = new JSObject();
            errorResponse.put("error", "not_authenticated");
            errorResponse.put("errorDescription", "User is not authenticated");
            future.complete(errorResponse);
            return future;
        }

        authState.performActionWithFreshTokens(authService, new AuthState.AuthStateAction() {
            @Override
            public void execute(@Nullable String accessToken, @Nullable String idToken, 
                              @Nullable AuthorizationException exception) {
                if (exception != null) {
                    JSObject errorResponse = new JSObject();
                    errorResponse.put("error", exception.error);
                    errorResponse.put("errorDescription", exception.getLocalizedMessage());
                    future.complete(errorResponse);
                    return;
                }
                
                JSObject successResponse = new JSObject();
                successResponse.put("accessToken", accessToken);
                successResponse.put("idToken", idToken);
                future.complete(successResponse);
            }
        });

        return future;
    }

    /**
     * Clean up resources
     */
    public void dispose() {
        if (authService != null) {
            authService.dispose();
        }
    }
}
