export interface FireSeason {
  start_month: number
  start_day: number
  end_month: number
  end_day: number
}

export interface StationGeometry {
  type: string
  coordinates: number[]
}

export interface StationProperties {
  code: number
  name: string
  ecodivision_name: string | null
  core_season: FireSeason
}

export interface DetailedStationProperties extends StationProperties {
  observations: {
    temperature: number
    relative_humidity: number
  }
  forecasts: {
    temperature: number
    relative_humidity: number
  }
}

export interface GeoJsonStation {
  type: string
  properties: StationProperties
  geometry: StationGeometry
}

export interface DetailedGeoJsonStation {
  type: string
  properties: DetailedStationProperties
  geometry: StationGeometry
}
