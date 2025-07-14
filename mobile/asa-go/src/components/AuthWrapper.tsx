import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
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

  if (error) {
    return <div>{error}</div>;
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
