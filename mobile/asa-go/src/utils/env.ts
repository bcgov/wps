export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
export const API_PUBLIC_BASE_URL =
  (import.meta.env.VITE_PUBLIC_API_BASE_URL as string | undefined) ??
  API_BASE_URL;
export const PMTILES_BUCKET = import.meta.env.VITE_PMTILES_BUCKET as string;
export const BASEMAP_TILE_URL = import.meta.env.VITE_BASEMAP_TILE_URL as string;
export const BASEMAP_STYLE_URL = import.meta.env
  .VITE_BASEMAP_STYLE_URL as string;
