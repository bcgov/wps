import axios from "axios";
import { API_BASE_URL, API_PUBLIC_BASE_URL } from "@/utils/env";
import type { AxiosInstance } from "axios";

export type ApiMode = "public" | "authenticated";

export const authenticatedApi = axios.create({
  baseURL: API_BASE_URL,
});

export const publicApi = axios.create({
  baseURL: API_PUBLIC_BASE_URL + "/asa-go",
});

let currentApiMode: ApiMode = "public";

export const setApiMode = (mode: ApiMode) => {
  currentApiMode = mode;
};

export const getApiClient = (): AxiosInstance => {
  return currentApiMode === "authenticated" ? authenticatedApi : publicApi;
};
