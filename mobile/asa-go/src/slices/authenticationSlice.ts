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
    resetAuthentication(state: AuthState) {
      state.isAuthenticated = false;
      state.idToken = undefined;
      state.token = undefined;
    },
  },
});

export const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
  resetAuthentication,
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

  const customRedirectUri = "ca.bc.gov.asago://auth";
  Keycloak.authenticate({
    authorizationBaseUrl: authUrl,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
    redirectUrl: customRedirectUri,
    accessTokenEndpoint: tokenUrl,
  })
    .then((result) => {
      console.log("Auth result:", result);
      if (result.isAuthenticated) {
        dispatch(
          authenticateFinished({
            isAuthenticated: result.isAuthenticated,
            token: result.accessToken,
            idToken: result.idToken,
          })
        );
      } else {
        dispatch(authenticateError(JSON.stringify(result.error)));
      }
    })
    .catch((error) => {
      dispatch(authenticateError(JSON.stringify(error)));
    });

  // Handle token refresh callback function
  const handleTokenRefresh = (tokenResponse: {
    accessToken: string;
    idToken: string;
    refreshToken?: string;
    tokenType?: string;
    expiresIn?: number;
    scope?: string;
  }) => {
    if (tokenResponse.refreshToken) {
      dispatch(
        refreshTokenFinished({
          tokenRefreshed: true,
          token: tokenResponse.accessToken,
          idToken: tokenResponse.idToken,
        })
      );
    }
  };

  // Set up event listener for token refresh events (works for both web and iOS)
  Keycloak.addListener("tokenRefresh", handleTokenRefresh);
};
