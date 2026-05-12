import { api } from "@/api/axios";
import { resetAuthentication } from "@/slices/authenticationSlice";
import { API_BASE_URL, API_PUBLIC_BASE_URL } from "@/utils/env";
import { selectAuthentication, store } from "@/store";
import { isNil } from "lodash";

let interceptorsConfigured = false;

export const configureApiInterceptors = () => {
  if (interceptorsConfigured) {
    return;
  }

  interceptorsConfigured = true;

  api.interceptors.request.use((config) => {
    const { sessionMode, token } = selectAuthentication(store.getState());
    if (sessionMode === "authenticated" && !isNil(token)) {
      config.baseURL = API_BASE_URL;
      config.headers.set("Authorization", `Bearer ${token}`);
    } else {
      config.baseURL = `${API_PUBLIC_BASE_URL}/asa-go`;
      config.headers.delete("Authorization");
    }

    return config;
  });

  api.interceptors.response.use(
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
