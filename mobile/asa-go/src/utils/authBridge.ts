import { registerPlugin } from "@capacitor/core";

interface AuthBridgePlugin {
  authStart(options: { idpHint?: string }): Promise<{
    error?: string;
    idToken?: string;
    accessToken?: string;
    authorized?: boolean;
  }>;

  logout(options: Record<string, never>): Promise<{ error?: string }>;

  token(
    options: Record<string, never>
  ): Promise<{ error?: string; idToken?: string; accessToken?: string }>;

  authStatus(
    options: Record<string, never>
  ): Promise<{ error?: string; authorized?: boolean }>;
}

const AuthBridge = registerPlugin<AuthBridgePlugin>("AuthBridge");

export default AuthBridge;
