import { App as CapacitorApp, AppState } from "@capacitor/app";
import { useEffect, useState } from "react";

/**
 * Hook to track whether the app is currently active (foregrounded).
 * Returns a boolean indicating active state.
 */
export const useAppIsActive = () => {
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    const handleAppStateChange = (state: AppState) => {
      setIsActive(state.isActive);
    };

    const listenerPromise = CapacitorApp.addListener(
      "appStateChange",
      handleAppStateChange
    );

    return () => {
      listenerPromise.then((h) => h.remove()).catch(() => {});
    };
  }, []);

  return isActive;
};
