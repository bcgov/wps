import React from 'react'

import { fromLonLat } from 'ol/proj'

import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'

import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import { source } from 'features/fireWeather/components/maps/constants'

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
