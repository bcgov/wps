import { ScreenOrientation } from "@capacitor/screen-orientation";
import { useEffect, useState } from "react";

export function useIsPortrait() {
  const [isPortrait, setIsPortrait] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const syncOrientation = async () => {
      try {
        const info = await ScreenOrientation.orientation();

        if (isMounted) {
          setIsPortrait(!info.type.includes("landscape"));
        }
      } catch {
        // Keep the previous value if the native plugin read fails.
      }
    };

    const listenerPromise = Promise.resolve(
      ScreenOrientation.addListener("screenOrientationChange", syncOrientation),
    );

    // Prime state from the current native orientation on mount.
    void syncOrientation();

    return () => {
      isMounted = false;
      // Remove only this hook instance's native listener. Avoid global listener
      // cleanup because this hook is used in more than one component.
      void listenerPromise
        .then((listener) => listener?.remove?.())
        .catch(() => {});
    };
  }, []);

  return isPortrait;
}
