import React from 'react'

import { fromLonLat } from 'ol/proj'
import * as olSource from 'ol/source'

import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'

import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'

const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

// Static source is allocated since our tiel source does not change and
// a new source is not allocated every time WeatherMap is re-rendered,
// which causes the TileLayer to re-render.
const source = new olSource.XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
  // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
  // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
  attributions: 'Government of British Columbia, DataBC, GeoBC'
})

interface Props {
  redrawFlag?: RedrawCommand
  center: number[]
  isCollapsed: boolean
  toiFromQuery: string
  setMapCenter: (newCenter: number[]) => void
  selectedWxVariable: AccuracyWeatherVariableEnum
}

const WeatherMap = ({
  redrawFlag,
  center,
  isCollapsed,
  toiFromQuery,
  setMapCenter,
  selectedWxVariable
}: Props) => {
  return (
    <Map
      center={fromLonLat(center)}
      isCollapsed={isCollapsed}
      setMapCenter={setMapCenter}
      redrawFlag={redrawFlag}
      selectedWxVariable={selectedWxVariable}
      toiFromQuery={toiFromQuery}
    >
      <TileLayer source={source} />
    </Map>
  )
}

export default React.memo(WeatherMap)
