import React, { useEffect, useRef, useState } from 'react'
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
import { createCurrentFirePolygonsLayer } from '@/features/smurfi/components/map/currentFirePolygonsLayer'
import SpotMapLayerSwitcher from '@/features/smurfi/components/map/SpotMapLayerSwitcher'
import { statusToPath } from '@/features/smurfi/components/map/SpotPopup'

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
const STATUS_FILTER_OPTIONS = [SpotRequestStatus.REQUESTED, SpotRequestStatus.STARTED, SpotRequestStatus.SUSPENDED]

const markerStyle = new Style({
  image: new CircleStyle({
    radius: 8,
    fill: new Fill({ color: '#d32f2f' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 })
  })
})

const existingSpotStyle = (feature: FeatureLike) => {
  const status = feature.get('status') as SpotRequestStatus

  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      src: statusToPath[status]
    })
  })
}

const SpotRequestLocationMap: React.FC<SpotRequestLocationMapProps> = ({ value, onChange, existingSpotRequests }) => {
  // refs
  const mapRef = useRef<HTMLDivElement | null>(null)
  const featureSourceRef = useRef(new VectorSource<Feature<Point>>())
  const existingSpotsSourceRef = useRef(new VectorSource<Feature<Point>>())
  const currentFirePolygonsLayerRef = useRef<ReturnType<typeof createCurrentFirePolygonsLayer> | null>(null)
  const onChangeRef = useRef(onChange)

  // state
  const [selectedStatuses, setSelectedStatuses] = useState<SpotRequestStatus[]>(STATUS_FILTER_OPTIONS)
  const [currentFiresVisible, setCurrentFiresVisible] = useState(true)

  // handlers
  const handleStatusFilterChange = (status: SpotRequestStatus, checked: boolean) => {
    setSelectedStatuses(current => {
      if (!checked) {
        return current.filter(selectedStatus => selectedStatus !== status)
      }

      return current.includes(status) ? current : [...current, status]
    })
  }

  const handleAllStatusesChange = (checked: boolean) => {
    setSelectedStatuses(checked ? STATUS_FILTER_OPTIONS : [])
  }

  // effects
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
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer()
    currentFirePolygonsLayerRef.current = currentFirePolygonsLayer

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        currentFirePolygonsLayer,
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
      currentFirePolygonsLayerRef.current = null
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    currentFirePolygonsLayerRef.current?.setVisible(currentFiresVisible)
  }, [currentFiresVisible])

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
      existingSpotRequests
        .filter(spotRequest => selectedStatuses.includes(spotRequest.status))
        .map(
          spotRequest =>
            new Feature({
              geometry: new Point(fromLonLat([spotRequest.longitude, spotRequest.latitude])),
              status: spotRequest.status
            })
        )
    )
  }, [existingSpotRequests, selectedStatuses])

  return (
    <Box sx={{ position: 'relative', width: '100%', height: 520, border: '1px solid', borderColor: 'divider' }}>
      <Box ref={mapRef} sx={{ width: '100%', height: '100%' }} />
      <SpotMapLayerSwitcher
        statusOptions={STATUS_FILTER_OPTIONS}
        selectedStatuses={selectedStatuses}
        currentFiresVisible={currentFiresVisible}
        onStatusChange={handleStatusFilterChange}
        onAllStatusesChange={handleAllStatusesChange}
        onCurrentFiresVisibleChange={setCurrentFiresVisible}
      />
    </Box>
  )
}

export default SpotRequestLocationMap
