import axios from "axios";
import { API_BASE_URL, API_PUBLIC_BASE_URL } from "@/utils/env";
import { store } from "@/store";
import type { AxiosInstance } from "axios";

export const authenticatedApi = axios.create({
  baseURL: API_BASE_URL,
});

export const publicApi = axios.create({
  baseURL: API_PUBLIC_BASE_URL + "/asa-go",
});

export const getApiClient = (): AxiosInstance => {
  return store.getState().authentication.isAuthenticated ? authenticatedApi : publicApi;
};
