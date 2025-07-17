import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Capacitor } from "@capacitor/core";
import { AppDispatch, selectAuthentication } from "@/store";
import { authenticate } from "@/slices/authenticationSlice";

interface Props {
  children: React.ReactElement;
}

const AuthWrapper = ({ children }: Props) => {
  const dispatch: AppDispatch = useDispatch();
  const { isAuthenticated, authenticating, error } =
    useSelector(selectAuthentication);

  useEffect(() => {
    dispatch(authenticate());
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // TODO implement for Android
  if (Capacitor.getPlatform() === "android") {
    return <React.StrictMode>{children}</React.StrictMode>;
  }

  if (error) {
    return <div style={{ marginTop: 100 }}>{error}</div>;
  }

  if (authenticating) {
    return <div>Signing in...</div>;
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>;
  }

  return <React.StrictMode>{children}</React.StrictMode>;
};

export default React.memo(AuthWrapper);
