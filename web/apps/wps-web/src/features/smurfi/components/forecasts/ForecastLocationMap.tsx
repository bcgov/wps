import { Box } from '@mui/material'
import { source as baseMapSource } from '@/features/fireWeather/components/maps/constants'
import {
  createCurrentFirePointsLayer,
  createCurrentFirePolygonsLayer
} from '@/features/currentFires/map/currentFireLayers'
import { CURRENT_FIRE_STATUS_OPTIONS } from '@/features/currentFires/map/layerVisibility'
import { createSpotStatusIcon } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Feature, Map, View } from 'ol'
import { Point } from 'ol/geom'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import { fromLonLat } from 'ol/proj'
import VectorSource from 'ol/source/Vector'
import { Style } from 'ol/style'
import { useEffect, useRef } from 'react'
import 'ol/ol.css'

interface ForecastLocation {
  latitude: number
  longitude: number
}

interface ForecastLocationMapProps {
  location: ForecastLocation
  spotStatus: SpotRequestStatus
  height?: number | string
}

const getForecastMarkerStyle = (status: SpotRequestStatus) =>
  new Style({
    image: createSpotStatusIcon(status)
  })

const ForecastLocationMap = ({ location, spotStatus, height = 280 }: ForecastLocationMapProps) => {
  const mapRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!mapRef.current) {
      return
    }

    const forecastCoordinate = fromLonLat([location.longitude, location.latitude])
    const forecastMarker = new Feature({
      geometry: new Point(forecastCoordinate)
    })
    forecastMarker.setStyle(getForecastMarkerStyle(spotStatus))

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        createCurrentFirePolygonsLayer(CURRENT_FIRE_STATUS_OPTIONS),
        createCurrentFirePointsLayer(CURRENT_FIRE_STATUS_OPTIONS),
        new VectorLayer({
          source: new VectorSource({ features: [forecastMarker] }),
          zIndex: 50
        })
      ],
      view: new View({
        center: forecastCoordinate,
        zoom: 12
      })
    })

    requestAnimationFrame(() => mapObject.updateSize())

    return () => {
      mapObject.setTarget('')
    }
  }, [location.latitude, location.longitude, spotStatus])

  return (
    <Box sx={{ width: '100%', height, border: '1px solid', borderColor: 'divider' }}>
      <Box ref={mapRef} sx={{ width: '100%', height: '100%' }} />
    </Box>
  )
}

export default ForecastLocationMap
