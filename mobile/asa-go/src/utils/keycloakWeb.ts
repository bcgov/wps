import Keycloak, { KeycloakInitOptions } from "keycloak-js";

export const kcInitOptions: KeycloakInitOptions = {
  onLoad: "login-required",
  checkLoginIframe: false,
  enableLogging: import.meta.env.MODE !== "production",
  pkceMethod: "S256",
};

export const getKeycloakInstance = (): Keycloak => {
  return new Keycloak({
    url: import.meta.env.VITE_KEYCLOAK_AUTH_URL,
    realm: import.meta.env.VITE_KEYCLOAK_REALM,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
  });
};
