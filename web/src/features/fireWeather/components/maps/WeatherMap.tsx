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

const BC_WEATHER_STATIONS_WEB_FEATURE_SERVICE =
  'https://openmaps.gov.bc.ca/geo/pub/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&outputFormat=json&typeName=WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP&srsName=EPSG:3857'
const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

const center = [-123.3656, 51.4484] // BC
const zoom = 6

const WeatherMap = () => {
  const [attributions, setAttributions] = useState('Not available')
  const [wxStationsGeoJSON, setWxStationsGeoJSON] = useState({
    type: 'FeatureCollection',
    features: []
  })

  useEffect(() => {
    fetch(BC_WEATHER_STATIONS_WEB_FEATURE_SERVICE)
      .then(resp => resp.json())
      .then(json => {
        setWxStationsGeoJSON(json)
      })

    fetch(`${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`)
      .then(resp => resp.json())
      .then(json => {
        if (typeof json.copyrightText === 'string') {
          setAttributions(json.copyrightText)
        }
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
    <Map center={fromLonLat(center)} zoom={zoom} renderTooltip={renderTooltip}>
      <TileLayer
        source={
          new olSource.XYZ({
            url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
            attributions
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
