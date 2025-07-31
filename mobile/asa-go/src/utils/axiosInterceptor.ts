import axios from "@/api/axios";
import { AppThunk, selectToken } from "@/store";
import { isNil } from "lodash";

export const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use((config) => {
    const token = selectToken(getState());
    if (!isNil(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });
};