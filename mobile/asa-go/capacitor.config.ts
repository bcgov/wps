import type { CapacitorConfig } from "@capacitor/cli";

const mode = process.env.APP_ENV ?? "prod";
const isDev = mode === "dev";

const config: CapacitorConfig = {
  appId: isDev ? "ca.bc.gov.asago.dev" : "ca.bc.gov.asago",
  appName: isDev ? "ASA Go Dev" : "ASA Go",
  webDir: "dist",
  android: {
    flavor: isDev ? "dev" : "prod",
  },
  ios: {
    scheme: isDev ? "ASA Go dev" : "ASA Go",
  },
  plugins: {
    FirebaseMessaging: {
      presentationOptions: ["alert", "badge", "sound"], // iOS only
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 500,
      backgroundColor: "#000C3A",
      iosSplashImageName: "splash",
      showSpinner: false,
    },
  },
};

export default config;
