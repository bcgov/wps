export const WEATHER_STATION_MAP_LINK =
  "https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=c36baf74b74a46978cf517579a9ee332";

export const BC_ROAD_BASE_MAP_SERVER_URL =
  "https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer";

export const FWI_VALUES_DECIMAL = 2;
export const TEMPERATURE_VALUES_DECIMAL = 1;
export const WIND_SPEED_VALUES_DECIMAL = 1;
export const WIND_SPEED_FORECAST_VALUES_DECIMAL = 0; // Feedback from forecasters: no decimal places for wind.
export const WIND_DIRECTION_VALUES_DECIMAL = 0;
export const PRECIP_VALUES_DECIMAL = 1;
export const DEW_POINT_VALUES_DECIMAL = 1;
export const RH_VALUES_DECIMAL = 0;
export const FFMC_VALUES_DECIMAL = 1;
export const ISI_VALUES_DECIMAL = 1;

export const PACIFIC_IANA_TIMEZONE = "Canada/Pacific";
export const PST_UTC_OFFSET = -8;
export const PST_ISO_TIMEZONE = "T00:00-08:00";

// Map center
export const CENTER_OF_BC = [-125, 54.5];
export const BC_EXTENT = [
  [-139.1, 48.2], // [minLon, minLat]
  [-114.1, 60.0], // [maxLon, maxLat]]
];

// Application names
export const FIRE_BEHAVIOUR_ADVISORY_NAME = "Auto Spatial Advisory";

export enum FireCentres {
  CARIBOO_FC = "Cariboo Fire Centre",
  COASTAL_FC = "Coastal Fire Centre",
  KAMLOOPS_FC = "Kamloops Fire Centre",
  NORTHWEST_FC = "Northwest Fire Centre",
  PRINCE_GEORGE_FC = "Prince George Fire Centre",
  SOUTHEAST_FC = "Southeast Fire Centre",
}

export enum AdvisoryStatus {
  ADVISORY = "advisory",
  WARNING = "warning",
}

export enum NavPanel {
  ADVISORY = "Advisory",
  MAP = "Map",
  PROFILE = "Profile",
}
