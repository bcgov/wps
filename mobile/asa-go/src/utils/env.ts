let ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL as string,
  PMTILES_BUCKET: import.meta.env.VITE_PMTILES_BUCKET as string,
};
ENV = {
  // TODO figure out mobile env substitution
  API_BASE_URL: "http://localhost:8080/api",
  PMTILES_BUCKET: "https://nrs.objectstore.gov.bc.ca/lwzrin/psu/pmtiles/"
};

export const { API_BASE_URL, PMTILES_BUCKET } = ENV;
