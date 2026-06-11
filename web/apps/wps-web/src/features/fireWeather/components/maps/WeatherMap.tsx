import type { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import { source } from 'features/fireWeather/components/maps/constants'

import MapComponent, { type RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import { fromLonLat } from 'ol/proj'
import React from 'react'

interface Props {
  redrawFlag?: RedrawCommand
  center: number[]
  isCollapsed: boolean
  toiFromQuery: string
  setMapCenter: (newCenter: number[]) => void
  selectedWxVariable: AccuracyWeatherVariableEnum
}

const WeatherMap = ({ redrawFlag, center, isCollapsed, toiFromQuery, setMapCenter, selectedWxVariable }: Props) => {
  return (
    <MapComponent
      center={fromLonLat(center)}
      isCollapsed={isCollapsed}
      setMapCenter={setMapCenter}
      redrawFlag={redrawFlag}
      selectedWxVariable={selectedWxVariable}
      toiFromQuery={toiFromQuery}
    >
      <TileLayer source={source} />
    </MapComponent>
  )
}

export default React.memo(WeatherMap)
