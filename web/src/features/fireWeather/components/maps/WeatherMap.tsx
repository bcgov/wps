import React, { useState, useCallback } from 'react'
import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'

import WeatherStationsGeoJson from 'features/fireWeather/components/maps/weather-stations-geojson.json'
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

const getArcGISAttribution = (service: string): string =>
  `Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/${service}/MapServer" target="_blank">ArcGIS</a>`
const getArcGISMapUrl = (service: string): string =>
  `https://server.arcgisonline.com/ArcGIS/rest/services/${service}/MapServer/tile/{z}/{y}/{x}`
const arcGisServicesMap = {
  Satellite: 'World_Imagery',
  Terrain: 'World_Terrain_Base',
  Topographic: 'World_Topo_Map'
}

const center = [-123.3656, 51.4484] // BC
const zoom = 6

const WeatherMap = () => {
  const [service, setService] = useState(arcGisServicesMap['Satellite'])

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
            url: getArcGISMapUrl(service),
            attributions: getArcGISAttribution(service)
          })
        }
      />
      <VectorLayer
        source={
          new olSource.Vector({
            features: new GeoJSON().readFeatures(WeatherStationsGeoJson, {
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
