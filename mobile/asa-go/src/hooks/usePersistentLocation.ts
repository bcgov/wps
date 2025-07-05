import { useCallback, useEffect, useRef } from "react";
import { App } from "@capacitor/app";
import { Geolocation, PermissionStatus } from "@capacitor/geolocation";
import { useDispatch, useSelector } from "react-redux";
import { setError, setPosition, setWatching } from "@/slices/geolocationSlice";
import { selectGeolocation } from "@/store";

export const usePersistentLocationWatch = () => {
  const dispatch = useDispatch();
  const watchIdRef = useRef<string | null>(null);
  const isWatchingRef = useRef(false);

  const { position, error, watching } = useSelector(selectGeolocation);

  const clearWatch = useCallback(async () => {
    if (watchIdRef.current != null) {
      try {
        await Geolocation.clearWatch({ id: watchIdRef.current });
      } catch {
        // ignore errors
      }
      watchIdRef.current = null;
      isWatchingRef.current = false;
      dispatch(setWatching(false));
    }
  }, [dispatch]);

  // used to force a fresh position update - useful when resuming app use
  const getCurrentPosition = useCallback(async () => {
    try {
      const position = await Geolocation.getCurrentPosition({
        enableHighAccuracy: true,
        timeout: 60000, // give it a minute
      });
      dispatch(setPosition(position));
      dispatch(setError(null));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to get current position";
      dispatch(setError(message));
    }
  }, [dispatch]);

  // main start watching function with permission checks
  const startWatching = useCallback(async () => {
    if (isWatchingRef.current) return; // prevent double watch

    try {
      const permStatus: PermissionStatus = await Geolocation.checkPermissions();

      if (permStatus.location === "denied") {
        const requestStatus = await Geolocation.requestPermissions();
        if (requestStatus.location === "denied") {
          dispatch(setError("Location permission denied"));
          return;
        }
      }

      await clearWatch(); // clear any previous watch before starting new one

      const id = await Geolocation.watchPosition(
        { enableHighAccuracy: true, timeout: 30000 },
        (position, err) => {
          if (err) {
            dispatch(setError(err?.message ?? "Unknown geolocation error"));
            return;
          }
          if (position) {
            dispatch(setPosition(position));
            dispatch(setError(null)); // clear previous errors on success
          }
        }
      );

      watchIdRef.current = id;
      isWatchingRef.current = true;
      dispatch(setWatching(true));
      dispatch(setError(null));
    } catch (error) {
      const message =
        error && typeof error === "object" && "message" in error
          ? (error as Error).message
          : "Failed to start geolocation watch";
      dispatch(setError(message));
    }
  }, [dispatch, clearWatch]);

  useEffect(() => {
    startWatching();

    const handle = App.addListener("appStateChange", ({ isActive }) => {
      if (isActive) {
        getCurrentPosition();
        startWatching();
      }
    });

    return () => {
      clearWatch();
      handle.then((h) => h.remove());
    };
  }, [clearWatch, getCurrentPosition, startWatching]);

  return {
    position,
    error,
    watching,
    startWatching,
    getCurrentPosition,
    clearWatch,
  };
};
