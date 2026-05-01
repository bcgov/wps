import { authenticatedApi } from "@/api/axios";
import { resetAuthentication } from "@/slices/authenticationSlice";
import { selectToken, store } from "@/store";
import { isNil } from "lodash";

let interceptorsConfigured = false;

export const configureAxiosInterceptors = () => {
  if (interceptorsConfigured) {
    return;
  }

  interceptorsConfigured = true;

  // add auth headers on the authenticated client
  authenticatedApi.interceptors.request.use((config) => {
    const token = selectToken(store.getState());
    if (!isNil(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  authenticatedApi.interceptors.response.use(
    // If there is a response we simply return it
    (response) => response,

    // If there is a 401 error we force re-authentication; otherwise we forward the error.
    (error) => {
      if (error?.response?.status === 401) {
        store.dispatch(resetAuthentication());
      }
      return Promise.reject(error);
    },
  );
};
