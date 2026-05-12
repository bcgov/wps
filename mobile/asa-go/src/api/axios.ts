import axios from "axios";
import type { AxiosInstance } from "axios";

export const api = axios.create();

export const getApiClient = (): AxiosInstance => {
  return api;
};
