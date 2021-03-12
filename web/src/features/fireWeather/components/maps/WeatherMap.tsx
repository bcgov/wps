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

const ArcGISAttribution =
  'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer" target="_blank">ArcGIS</a>'
const getArcGISMapUrl = (service: string): string =>
  `https://server.arcgisonline.com/ArcGIS/rest/services/${service}/MapServer/tile/{z}/{y}/{x}`
const satelliteLayerUrl = getArcGISMapUrl('World_Imagery')
const terrainLayerUrl = getArcGISMapUrl('World_Terrain_Base')
const topoLayerUrl = getArcGISMapUrl('World_Topo_Map')
const baseLayersMap = {
  Satellite: satelliteLayerUrl,
  Terrain: terrainLayerUrl,
  Topographic: topoLayerUrl
}

const center = [-123.3656, 51.4484] // BC
const zoom = 6

const WeatherMap = () => {
  const [tileLayerUrl, setTileLayerUrl] = useState(satelliteLayerUrl)

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
      <LayerSwitch
        layersMap={baseLayersMap}
        layerUrl={tileLayerUrl}
        setLayerUrl={setTileLayerUrl}
      />
      <TileLayer
        source={
          new olSource.XYZ({
            url: tileLayerUrl,
            attributions: ArcGISAttribution
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
