import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'

import WeatherStationsGeoJson from 'features/fireWeather/components/weather-stations-geojson.json'
import Map from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'

const styles = {
  Point: new Style({
    image: new CircleStyle({
      radius: 3,
      fill: new Fill({
        color: 'pink' //'rgba(0, 0, 255, 1)'
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

const center = [-123.3656, 48.4284] // Victoria
const zoom = 5

const WeatherMap = () => {
  const classes = useStyles()

  return (
    <div className={classes.root}>
      <Map center={fromLonLat(center)} zoom={zoom}>
        <TileLayer
          source={
            new olSource.XYZ({
              url:
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
              attributions:
                'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer" target="_blank">ArcGIS</a>'
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
          zIndex={3}
        />
      </Map>
    </div>
  )
}

export default React.memo(WeatherMap)
