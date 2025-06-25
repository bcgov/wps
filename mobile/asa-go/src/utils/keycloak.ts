import { KC_AUTH_URL, KC_CLIENT, KC_REALM } from "@/utils/env";
import Keycloak, {
  KeycloakInitOptions,
  KeycloakLoginOptions,
  KeycloakLogoutOptions,
  KeycloakRegisterOptions,
} from "keycloak-js";
import { Browser } from "@capacitor/browser";

export const kcInitOptions: KeycloakInitOptions = {
  onLoad: "login-required",
  checkLoginIframe: false,
  enableLogging: import.meta.env.MODE !== "production",
  pkceMethod: "S256",
  redirectUri: window.location.origin,
};

export const getKeycloakInstance = (): Keycloak => {
  return new Keycloak({
    url: KC_AUTH_URL,
    realm: KC_REALM,
    clientId: KC_CLIENT,
  });
};

// Capacitor Keycloak utility functions
const CAPACITOR_REDIRECT_URI = "asago://auth"; // TODO: Replace with your app's scheme

export async function capacitorLogin(
  keycloak: Keycloak,
  options?: KeycloakLoginOptions
) {
  await keycloak.login({ ...options, redirectUri: CAPACITOR_REDIRECT_URI });
  console.log(keycloak.token);
  // await Browser.open({ url: loginUrl });
  // return new Promise<void>((resolve, reject) => {
  //   const handler = (event: { url: string }) => {
  //     if (event.url && event.url.startsWith(CAPACITOR_REDIRECT_URI)) {
  //       App.removeAllListeners();
  //       Browser.close();
  //       try {
  //         // Extract code and state from the URL
  //         const url = new URL(event.url);
  //         const code = url.searchParams.get("code");
  //         if (code) {
  //           // You may need to call keycloak.login() or keycloak.init() with the code, depending on your flow
  //           // For PKCE, Keycloak JS should handle the code exchange automatically on init
  //           resolve();
  //         } else {
  //           reject(new Error("No code found in redirect URL"));
  //         }
  //       } catch (e) {
  //         reject(e);
  //       }
  //     }
  //   };
  //   App.addListener("appUrlOpen", handler);
  // });
}

/**
 * Deep Link Setup Instructions (iOS & Android):
 *
 * iOS:
 * 1. Open ios/App/App/Info.plist
 * 2. Add:
 *    <key>CFBundleURLTypes</key>
 *    <array>
 *      <dict>
 *        <key>CFBundleURLSchemes</key>
 *        <array>
 *          <string>myapp</string> <!-- Use your scheme -->
 *        </array>
 *      </dict>
 *    </array>
 *
 * Android:
 * 1. Open android/app/src/main/AndroidManifest.xml
 * 2. Inside <activity ...>, add:
 *    <intent-filter android:autoVerify="true">
 *      <action android:name="android.intent.action.VIEW" />
 *      <category android:name="android.intent.category.DEFAULT" />
 *      <category android:name="android.intent.category.BROWSABLE" />
 *      <data android:scheme="myapp" android:host="auth" />
 *    </intent-filter>
 *  (Replace 'myapp' and 'auth' with your scheme/host as needed)
 *
 * 3. Set the redirect URI in Keycloak and your app to match (e.g., myapp://auth)
 *
 * 4. On successful login, Keycloak will redirect to your app, triggering the handler above.
 */

export async function capacitorLogout(
  keycloak: Keycloak,
  options?: KeycloakLogoutOptions
) {
  const logoutUrl = keycloak.createLogoutUrl({
    ...options,
    redirectUri: CAPACITOR_REDIRECT_URI,
  });
  return Browser.open({ url: logoutUrl });
}

export async function capacitorRegister(
  keycloak: Keycloak,
  options?: KeycloakRegisterOptions
) {
  const registerUrl = await keycloak.createRegisterUrl({
    ...options,
    redirectUri: CAPACITOR_REDIRECT_URI,
  });
  return Browser.open({ url: registerUrl });
}

export function getCapacitorRedirectUri() {
  return CAPACITOR_REDIRECT_URI;
}

// Usage:
// import { getKeycloakInstance, capacitorLogin, capacitorLogout, ... } from './keycloak';
// const keycloak = getKeycloakInstance();
// await capacitorLogin(keycloak);
// ...
