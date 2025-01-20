let ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL as string,
  PMTILES_BUCKET: import.meta.env.VITE_PMTILES_BUCKET as string,
  MUI_LICENSE: import.meta.env.VITE_MUI_LICENSE_KEY as string,
};
// If the app is built using 'npm run build'
if (import.meta.env.MODE === "production") {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    // TODO: Figure out why axios goes to http on gets!
    API_BASE_URL: "http://localhost:8080/api",
    PMTILES_BUCKET: "https://nrs.objectstore.gov.bc.ca/lwzrin/psu/pmtiles/",
    MUI_LICENSE:
      "b3024910924a257f1c5e714689768c93Tz04NjAxOSxFPTE3NDE0NzA3MjcwMDAsUz1wcm8sTE09c3Vic2NyaXB0aW9uLEtWPTI",
  };
}

export const { API_BASE_URL, PMTILES_BUCKET, MUI_LICENSE } = ENV;
