import React, { useState, useCallback } from 'react'
import { makeStyles } from '@material-ui/core/styles'
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

const useStyles = makeStyles({
  root: {
    paddingTop: 12,
    paddingBottom: 12
  }
})

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
  const classes = useStyles()
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
    <div className={classes.root}>
      <Map center={fromLonLat(center)} zoom={zoom} renderTooltip={renderTooltip}>
        <LayerSwitch
          title="Base Layers"
          layersMap={baseLayersMap}
          layerUrl={tileLayerUrl}
          setLayerUrl={setTileLayerUrl}
        />
        {tileLayerUrl === satelliteLayerUrl && (
          <TileLayer
            source={
              new olSource.XYZ({
                url: satelliteLayerUrl,
                attributions: ArcGISAttribution
              })
            }
          />
        )}
        {tileLayerUrl === terrainLayerUrl && (
          <TileLayer
            source={
              new olSource.XYZ({
                url: terrainLayerUrl,
                attributions: ArcGISAttribution
              })
            }
          />
        )}
        {tileLayerUrl === topoLayerUrl && (
          <TileLayer
            source={
              new olSource.XYZ({
                url: topoLayerUrl,
                attributions: ArcGISAttribution
              })
            }
          />
        )}
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
    </div>
  )
}

export default React.memo(WeatherMap)
