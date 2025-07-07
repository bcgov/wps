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

  // Debug environment variables
  console.log("All environment variables:", import.meta.env);
  console.log(
    "VITE_KEYCLOAK_AUTH_URL:",
    import.meta.env.VITE_KEYCLOAK_AUTH_URL
  );
  console.log("VITE_KEYCLOAK_REALM:", import.meta.env.VITE_KEYCLOAK_REALM);
  console.log("VITE_KEYCLOAK_CLIENT:", import.meta.env.VITE_KEYCLOAK_CLIENT);

  Keycloak.echo({ value: "helloWorld" });
  const realm = import.meta.env.VITE_KEYCLOAK_REALM;
  const authUrl = `${
    import.meta.env.VITE_KEYCLOAK_AUTH_URL
  }/realms/${realm}/protocol/openid-connect/auth`;
  const tokenUrl = `${
    import.meta.env.VITE_KEYCLOAK_AUTH_URL
  }/realms/${realm}/protocol/openid-connect/token`;

  console.log("Constructed authUrl:", authUrl);
  console.log("Constructed tokenUrl:", tokenUrl);

  // Test the echo method
  Keycloak.echo({ value: "helloWorld" });

  // Simple authentication - just get the authorization code
  Keycloak.authenticate({
    authorizationBaseUrl: authUrl,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
    redirectUrl: "http://localhost:8100/auth/callback",
  })
    .then((result) => {
      console.log("🎉 Authentication successful:", result);
      // The result contains: { redirectUrl, code, state, ... }
      // You can now exchange the code for tokens in JavaScript if needed
      if (result.code) {
        console.log("Got authorization code:", result.code);
        // TODO: Exchange code for tokens using your preferred HTTP library
      }
    })
    .catch((error) => {
      console.error("❌ Authentication failed:", error);
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
