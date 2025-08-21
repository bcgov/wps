import axios from "@/api/axios";
import { resetAuthentication } from "@/slices/authenticationSlice";
import { AppThunk, selectToken } from "@/store";
import { isNil } from "lodash";

export const setAxiosRequestInterceptors =
  (): AppThunk => (dispatch, getState) => {
    // Use axios interceptors to intercept any requests and add authorization headers.
    axios.interceptors.request.use((config) => {
      const token = selectToken(getState());
      if (!isNil(token)) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    });
    axios.interceptors.response.use(
      // If there is a response we simply return it
      (response) => {
        return response;
      },
      // If there is a 401 error we force re-authentication; otherwise we forward the error.
      (error) => {
        if (error?.response?.status === 401) {
          dispatch(resetAuthentication());
        }
        return Promise.reject(error);
      }
    );
  };
