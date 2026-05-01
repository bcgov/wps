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

  // keep auth headers on the authenticated client so public requests stay anonymous
  authenticatedApi.interceptors.request.use((config) => {
    const token = selectToken(store.getState());
    if (!isNil(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  authenticatedApi.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error?.response?.status === 401) {
        store.dispatch(resetAuthentication());
      }
      return Promise.reject(error);
    },
  );
};
