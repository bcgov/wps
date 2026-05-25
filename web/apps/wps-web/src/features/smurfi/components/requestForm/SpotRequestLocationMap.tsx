import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { Feature, Map, MapBrowserEvent, View } from 'ol'
import { FeatureLike } from 'ol/Feature'
import { boundingExtent } from 'ol/extent'
import { Point } from 'ol/geom'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import 'ol/ol.css'
import { fromLonLat, toLonLat } from 'ol/proj'
import VectorSource from 'ol/source/Vector'
import { Circle as CircleStyle, Fill, Icon, Stroke, Style } from 'ol/style'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import { source as baseMapSource } from '@/features/fireWeather/components/maps/constants'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import activeSpot from '@/features/smurfi/components/map/styles/activeSpot.svg'
import pendingSpot from '@/features/smurfi/components/map/styles/newSpotRequest.svg'
import pausedSpot from '@/features/smurfi/components/map/styles/onHoldSpot.svg'

interface SpotRequestLocation {
  latitude: number
  longitude: number
}

interface SpotRequestLocationMapProps {
  value: SpotRequestLocation | null
  onChange: (value: SpotRequestLocation | null) => void
  existingSpotRequests: SpotRequestOutput[]
}

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))
const statusToPath: Partial<Record<SpotRequestStatus, string>> = {
  [SpotRequestStatus.REQUESTED]: pendingSpot,
  [SpotRequestStatus.STARTED]: activeSpot,
  [SpotRequestStatus.SUSPENDED]: pausedSpot
}

const markerStyle = new Style({
  image: new CircleStyle({
    radius: 8,
    fill: new Fill({ color: '#d32f2f' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 })
  })
})

const existingSpotStyle = (feature: FeatureLike) => {
  const status = feature.get('status') as SpotRequestStatus
  const iconPath = statusToPath[status]

  if (!iconPath) {
    return undefined
  }

  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      src: iconPath
    })
  })
}

const SpotRequestLocationMap: React.FC<SpotRequestLocationMapProps> = ({ value, onChange, existingSpotRequests }) => {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const featureSourceRef = useRef(new VectorSource<Feature<Point>>())
  const existingSpotsSourceRef = useRef(new VectorSource<Feature<Point>>())
  const onChangeRef = useRef(onChange)

  useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  useEffect(() => {
    if (!mapRef.current) {
      return
    }

    const featureLayer = new VectorLayer({
      source: featureSourceRef.current,
      style: markerStyle,
      zIndex: 50
    })
    const existingSpotsLayer = new VectorLayer({
      source: existingSpotsSourceRef.current,
      style: existingSpotStyle,
      zIndex: 40
    })

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        existingSpotsLayer,
        featureLayer
      ],
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })

    mapObject.getView().fit(bcExtent, { padding: [30, 30, 30, 30] })

    mapObject.on('singleclick', (event: MapBrowserEvent<UIEvent>) => {
      const [longitude, latitude] = toLonLat(event.coordinate)
      onChangeRef.current({
        latitude: Number(latitude.toFixed(6)),
        longitude: Number(longitude.toFixed(6))
      })
    })

    return () => {
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    featureSourceRef.current.clear()

    if (value) {
      featureSourceRef.current.addFeature(
        new Feature({
          geometry: new Point(fromLonLat([value.longitude, value.latitude]))
        })
      )
    }
  }, [value])

  useEffect(() => {
    existingSpotsSourceRef.current.clear()
    existingSpotsSourceRef.current.addFeatures(
      existingSpotRequests.map(
        spotRequest =>
          new Feature({
            geometry: new Point(fromLonLat([spotRequest.longitude, spotRequest.latitude])),
            status: spotRequest.status
          })
      )
    )
  }, [existingSpotRequests])

  return <Box ref={mapRef} sx={{ width: '100%', height: 520, border: '1px solid', borderColor: 'divider' }} />
}

export default SpotRequestLocationMap
