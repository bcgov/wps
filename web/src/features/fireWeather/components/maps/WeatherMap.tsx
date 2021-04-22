import React, { useCallback, useEffect } from 'react'

import { Button } from '@material-ui/core'

import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'

import Map from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'
import { useDispatch, useSelector } from 'react-redux'

import { selectFireWeatherStations } from 'app/rootReducer'
import { getDetailedStations } from 'api/stationAPI'
import { computeAccuracyColors } from 'features/fireWeather/components/maps/stationAccuracy'

const pointStyleFunction = (feature: any, resolution: any) => {
  const colorResult = computeAccuracyColors(feature.values_)
  return new Style({
    image: new CircleStyle({
      radius: 4,
      fill: new Fill({ color: colorResult.relative_humidity }),
      stroke: new Stroke({ color: 'black', width: 1 })
    })
  })
}

const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

const center = [-123.3656, 51.4484] // BC
const zoom = 6

interface Props {
  redrawFlag?: boolean
  selectedStationCodes: number[]
  setSelectedStationCodes: (codes: number[]) => void
}

const WeatherMap = ({
  redrawFlag,
  selectedStationCodes,
  setSelectedStationCodes
}: Props) => {
  const dispatch = useDispatch()

  const { stations } = useSelector(selectFireWeatherStations)

  useEffect(() => {
    dispatch(fetchWxStations(getDetailedStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const renderTooltip = useCallback(
    (feature: FeatureLike | null) => {
      if (!feature) return null

      return (
        <div>
          <p>
            {feature.get('name')} ({feature.get('code')})
          </p>
          <Button
            variant="outlined"
            size="small"
            onClick={() => {
              setSelectedStationCodes([...selectedStationCodes, feature.get('code')])
            }}
            data-testid={`select-wx-station-${feature.get('code')}-button`}
          >
            Select
          </Button>
        </div>
      )
    },
    [selectedStationCodes]
  )

  return (
    <Map
      center={fromLonLat(center)}
      zoom={zoom}
      renderTooltip={renderTooltip}
      redrawFlag={redrawFlag}
    >
      <TileLayer
        source={
          new olSource.XYZ({
            url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
            // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
            // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
            attributions: 'Government of British Columbia, DataBC, GeoBC'
          })
        }
      />
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
        style={pointStyleFunction}
        zIndex={1}
      />
    </Map>
  )
}

export default React.memo(WeatherMap)
