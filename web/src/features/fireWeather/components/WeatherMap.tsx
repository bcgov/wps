import React, { useCallback } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { fromLonLat, get } from 'ol/proj'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { FeatureLike } from 'ol/Feature'

import WeatherStationsGeoJson from 'features/fireWeather/components/weather-stations-geojson.json'
import Map from 'features/map/Map'
import TileLayer from 'features/map/TileLayer'
import VectorLayer from 'features/map/VectorLayer'

const styles = {
  Point: new Style({
    image: new CircleStyle({
      radius: 3.5,
      fill: new Fill({
        color: '#E59982' //'rgba(0, 0, 255, 1)'
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

const center = [-123.3656, 51.4484] // BC
const zoom = 6

const WeatherMap = () => {
  const classes = useStyles()
  const renderTooltip = useCallback((f: FeatureLike | null) => {
    if (!f) return null

    return <div>Station: {f.get('STATION_NAME')}</div>
  }, [])

  return (
    <div className={classes.root}>
      <Map center={fromLonLat(center)} zoom={zoom} renderTooltip={renderTooltip}>
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
