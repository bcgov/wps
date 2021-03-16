import React, { useState, useCallback, useEffect } from 'react'
import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'

import Map from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'
import LayerSwitch from 'features/fireWeather/components/maps/LayerSwitch'

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
const baseArcGISUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services'
const getArcGISMapTileUrl = (service: string): string =>
  `${baseArcGISUrl}/${service}/MapServer/tile/{z}/{y}/{x}`
const getArcGISMapTileInfoUrl = (service: string): string =>
  `${baseArcGISUrl}/${service}/MapServer?f=pjson`
const arcGisServicesMap = {
  Satellite: 'World_Imagery',
  Terrain: 'World_Terrain_Base',
  Topographic: 'World_Topo_Map'
}

const center = [-123.3656, 51.4484] // BC
const zoom = 6

const WeatherMap = () => {
  const [service, setService] = useState(arcGisServicesMap['Satellite'])
  const [baseLayerAttribution, setBaseLayerAttribution] = useState('Not available')
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
  }, [])

  useEffect(() => {
    fetch(getArcGISMapTileInfoUrl(service))
      .then(resp => resp.json())
      .then(json => {
        if (typeof json.copyrightText === 'string') {
          setBaseLayerAttribution(json.copyrightText)
        }
      })
  }, [service])

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
      <LayerSwitch map={arcGisServicesMap} value={service} setValue={setService} />
      <TileLayer
        source={
          new olSource.XYZ({
            url: getArcGISMapTileUrl(service),
            attributions: baseLayerAttribution
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
