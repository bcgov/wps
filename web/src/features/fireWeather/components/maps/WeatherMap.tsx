import React, { useCallback, useEffect } from 'react'

import { Button } from '@material-ui/core'

import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'
import { fetchWxStations, selectStation } from 'features/stations/slices/stationsSlice'

import Map, { RedrawCommand } from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'
import { useDispatch, useSelector } from 'react-redux'

import { selectFireWeatherStations } from 'app/rootReducer'
import { getDetailedStations, StationSource } from 'api/stationAPI'
import { computeRHAccuracyColor, computeTempAccuracyColor } from 'features/fireWeather/components/maps/stationAccuracy'
import { AccuracyWeatherVariableEnum } from '../AccuracyVariablePicker'

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

const zoom = 6

const rhPointStyleFunction = (feature: any) => {
  return new Style({
    image: new CircleStyle({
      radius: 4,
      fill: new Fill({ color: computeRHAccuracyColor(feature.values_) }),
      stroke: new Stroke({ color: 'black', width: 1 })
    })
  })
}

const tempPointStyleFunction = (feature: any) => {
  return new Style({
    image: new CircleStyle({
      radius: 4,
      fill: new Fill({ color: computeTempAccuracyColor(feature.values_) }),
      stroke: new Stroke({ color: 'black', width: 1 })
    })
  })
}
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
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)
  const styleFunction = selectedWxVariable === 
    AccuracyWeatherVariableEnum['Relative Humidity'] ? rhPointStyleFunction : tempPointStyleFunction

  useEffect(() => {
    dispatch(
      fetchWxStations(getDetailedStations, StationSource.unspecified, toiFromQuery)
    )
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const renderTooltip = useCallback(
    (feature: FeatureLike | null) => {
      if (!feature) return null

      return (
        <div data-testid={`station-${feature.get('code')}-tooltip`}>
          <p>
            {feature.get('name')} ({feature.get('code')})
          </p>
          <Button
            variant="outlined"
            size="small"
            onClick={() => {
              dispatch(selectStation(feature.get('code')))
            }}
            data-testid={`select-wx-station-${feature.get('code')}-button`}
          >
            Select
          </Button>
        </div>
      )
    },
    [dispatch]
  )

  return (
    <Map
      center={fromLonLat(center)}
      isCollapsed={isCollapsed}
      setMapCenter={setMapCenter}
      zoom={zoom}
      redrawFlag={redrawFlag}
      renderTooltip={renderTooltip}
    >
      <TileLayer source={source} />
      <VectorLayer
        source={
          new olSource.Vector({
            features: new GeoJSON().readFeatures(
              { type: 'FeatureCollection', features: stations },
              {
                featureProjection: get('EPSG:3857')
              }
            )
          })
        }
        style={styleFunction}
        zIndex={1}
      />
    </Map>
  )
}

export default React.memo(WeatherMap)
