import { Box } from '@mui/material'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Feature, Map, View } from 'ol'
import { fromLonLat, toLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import 'ol/ol.css'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { boundingExtent } from 'ol/extent'
import VectorLayer from 'ol/layer/Vector'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { Point } from 'ol/geom'
import VectorSource from 'ol/source/Vector'
import SpotPopup from './SpotPopup'
import { FeatureLike } from 'ol/Feature'
import {
  BC_EXTENT,
  CENTER_OF_BC,
  getSmurfiForecastsRoute,
  getSmurfiNewForecastRoute,
  getSmurfiRequestRoute
} from '@wps/utils/constants'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from '@/app/store'
import { fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { useNavigate } from 'react-router-dom'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import {
  CurrentFirePolygonAttributes,
  createCurrentFirePolygonsLayer,
  getCurrentFirePolygonAttributes
} from '@/features/smurfi/components/map/currentFirePolygonsLayer'
import CurrentFirePolygonPopup from '@/features/smurfi/components/map/CurrentFirePolygonPopup'
import SpotMapLayerSwitcher from '@/features/smurfi/components/map/SpotMapLayerSwitcher'
import { createSpotStatusIcon } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { formatFireNumbers } from '@/features/smurfi/utils/spotForecastUtils'

export interface SelectedCoordinates {
  latitude: number
  longitude: number
}

type SpotFeature = {
  lon: number
  lat: number
  status: SpotRequestStatus
  id: string
  spotId: number
  fireNumber: string
  spotRequest: SpotRequestOutput
}

type SpotPopupData = {
  type: 'spot'
  open: boolean
  position: number[]
  lat: number
  lng: number
  status: SpotRequestStatus
  fireNumber: string
  spotId: number
  spotRequest: SpotRequestOutput
}

type FirePopupData = {
  type: 'fire'
  open: boolean
  position: number[]
  attributes: CurrentFirePolygonAttributes
}

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))
const STATUS_FILTER_OPTIONS = [
  SpotRequestStatus.REQUESTED,
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE,
  SpotRequestStatus.ARCHIVED
]

// Tolerance for coordinate matching (in degrees)
const COORDINATE_TOLERANCE = 0.0001

const buildSpotFeature = (spotRequest: SpotRequestOutput): SpotFeature => ({
  lon: spotRequest.current_instance.longitude,
  lat: spotRequest.current_instance.latitude,
  status: spotRequest.status,
  id: String(spotRequest.id),
  spotId: spotRequest.id,
  fireNumber: formatFireNumbers(spotRequest.fire_number),
  spotRequest
})

interface SMURFIMapProps {
  selectedCoordinates?: SelectedCoordinates | null
  spotRequests?: SpotRequestOutput[]
}

const SMURFIMap = ({ selectedCoordinates, spotRequests: propSpotRequests }: SMURFIMapProps) => {
  // hooks
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { spotRequests } = useSelector(selectSmurfi)
  const { isForecaster } = useSpotPermissions(undefined)

  // state
  const [selectedStatuses, setSelectedStatuses] = useState<SpotRequestStatus[]>(STATUS_FILTER_OPTIONS)
  const [selectedFireNumbers, setSelectedFireNumbers] = useState<string[]>([])
  const [currentFiresVisible, setCurrentFiresVisible] = useState(true)
  const [map, setMap] = useState<Map | null>(null)
  const [popupData, setPopupData] = useState<SpotPopupData | FirePopupData | null>(null)

  // refs
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const featureLayerRef = useRef<VectorLayer<VectorSource<Feature<Point>>> | null>(null)
  const currentFirePolygonsLayerRef = useRef<ReturnType<typeof createCurrentFirePolygonsLayer> | null>(null)

  // derived values
  const mapSpotRequests = propSpotRequests ?? spotRequests
  const allFireNumbers = useMemo(
    () => [...new Set(mapSpotRequests.flatMap(sr => sr.fire_number ?? []))].sort((a, b) => a.localeCompare(b)),
    [mapSpotRequests]
  )
  const filteredSpotRequests = useMemo(
    () =>
      mapSpotRequests.filter(
        sr =>
          selectedStatuses.includes(sr.status) &&
          (selectedFireNumbers.length === 0 || sr.fire_number?.some(fn => selectedFireNumbers.includes(fn)))
      ),
    [mapSpotRequests, selectedStatuses, selectedFireNumbers]
  )
  const spotFeatures = useMemo(() => filteredSpotRequests.map(buildSpotFeature), [filteredSpotRequests])

  // handlers
  const handleOpenRequest = (spotRequestId: number) => {
    navigate(getSmurfiRequestRoute(spotRequestId))
  }

  const handleOpenForecasts = (spotRequestId: number) => {
    navigate(getSmurfiForecastsRoute(spotRequestId))
  }

  const handleSubmitForecast = (spotRequest: SpotRequestOutput) => {
    navigate(getSmurfiNewForecastRoute(spotRequest.id))
  }

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

  // styles
  // create highlight style for selected marker
  const createHighlightStyle = () => {
    return new Style({
      image: new CircleStyle({
        radius: 20,
        fill: new Fill({ color: 'rgba(255, 255, 0, 0.3)' }),
        stroke: new Stroke({ color: '#FFD700', width: 3 })
      })
    })
  }

  // create marker style function that checks if feature is selected
  const createMarkerStyle = (selectedCoords: SelectedCoordinates | null | undefined) => {
    return (feature: FeatureLike) => {
      const status = feature.get('status') as SpotRequestStatus
      const featureLon = feature.get('lon') as number
      const featureLat = feature.get('lat') as number

      const baseStyle = new Style({
        image: createSpotStatusIcon(status)
      })

      // check if this feature is selected
      if (
        selectedCoords &&
        Math.abs(featureLon - selectedCoords.longitude) < COORDINATE_TOLERANCE &&
        Math.abs(featureLat - selectedCoords.latitude) < COORDINATE_TOLERANCE
      ) {
        // return both highlight and base style for selected marker
        return [createHighlightStyle(), baseStyle]
      }

      return baseStyle
    }
  }

  // effects
  useEffect(() => {
    if (propSpotRequests === undefined) {
      dispatch(fetchSpotRequests())
    }
  }, [dispatch, propSpotRequests])

  useEffect(() => {
    if (!mapRef.current) return

    const featureSource = new VectorSource<Feature<Point>>({
      features: []
    })
    const featureLayer = new VectorLayer({
      source: featureSource,
      style: createMarkerStyle(null),
      zIndex: 50
    })
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer()
    featureLayerRef.current = featureLayer
    currentFirePolygonsLayerRef.current = currentFirePolygonsLayer

    const mapObject = new Map({
      target: mapRef.current,
      layers: [currentFirePolygonsLayer, featureLayer],
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

    // add popup overlay
    const overlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: true,
      offset: [0, -10],
      autoPan: {
        margin: 24,
        animation: {
          duration: 250
        }
      }
    })
    mapObject.addOverlay(overlay)

    // add click handler
    mapObject.on('click', event => {
      const feature = mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
        layer === featureLayer ? f : undefined
      )
      if (feature) {
        const coord = event.coordinate
        const [lng, lat] = toLonLat(coord)
        overlay.setPosition(coord)
        setPopupData({
          type: 'spot',
          open: true,
          position: coord,
          lat,
          lng,
          status: feature.get('status') as SpotRequestStatus,
          fireNumber: feature.get('fireNumber'),
          spotId: feature.get('spotId') as number,
          spotRequest: feature.get('spotRequest') as SpotRequestOutput
        })
        return
      }

      if (currentFirePolygonsLayer.getVisible()) {
        const fireFeature = mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
          layer === currentFirePolygonsLayer ? f : undefined
        )
        if (fireFeature) {
          overlay.setPosition(event.coordinate)
          setPopupData({
            type: 'fire',
            open: true,
            position: event.coordinate,
            attributes: getCurrentFirePolygonAttributes(fireFeature)
          })
          return
        }
      }

      overlay.setPosition(undefined)
      setPopupData(null)
    })

    setMap(mapObject)

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      currentFirePolygonsLayerRef.current = null
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    currentFirePolygonsLayerRef.current?.setVisible(currentFiresVisible)
  }, [currentFiresVisible])

  useEffect(() => {
    if (!currentFiresVisible) {
      setPopupData(current => (current?.type === 'fire' ? null : current))
    }
  }, [currentFiresVisible])

  useEffect(() => {
    const featureSource = featureLayerRef.current?.getSource()
    if (!featureSource) {
      return
    }

    const markers = spotFeatures.map(
      spotFeature =>
        new Feature({
          geometry: new Point(fromLonLat([spotFeature.lon, spotFeature.lat])),
          id: spotFeature.id,
          spotId: spotFeature.spotId,
          status: spotFeature.status,
          fireNumber: spotFeature.fireNumber,
          spotRequest: spotFeature.spotRequest,
          lon: spotFeature.lon,
          lat: spotFeature.lat
        })
    )

    featureSource.clear()
    featureSource.addFeatures(markers)
  }, [spotFeatures])

  useEffect(() => {
    if (popupData?.type !== 'spot') return
    const statusFiltered = !selectedStatuses.includes(popupData.status)
    const fireNumberFiltered =
      selectedFireNumbers.length > 0 && !popupData.spotRequest.fire_number?.some(fn => selectedFireNumbers.includes(fn))
    if (statusFiltered || fireNumberFiltered) {
      setPopupData(null)
    }
  }, [popupData, selectedStatuses, selectedFireNumbers])

  // update marker styles when selectedCoordinates changes
  useEffect(() => {
    if (featureLayerRef.current) {
      featureLayerRef.current.setStyle(createMarkerStyle(selectedCoordinates))

      // if coordinates are selected, pan to them
      if (selectedCoordinates && map) {
        const coord = fromLonLat([selectedCoordinates.longitude, selectedCoordinates.latitude])
        map.getView().animate({
          center: coord,
          duration: 500
        })
      }
    }
  }, [selectedCoordinates, map])

  return (
    <MapContext.Provider value={map}>
      <Box sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 0, flex: 1 }}>
        <Box ref={mapRef} data-testid={'smurfi-map'} sx={{ width: '100%', height: '100%' }} />
        <SpotMapLayerSwitcher
          statusOptions={STATUS_FILTER_OPTIONS}
          selectedStatuses={selectedStatuses}
          currentFiresVisible={currentFiresVisible}
          allFireNumbers={allFireNumbers}
          selectedFireNumbers={selectedFireNumbers}
          onStatusChange={handleStatusFilterChange}
          onAllStatusesChange={handleAllStatusesChange}
          onCurrentFiresVisibleChange={setCurrentFiresVisible}
          onFireNumbersChange={setSelectedFireNumbers}
        />
        <div
          ref={popupRef}
          className="ol-popup"
          style={{ display: popupData?.open ? 'block' : 'none', pointerEvents: 'auto' }}
        >
          {popupData?.type === 'spot' && (
            <SpotPopup
              lat={popupData.lat}
              lng={popupData.lng}
              status={popupData.status}
              fireNumber={popupData.fireNumber}
              spotId={popupData.spotId}
              spotRequest={popupData.spotRequest}
              canSubmitForecast={isForecaster}
              onOpenRequest={handleOpenRequest}
              onOpenForecast={handleOpenForecasts}
              onSubmitForecast={handleSubmitForecast}
            />
          )}
          {popupData?.type === 'fire' && (
            <CurrentFirePolygonPopup attributes={popupData.attributes} onClose={() => setPopupData(null)} />
          )}
        </div>
      </Box>
    </MapContext.Provider>
  )
}

export default SMURFIMap
