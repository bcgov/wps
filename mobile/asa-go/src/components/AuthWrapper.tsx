import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Capacitor } from "@capacitor/core";
import { AppDispatch, selectAuthentication } from "@/store";
import {
  authenticateError,
  authenticateFinished,
  refreshTokenFinished,
} from "@/slices/authenticationSlice";
import { App as CapApp } from "@capacitor/app";
import { KeycloakAuthResponse } from "@/keycloak/definitions";
import { Keycloak } from "@/keycloak/auth";

interface Props {
  children: React.ReactElement;
}

const AuthWrapper = ({ children }: Props) => {
  const dispatch: AppDispatch = useDispatch();
  const [message, setMessage] = useState<string>("No message");
  const { isAuthenticated, authenticating, error } =
    useSelector(selectAuthentication);

  CapApp.addListener("appUrlOpen", (data) => {
    if (data.url?.startsWith("ca.bc.gov.asago")) {
      // Handle the auth response here
      console.log("Redirect URL received:", data.url);
      setMessage(JSON.stringify(data));
      // You might want to parse the URL and extract tokens or codes
    }
  });

  async function authenticate() {
    const realm = import.meta.env.VITE_KEYCLOAK_REALM;
    const authUrl = `${
      import.meta.env.VITE_KEYCLOAK_AUTH_URL
    }/realms/${realm}/protocol/openid-connect/auth`;
    const tokenUrl = `${
      import.meta.env.VITE_KEYCLOAK_AUTH_URL
    }/realms/${realm}/protocol/openid-connect/token`;

    const customRedirectUri = "ca.bc.gov.asago://auth/callback";
    let result: KeycloakAuthResponse | null = null;
    try {
      setInterval(() => {
        console.log("Waiting");
      }, 1000);
      result = await Keycloak.authenticate({
        authorizationBaseUrl: authUrl,
        clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
        redirectUrl: customRedirectUri,
        accessTokenEndpoint: tokenUrl,
      });
      console.log("Logging the auth result");
      console.log(result);
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
        console.log(`Error: ${result.error}`);
      }
    } catch (error) {
      dispatch(authenticateError(JSON.stringify(error)));
      console.log(`Error: ${error}`);
    }
  }

  useEffect(() => {
    authenticate();
  }, []);

  useEffect(() => {
    const handleTokenRefresh = (tokenResponse: {
      accessToken: string;
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
            idToken: undefined,
          })
        );
      }
    };

    // Set up event listener for token refresh events (works for both web and iOS)
    Keycloak.addListener("tokenRefresh", handleTokenRefresh);
  }, []);

  useEffect(() => {
    console.log(`Authenticating: ${authenticating}`);
    console.log(`isAuthenticated: ${isAuthenticated}`);
    console.log(`error: ${error}`);
  }, [authenticating, isAuthenticated, error]);

  // TODO implement for Android
  if (Capacitor.getPlatform() === "android") {
    return <React.StrictMode>{children}</React.StrictMode>;
  }

  // if (error) {
  //   setInterval(() => {
  //     authenticate();
  //   }, 3000);
  //   return (
  //     <div style={{ marginTop: 100 }}>
  //       {error}
  //       <p>Trying again in 3 seconds</p>
  //     </div>
  //   );
  // }

  if (authenticating) {
    return <div>Signing in...</div>;
  }

  if (!isAuthenticated) {
    return <div>{message}</div>;
  }

  return <React.StrictMode>{children}</React.StrictMode>;
};

export default React.memo(AuthWrapper);
