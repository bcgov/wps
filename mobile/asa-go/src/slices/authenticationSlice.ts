import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { jwtDecode } from "jwt-decode";
import { isUndefined } from "lodash";
import { AppThunk } from "@/store";
import { Capacitor } from "@capacitor/core";
import { kcInitOptions } from "@/utils/webAuthBridge";
import { getKeycloakInstance } from "@/utils/keycloak";

export interface AuthState {
  authenticating: boolean;
  isAuthenticated: boolean;
  tokenRefreshed: boolean;
  token: string | undefined;
  idToken: string | undefined;
  idir: string | undefined;
  email: string | undefined;
  roles: string[];
  error: string | null;
}

export const initialState: AuthState = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  idToken: undefined,
  idir: undefined,
  email: undefined,
  roles: [],
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
      const userDetails = decodeUserDetails(action.payload.token);
      state.idir = userDetails?.idir;
      state.email = userDetails?.email;
    },
    authenticateError(state: AuthState, action: PayloadAction<string>) {
      state.authenticating = false;
      state.isAuthenticated = false;
      state.error = action.payload;
      state.roles = [];
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
      const userDetails = decodeUserDetails(action.payload.token);
      state.idir = userDetails?.idir;
      state.email = userDetails?.email;
    },
    signoutFinished(state: AuthState) {
      state.authenticating = false;
      state.isAuthenticated = false;
      state.token = undefined;
      state.idToken = undefined;
      state.roles = [];
    },
    signoutError(state: AuthState, action: PayloadAction<string>) {
      state.authenticating = false;
      state.isAuthenticated = false;
      state.error = action.payload;
      state.token = undefined;
      state.idToken = undefined;
      state.roles = [];
    },
  },
});

export const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
  signoutFinished,
  signoutError,
} = authSlice.actions;

export default authSlice.reducer;

export const decodeUserDetails = (token: string | undefined) => {
  if (isUndefined(token)) {
    return undefined;
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const decodedToken: any = jwtDecode(token);
  try {
    return { idir: decodedToken.idir_username, email: decodedToken.email };
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (e) {
    // No idir username
    return undefined;
  }
};

export const testAuthenticate =
  (isAuthenticated: boolean, token: string, idToken: string): AppThunk =>
  (dispatch) => {
    dispatch(authenticateFinished({ isAuthenticated, token, idToken }));
  };

export const authenticate = (): AppThunk => async (dispatch) => {
  dispatch(authenticateStart());
  // Platform detection: use capacitorLogin for mobile, keycloak.init for web
  const isNative = Capacitor.isNativePlatform();

  if (isNative) {
    // await capacitorLogin(keycloak);
    // dispatch(
    //   authenticateFinished({
    //     isAuthenticated: !!keycloak.token,
    //     token: keycloak.token,
    //     idToken: keycloak.idToken,
    //   })
    // );
  } else {
    // Use Keycloak JS for web
    dispatch(authenticateStart());

    const keycloak = getKeycloakInstance();
    keycloak
      .init(kcInitOptions)
      .then((isAuthenticated) => {
        console.log("Keycloak init:", {
          isAuthenticated,
          token: keycloak.token,
          idToken: keycloak.idToken,
        });
        dispatch(
          authenticateFinished({
            isAuthenticated,
            token: keycloak?.token,
            idToken: keycloak?.idToken,
          })
        );
      })
      .catch((err) => {
        console.log(err);
        dispatch(authenticateError("Failed to authenticate."));
      });

    keycloak.onTokenExpired = () => {
      keycloak
        ?.updateToken(0)
        .then((tokenRefreshed) => {
          dispatch(
            refreshTokenFinished({
              tokenRefreshed,
              token: keycloak?.token,
              idToken: keycloak?.idToken,
            })
          );
        })
        .catch(() => {
          // Restart the authentication flow
          dispatch(authenticate());
        });
    };
  }
};
