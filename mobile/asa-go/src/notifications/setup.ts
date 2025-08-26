import { PushNotifications } from "@capacitor/push-notifications";

export const setupPushNotifications = async () => {
  await PushNotifications.addListener("registration", (token) => {
    console.debug("Registration token: ", token.value);
    console.info("Successfully registered for push notifications");
  });

  await PushNotifications.addListener("registrationError", (err) => {
    console.error("Registration error: ", err.error);
  });

  let permStatus = await PushNotifications.checkPermissions();

  if (permStatus.receive === "prompt") {
    permStatus = await PushNotifications.requestPermissions();
  }

  if (permStatus.receive !== "granted") {
    throw new Error("User denied push notification permissions");
  }

  await PushNotifications.register();
};
