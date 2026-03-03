import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "ca.bc.gov.asago",
  appName: "asa-go",
  webDir: "dist",
  ios: { scheme: "ASA Go" },
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
