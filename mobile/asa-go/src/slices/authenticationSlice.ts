import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { AppThunk } from "@/store";
import { Keycloak } from "../../../keycloak/src";

export interface AuthState {
  authenticating: boolean;
  isAuthenticated: boolean;
  tokenRefreshed: boolean;
  token: string | undefined;
  idToken: string | undefined;
  error: string | null;
}

export const initialState: AuthState = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  idToken: undefined,
  error: null,
};

const authSlice = createSlice({
  name: "authentication",
  initialState,
  reducers: {
    authenticateStart(state: AuthState) {
      state.authenticating = true;
    },
    authenticateFinished(
      state: AuthState,
      action: PayloadAction<{
        isAuthenticated: boolean;
        token: string | undefined;
        idToken: string | undefined;
      }>
    ) {
      state.authenticating = false;
      state.isAuthenticated = action.payload.isAuthenticated;
      state.token = action.payload.token;
      state.idToken = action.payload.idToken;
    },
    authenticateError(state: AuthState, action: PayloadAction<string>) {
      state.authenticating = false;
      state.isAuthenticated = false;
      state.error = action.payload;
    },
    refreshTokenFinished(
      state: AuthState,
      action: PayloadAction<{
        tokenRefreshed: boolean;
        token: string | undefined;
        idToken: string | undefined;
      }>
    ) {
      state.token = action.payload.token;
      state.idToken = action.payload.idToken;
      state.tokenRefreshed = action.payload.tokenRefreshed;
    },
  },
});

export const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
} = authSlice.actions;

export default authSlice.reducer;

export const authenticate = (): AppThunk => (dispatch) => {
  dispatch(authenticateStart());

  const realm = import.meta.env.VITE_KEYCLOAK_REALM;
  const authUrl = `${
    import.meta.env.VITE_KEYCLOAK_AUTH_URL
  }/realms/${realm}/protocol/openid-connect/auth`;
  const tokenUrl = `${
    import.meta.env.VITE_KEYCLOAK_AUTH_URL
  }/realms/${realm}/protocol/openid-connect/token`;

  console.log("Constructed authUrl:", authUrl);
  console.log("Constructed tokenUrl:", tokenUrl);

  const customRedirectUri = "ca.bc.gov.asago://auth/callback";
  Keycloak.authenticate({
    authorizationBaseUrl: authUrl,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
    redirectUrl: customRedirectUri,
    accessTokenEndpoint: "",
  })
    .then((result) => {
      console.log("🎉 Authentication successful:", result);
      // The result contains: { redirectUrl, code, state, codeVerifier, ... }
      // You can now exchange the code for tokens in JavaScript if needed
      if (result.code) {
        console.log("Got authorization code:", result.code);
        if (result.codeVerifier) {
          console.log("Got PKCE code verifier:", result.codeVerifier);
          console.log("Use both code and codeVerifier for token exchange");
        }
        // TODO: Exchange code for tokens using your preferred HTTP library
        // For PKCE, include code_verifier in the token exchange request
      }
    })
    .catch((error) => {
      console.error("❌ Authentication failed:", error);
      console.log("Error details:", error);
    });

  // keycloak.onTokenExpired = () => {
  //   keycloak
  //     ?.updateToken(0)
  //     .then((tokenRefreshed) => {
  //       dispatch(
  //         refreshTokenFinished({
  //           tokenRefreshed,
  //           token: keycloak?.token,
  //           idToken: keycloak?.idToken,
  //         })
  //       );
  //     })
  //     .catch(() => {
  //       // Restart the authentication flow
  //       dispatch(authenticate());
  //     });
  // };
};
