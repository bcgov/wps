import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline } from "@mui/material";
import { ThemeProvider, StyledEngineProvider } from "@mui/material/styles";
import { Provider } from "react-redux";
import { store } from "@/store";
import { theme } from "@/theme.ts";
import { Keycloak } from "../../keycloak/src";
import App from "@/App.tsx";

const render = () => {
  const container = document.getElementById("root");
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
    accessTokenEndpoint: tokenUrl,
  })
    .then((result) => {
      console.log("🎉 Authentication response:", result);

      if (result.isAuthenticated) {
        console.log("✅ Authentication successful!");
        console.log("Access Token:", result.accessToken);

        if (result.refreshToken) {
          console.log("Refresh Token:", result.refreshToken);
        }

        if (result.idToken) {
          console.log("ID Token:", result.idToken);
        }

        console.log("Token Type:", result.tokenType);
        console.log("Expires In:", result.expiresIn, "seconds");
        console.log("Scope:", result.scope);

        // Store tokens securely for your app (consider using secure storage)
        // localStorage.setItem('accessToken', result.accessToken);
        // localStorage.setItem('refreshToken', result.refreshToken);
      } else {
        console.log("❌ Authentication failed");
        console.log("Error:", result.error);
        console.log("Error Description:", result.errorDescription);
        console.log("Redirect URL:", result.redirectUrl);
      }
    })
    .catch((error) => {
      console.error("❌ Authentication failed with exception:", error);
      console.log("Error details:", error);
    });

  // Null check to keep TypeScript happy
  if (container === null) {
    throw new Error("Root container is missing in index.html");
  }
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <StyledEngineProvider injectFirst>
            <App />
          </StyledEngineProvider>
        </ThemeProvider>
      </Provider>
    </StrictMode>
  );
};

render();
