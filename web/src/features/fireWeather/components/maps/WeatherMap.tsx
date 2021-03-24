import React, { useState, useCallback, useEffect } from 'react'
import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'

import Map from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'

const styles = {
  Point: new Style({
    image: new CircleStyle({
      radius: 4,
      fill: new Fill({
        color: '#E59982'
      }),
      stroke: new Stroke({
        color: 'black'
      })
    })
  })
}

const WEATHER_STATIONS_WEB_FEATURE_SERVICE =
  'https://openmaps.gov.bc.ca/geo/pub/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&outputFormat=json&typeName=WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP&srsName=EPSG:3857'

const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

const center = [-123.3656, 51.4484] // BC
const zoom = 6

interface Props {
  redrawFlag?: boolean
}

const WeatherMap = ({ redrawFlag }: Props) => {
  const [wxStationsGeoJSON, setWxStationsGeoJSON] = useState({
    type: 'FeatureCollection',
    features: []
  })

  useEffect(() => {
    fetch(WEATHER_STATIONS_WEB_FEATURE_SERVICE)
      .then(resp => resp.json())
      .then(json => {
        setWxStationsGeoJSON(json)
      })
  }, [])

  const renderTooltip = useCallback((feature: FeatureLike | null) => {
    if (!feature) return null

    return (
      <div>
        {feature.get('STATION_NAME')} ({feature.get('STATION_CODE')})
      </div>
    )
  }, [])

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
            features: new GeoJSON().readFeatures(wxStationsGeoJSON, {
              featureProjection: get('EPSG:3857')
            })
          })
        }
        style={styles.Point}
        zIndex={1}
      />
    </Map>
  )
}

export default React.memo(WeatherMap)
