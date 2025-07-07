import { useCallback, useEffect, useRef } from "react";
import { Geolocation } from "@capacitor/geolocation";
import { App } from "@capacitor/app";
import { useDispatch } from "react-redux";
import { setError, setLoading, setPosition } from "@/slices/geolocationSlice";

interface useLocationProps {
  enabled?: boolean;
}

export const useLocation = ({ enabled }: useLocationProps) => {
  const dispatch = useDispatch();
  const watchIdRef = useRef<string | null>(null);

  const startWatching = useCallback(async () => {
    dispatch(setLoading(true));

    try {
      const permStatus = await Geolocation.checkPermissions();
      if (permStatus.location !== "granted") {
        const req = await Geolocation.requestPermissions();
        if (req.location !== "granted") {
          dispatch(setError("Location permission denied"));
          return;
        }
      }

      // get initial position
      const current = await Geolocation.getCurrentPosition({
        enableHighAccuracy: true,
        timeout: 60000, // give it a minute
      });
      dispatch(setPosition(current));

      // start watching position
      watchIdRef.current = await Geolocation.watchPosition(
        { enableHighAccuracy: true, timeout: 30000 },
        (pos, err) => {
          if (err) {
            dispatch(setError(err.message));
          } else if (pos) {
            dispatch(setPosition(pos));
          }
        }
      );
    } catch (e) {
      dispatch(setError((e as Error).message));
    }
  }, [dispatch]);

  const stopWatching = async () => {
    if (watchIdRef.current) {
      await Geolocation.clearWatch({ id: watchIdRef.current });
      watchIdRef.current = null;
    }
  };

  useEffect(() => {
    startWatching();

    const appListener = App.addListener("appStateChange", async (state) => {
      if (state.isActive && enabled) {
        await startWatching();
      } else {
        await stopWatching();
      }
    });

    return () => {
      stopWatching();
      appListener.then((h) => h.remove());
    };
  }, [startWatching, enabled]);
};
