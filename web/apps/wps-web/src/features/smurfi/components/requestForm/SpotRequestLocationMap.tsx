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
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import { source as baseMapSource } from '@/features/fireWeather/components/maps/constants'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import {
  createCurrentFirePointsLayer,
  createCurrentFirePolygonsLayer
} from '@/features/currentFires/map/currentFireLayers'
import { CurrentFireLayerController } from '@/features/currentFires/map/currentFireLayerController'
import SpotMapLayerSwitcher from '@/features/smurfi/components/map/SpotMapLayerSwitcher'
import { createSpotStatusIcon } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { CurrentFireStatus, getVisibleCurrentFireStatusDefaults } from '@/features/currentFires/map/layerVisibility'
import { getSpotRequestDisplayLocation } from '@/features/smurfi/utils/spotForecastUtils'

interface SpotRequestLocation {
  latitude: number
  longitude: number
}

interface SpotRequestLocationMapProps {
  value: SpotRequestLocation | null
  onChange: (value: SpotRequestLocation | null) => void
  existingSpotRequests: SpotRequestOutput[]
  focusOnValue?: boolean
}

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))
const STATUS_FILTER_OPTIONS = [SpotRequestStatus.REQUESTED, SpotRequestStatus.STARTED, SpotRequestStatus.SUSPENDED]

const markerStyle = new Style({
  image: new CircleStyle({
    radius: 8,
    fill: new Fill({ color: '#053662' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 })
  })
})

const existingSpotStyle = (feature: FeatureLike) => {
  const status = feature.get('status') as SpotRequestStatus

  return new Style({
    image: createSpotStatusIcon(status)
  })
}

const SpotRequestLocationMap: React.FC<SpotRequestLocationMapProps> = ({
  value,
  onChange,
  existingSpotRequests,
  focusOnValue = false
}) => {
  // refs
  const mapRef = useRef<HTMLDivElement | null>(null)
  const mapObjectRef = useRef<Map | null>(null)
  const hasFocusedValueRef = useRef(false)
  const featureSourceRef = useRef(new VectorSource<Feature<Point>>())
  const existingSpotsSourceRef = useRef(new VectorSource<Feature<Point>>())
  const currentFireLayerControllerRef = useRef<CurrentFireLayerController | null>(null)
  const onChangeRef = useRef(onChange)

  // state
  const [selectedStatuses, setSelectedStatuses] = useState<SpotRequestStatus[]>(STATUS_FILTER_OPTIONS)
  const [currentFiresVisible, setCurrentFiresVisible] = useState(true)
  const [selectedCurrentFireStatuses, setSelectedCurrentFireStatuses] = useState<CurrentFireStatus[]>(
    getVisibleCurrentFireStatusDefaults
  )

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

  const handleCurrentFireStatusChange = (status: CurrentFireStatus, checked: boolean) => {
    setSelectedCurrentFireStatuses(current => {
      if (!checked) {
        return current.filter(selectedStatus => selectedStatus !== status)
      }

      return current.includes(status) ? current : [...current, status]
    })
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
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer(selectedCurrentFireStatuses)
    const currentFirePointsLayer = createCurrentFirePointsLayer(selectedCurrentFireStatuses)
    currentFireLayerControllerRef.current = new CurrentFireLayerController({
      pointsLayer: currentFirePointsLayer,
      polygonsLayer: currentFirePolygonsLayer
    })

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        currentFirePolygonsLayer,
        currentFirePointsLayer,
        existingSpotsLayer,
        featureLayer
      ],
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })

    mapObjectRef.current = mapObject
    if (focusOnValue && value) {
      mapObject.getView().setCenter(fromLonLat([value.longitude, value.latitude]))
      mapObject.getView().setZoom(12)
      hasFocusedValueRef.current = true
    } else {
      mapObject.getView().fit(bcExtent, { padding: [30, 30, 30, 30] })
    }

    mapObject.on('singleclick', (event: MapBrowserEvent<UIEvent>) => {
      const [longitude, latitude] = toLonLat(event.coordinate)
      onChangeRef.current({
        latitude: Number(latitude.toFixed(6)),
        longitude: Number(longitude.toFixed(6))
      })
    })

    return () => {
      currentFireLayerControllerRef.current = null
      mapObjectRef.current = null
      hasFocusedValueRef.current = false
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    if (!focusOnValue || !value || hasFocusedValueRef.current) {
      return
    }

    const mapObject = mapObjectRef.current
    if (!mapObject) {
      return
    }

    mapObject.getView().setCenter(fromLonLat([value.longitude, value.latitude]))
    mapObject.getView().setZoom(12)
    hasFocusedValueRef.current = true
  }, [focusOnValue, value])

  useEffect(() => {
    currentFireLayerControllerRef.current?.setVisible(currentFiresVisible)
  }, [currentFiresVisible])

  useEffect(() => {
    currentFireLayerControllerRef.current?.setStatuses(selectedCurrentFireStatuses)
  }, [selectedCurrentFireStatuses])

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
        .map(spotRequest => {
          const { instance } = getSpotRequestDisplayLocation(spotRequest)
          return new Feature({
            geometry: new Point(fromLonLat([instance.longitude, instance.latitude])),
            status: spotRequest.status
          })
        })
    )
  }, [existingSpotRequests, selectedStatuses])

  return (
    <Box sx={{ position: 'relative', width: '100%', height: 520, border: '1px solid', borderColor: 'divider' }}>
      <Box ref={mapRef} sx={{ width: '100%', height: '100%' }} />
      <SpotMapLayerSwitcher
        selectedStatuses={selectedStatuses}
        currentFiresVisible={currentFiresVisible}
        selectedCurrentFireStatuses={selectedCurrentFireStatuses}
        onStatusChange={handleStatusFilterChange}
        onAllStatusesChange={handleAllStatusesChange}
        onCurrentFiresVisibleChange={setCurrentFiresVisible}
        onCurrentFireStatusChange={handleCurrentFireStatusChange}
      />
    </Box>
  )
}

export default SpotRequestLocationMap
