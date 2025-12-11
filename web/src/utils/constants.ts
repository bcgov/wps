export const WEATHER_STATION_MAP_LINK =
  'https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=c36baf74b74a46978cf517579a9ee332'

export const FWI_VALUES_DECIMAL = 2
export const TEMPERATURE_VALUES_DECIMAL = 1
export const WIND_SPEED_VALUES_DECIMAL = 1
export const WIND_SPEED_FORECAST_VALUES_DECIMAL = 0 // Feedback from forecasters: no decimal places for wind.
export const WIND_DIRECTION_VALUES_DECIMAL = 0
export const PRECIP_VALUES_DECIMAL = 1
export const DEW_POINT_VALUES_DECIMAL = 1
export const RH_VALUES_DECIMAL = 0
export const FFMC_VALUES_DECIMAL = 1
export const ISI_VALUES_DECIMAL = 1

export const PACIFIC_IANA_TIMEZONE = 'Canada/Pacific'
export const PST_UTC_OFFSET = -8
export const PST_ISO_TIMEZONE = 'T00:00-08:00'

export const PERCENTILE_CALC_ROUTE = '/percentile-calculator'
export const MORECAST_ROUTE = '/morecast'
export const HFI_CALC_ROUTE = '/hfi-calculator'
export const C_HAINES_ROUTE = '/c-haines'
export const FBP_GO_ROUTE = 'https://psu.nrs.gov.bc.ca/fbp-go'
export const FIRE_BEHAVIOR_CALC_ROUTE = '/fire-behaviour-calculator'
export const FIRE_BEHAVIOUR_ADVISORY_ROUTE = '/auto-spatial-advisory'
export const MORE_CAST_2_ROUTE = '/morecast-2'
export const SFMS_INSIGHTS_ROUTE = '/insights'
export const LANDING_PAGE_ROUTE = '/'
export const FIRE_WATCH_ROUTE = '/fire-watch'

// ExpandableContainer widths
export const PARTIAL_WIDTH = 850
export const FULL_WIDTH = 1200

// Map center
export const CENTER_OF_BC = [-125, 54.5]
export const BC_EXTENT = [
  [-139.1, 48.2], // [minLon, minLat]
  [-114.1, 60.0] // [maxLon, maxLat]]
]

// Application names
export const C_HAINES_NAME = 'C-Haines'
export const FBP_GO_NAME = 'FBP Go'
export const FIRE_BEHAVIOUR_ADVISORY_NAME = 'Auto Spatial Advisory'
export const FIRE_BEHAVIOUR_CALC_NAME = 'FireCalc'
export const HFI_CALC_NAME = 'HFI Calculator'
export const MORE_CAST_NAME = 'MoreCast'
export const PERCENTILE_CALC_NAME = 'Percentile Calculator'
export const SFMS_INSIGHTS_NAME = 'SFMS Insights'
export const FIRE_WATCH_NAME = 'Fire Watch'

// UI constants
export const HEADER_HEIGHT = 56
export type Order = 'asc' | 'desc'

// Document titles
export const LANDING_PAGE_DOC_TITLE = 'Decision Support Tools | BCWS PSU'
export const ASA_DOC_TITLE = 'Automated Spatial Advisory | BCWS PSU'
export const C_HAINES_DOC_TITLE = 'C-Haines | BCWS PSU'
export const FIRECALC_DOC_TITLE = 'FireCalc | BCWS PSU'
export const HFI_CALC_DOC_TITLE = 'HFI Calculator | BCWS PSU'
export const MORE_CAST_DOC_TITLE = 'MoreCast | BCWS PSU'
export const PERCENTILE_CALC_DOC_TITLE = 'Percentile Calculator | BCWS PSU'
export const SFMS_INSIGHTS_DOC_TITLE = 'SFMS Insights | BCWS PSU'
export const FIRE_WATCH_TITLE = 'Fire Watch | BCWS PSU'

export enum FireCentres {
  CARIBOO_FC = 'Cariboo Fire Centre',
  COASTAL_FC = 'Coastal Fire Centre',
  KAMLOOPS_FC = 'Kamloops Fire Centre',
  NORTHWEST_FC = 'Northwest Fire Centre',
  PRINCE_GEORGE_FC = 'Prince George Fire Centre',
  SOUTHEAST_FC = 'Southeast Fire Centre'
}

export enum AdvisoryStatus {
  ADVISORY = 'advisory',
  WARNING = 'warning'
}

export const DRAWER_WIDTH = 240
