import { Box } from '@mui/material'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Feature, Map, View } from 'ol'
import { fromLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import 'ol/ol.css'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { boundingExtent } from 'ol/extent'
import VectorLayer from 'ol/layer/Vector'
import { LineString, Point } from 'ol/geom'
import VectorSource from 'ol/source/Vector'
import NewRequestPopup from './NewRequestPopup'
import SpotPopup from './SpotPopup'
import ForecastPopup from './ForecastPopup'
import {
  BC_EXTENT,
  CENTER_OF_BC,
  SMURFI_NEW_REQUEST_ROUTE,
  getSmurfiForecastRoute,
  getSmurfiForecastsRoute,
  getSmurfiNewForecastRoute,
  getSmurfiRequestRoute
} from '@wps/utils/constants'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import {
  SpotForecastOutput,
  SpotRequestCurrentInstanceType,
  SpotRequestOutput,
  SpotRequestStatus
} from '@wps/api/SMURFIAPI'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from '@/app/store'
import { fetchSpotForecasts, fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { useNavigate } from 'react-router-dom'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import {
  createCurrentFirePointsLayer,
  createCurrentFirePolygonsLayer
} from '@/features/currentFires/map/currentFireLayers'
import { CurrentFiresClickInteraction } from '@/features/currentFires/map/CurrentFiresClickInteraction'
import { CurrentFireLayerController } from '@/features/currentFires/map/currentFireLayerController'
import { NewRequestClickInteraction } from '@/features/smurfi/components/map/NewRequestClickInteraction'
import CurrentFirePolygonPopup from '@/features/smurfi/components/map/CurrentFirePolygonPopup'
import SpotMapLayerSwitcher from '@/features/smurfi/components/map/SpotMapLayerSwitcher'
import { panMapToFitElement } from '@/features/map/mapPopupUtils'
import { CurrentFireStatus, getVisibleCurrentFireStatusDefaults } from '@/features/currentFires/map/layerVisibility'
import {
  SPOT_REQUEST_STATUS_OPTIONS,
  getVisibleSpotRequestStatusDefaults
} from '@/features/smurfi/components/map/mapLayerVisibility'
import {
  FirePopupData,
  ForecastPopupData,
  MapClickPopupData,
  SelectedCoordinates,
  SpotPopupData
} from '@/features/smurfi/interfaces'
import { buildSpotFeature, getForecastFeaturesForRequest } from '@/features/smurfi/components/map/spotMapFeatureUtils'
import {
  createForecastMarkerStyle,
  createSpotMarkerStyle,
  forecastLineStyle
} from '@/features/smurfi/components/map/mapFeatureStyles'

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

interface SMURFIMapProps {
  selectedCoordinates?: SelectedCoordinates | null
  spotRequests?: SpotRequestOutput[]
}

const SMURFIMap = ({ selectedCoordinates, spotRequests: propSpotRequests }: SMURFIMapProps) => {
  // hooks
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { spotForecastsByRequestId, spotRequests } = useSelector(selectSmurfi)
  const { isForecaster } = useSpotPermissions(undefined)

  // state
  const [selectedStatuses, setSelectedStatuses] = useState<SpotRequestStatus[]>(getVisibleSpotRequestStatusDefaults)
  const [selectedFireNumbers, setSelectedFireNumbers] = useState<string[]>([])
  const [currentFiresVisible, setCurrentFiresVisible] = useState(true)
  const [selectedCurrentFireStatuses, setSelectedCurrentFireStatuses] = useState<CurrentFireStatus[]>(
    getVisibleCurrentFireStatusDefaults
  )
  const [map, setMap] = useState<Map | null>(null)
  const [popupData, setPopupData] = useState<
    SpotPopupData | ForecastPopupData | FirePopupData | MapClickPopupData | null
  >(null)
  const [expandedSpotRequestId, setExpandedSpotRequestId] = useState<number | null>(null)

  // refs
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const featureLayerRef = useRef<VectorLayer<VectorSource<Feature<Point>>> | null>(null)
  const forecastLayerRef = useRef<VectorLayer<VectorSource<Feature<Point>>> | null>(null)
  const forecastLineLayerRef = useRef<VectorLayer<VectorSource<Feature<LineString>>> | null>(null)
  const currentFireLayerControllerRef = useRef<CurrentFireLayerController | null>(null)
  const currentFiresClickInteractionRef = useRef<CurrentFiresClickInteraction | null>(null)
  const newRequestClickInteractionRef = useRef<NewRequestClickInteraction | null>(null)
  const popupDataRef = useRef<SpotPopupData | ForecastPopupData | FirePopupData | MapClickPopupData | null>(null)
  const spotForecastsByRequestIdRef = useRef(spotForecastsByRequestId)

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
  const expandedSpotRequest = useMemo(
    () => filteredSpotRequests.find(spotRequest => spotRequest.id === expandedSpotRequestId),
    [expandedSpotRequestId, filteredSpotRequests]
  )
  const expandedForecastFeatures = useMemo(() => {
    if (!expandedSpotRequest) {
      return []
    }

    return getForecastFeaturesForRequest(expandedSpotRequest, spotForecastsByRequestId[expandedSpotRequest.id] ?? [])
  }, [expandedSpotRequest, spotForecastsByRequestId])

  // handlers
  const handleOpenRequest = (spotRequestId: number) => {
    navigate(getSmurfiRequestRoute(spotRequestId))
  }

  const handleOpenForecasts = (spotRequestId: number) => {
    navigate(getSmurfiForecastsRoute(spotRequestId))
  }

  const handleOpenForecast = (spotRequestId: number, forecastId: number) => {
    navigate(getSmurfiForecastRoute(spotRequestId, forecastId))
  }

  const handleSubmitForecast = (spotRequestId: number) => {
    navigate(getSmurfiNewForecastRoute(spotRequestId))
  }

  const handleSubmitForecastFromForecastLocation = (spotRequestId: number, sourceForecastId: number) => {
    navigate(getSmurfiNewForecastRoute(spotRequestId), { state: { sourceForecastId } })
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
    setSelectedStatuses(checked ? SPOT_REQUEST_STATUS_OPTIONS : [])
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
    popupDataRef.current = popupData
  }, [popupData])

  useEffect(() => {
    spotForecastsByRequestIdRef.current = spotForecastsByRequestId
  }, [spotForecastsByRequestId])

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
      style: createSpotMarkerStyle(null),
      zIndex: 50
    })
    const forecastSource = new VectorSource<Feature<Point>>({
      features: []
    })
    const forecastLineSource = new VectorSource<Feature<LineString>>({
      features: []
    })
    const forecastLineLayer = new VectorLayer({
      source: forecastLineSource,
      style: forecastLineStyle,
      zIndex: 55
    })
    const forecastLayer = new VectorLayer({
      source: forecastSource,
      style: createForecastMarkerStyle,
      zIndex: 60
    })
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer(selectedCurrentFireStatuses)
    const currentFirePointsLayer = createCurrentFirePointsLayer(selectedCurrentFireStatuses)
    featureLayerRef.current = featureLayer
    forecastLineLayerRef.current = forecastLineLayer
    forecastLayerRef.current = forecastLayer
    currentFireLayerControllerRef.current = new CurrentFireLayerController({
      pointsLayer: currentFirePointsLayer,
      polygonsLayer: currentFirePolygonsLayer
    })

    const mapObject = new Map({
      target: mapRef.current,
      layers: [currentFirePolygonsLayer, currentFirePointsLayer, featureLayer, forecastLineLayer, forecastLayer],
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

    // add popup overlay (shared by all popup types)
    const overlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: true,
      offset: [0, -25]
    })
    mapObject.addOverlay(overlay)

    const newRequestClickInteraction = new NewRequestClickInteraction({
      overlay,
      shouldIgnoreClick: event =>
        Boolean(
          mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
            layer === featureLayer ||
            layer === forecastLayer ||
            layer === currentFirePointsLayer ||
            layer === currentFirePolygonsLayer
              ? f
              : undefined
          )
        ),
      onEmptyClick: ({ lat, lon, coordinate }) => {
        // if any popup is already open, dismiss it rather than opening a new request
        if (popupDataRef.current) {
          newRequestClickInteraction.close()
          setPopupData(null)
          setExpandedSpotRequestId(null)
          return
        }
        setPopupData({ type: 'map', open: true, position: coordinate, lat, lon })
        setExpandedSpotRequestId(null)
      },
      onDismiss: () => {
        setPopupData(null)
      }
    })
    newRequestClickInteractionRef.current = newRequestClickInteraction
    mapObject.addInteraction(newRequestClickInteraction)

    // spot click handler — new request and fire clicks are handled by their interactions
    mapObject.on('click', event => {
      const forecastFeature = mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
        layer === forecastLayer ? f : undefined
      )
      if (forecastFeature) {
        newRequestClickInteraction.close()
        const lng = forecastFeature.get('lon') as number
        const lat = forecastFeature.get('lat') as number
        const coord = fromLonLat([lng, lat])
        overlay.setPosition(coord)
        setPopupData({
          type: 'forecast',
          open: true,
          position: coord,
          lat,
          lng,
          fireNumber: forecastFeature.get('fireNumber'),
          spotId: forecastFeature.get('spotId') as number,
          spotRequest: forecastFeature.get('spotRequest') as SpotRequestOutput,
          forecastCount: forecastFeature.get('forecastCount') as number,
          forecasts: forecastFeature.get('forecasts') as SpotForecastOutput[],
          latestForecast: forecastFeature.get('latestForecast') as SpotForecastOutput
        })
        return
      }

      const feature = mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
        layer === featureLayer ? f : undefined
      )
      if (!feature) return
      newRequestClickInteraction.close()
      const lng = feature.get('lon') as number
      const lat = feature.get('lat') as number
      const coord = fromLonLat([lng, lat])
      const spotId = feature.get('spotId') as number
      overlay.setPosition(coord)
      setExpandedSpotRequestId(spotId)
      if (spotForecastsByRequestIdRef.current[spotId] === undefined) {
        dispatch(fetchSpotForecasts(spotId))
      }
      setPopupData({
        type: 'spot',
        open: true,
        position: coord,
        lat,
        lng,
        locationType: feature.get('locationType') as SpotRequestCurrentInstanceType,
        status: feature.get('status') as SpotRequestStatus,
        fireNumber: feature.get('fireNumber'),
        spotId,
        spotRequest: feature.get('spotRequest') as SpotRequestOutput
      })
    })

    const currentFiresClickInteraction = new CurrentFiresClickInteraction({
      currentFirePointsLayer,
      currentFirePolygonsLayer,
      shouldIgnoreClick: event =>
        Boolean(
          mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
            layer === featureLayer || layer === forecastLayer ? f : undefined
          )
        ),
      onFireClick: ({ attributes, coordinate }) => {
        newRequestClickInteraction.close()
        setExpandedSpotRequestId(null)
        overlay.setPosition(coordinate)
        setPopupData({
          type: 'fire',
          open: true,
          position: coordinate,
          attributes
        })
      },
      onMapMiss: () => {
        // popup dismissal on empty clicks is handled by NewRequestClickInteraction.onEmptyClick
      }
    })
    currentFiresClickInteractionRef.current = currentFiresClickInteraction
    mapObject.addInteraction(currentFiresClickInteraction)

    setMap(mapObject)

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      currentFireLayerControllerRef.current = null
      currentFiresClickInteractionRef.current = null
      newRequestClickInteractionRef.current = null
      forecastLineLayerRef.current = null
      forecastLayerRef.current = null
      mapObject.removeInteraction(newRequestClickInteraction)
      mapObject.removeInteraction(currentFiresClickInteraction)
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    currentFireLayerControllerRef.current?.setVisible(currentFiresVisible)
    currentFiresClickInteractionRef.current?.setActive(currentFiresVisible)
  }, [currentFiresVisible])

  useEffect(() => {
    currentFireLayerControllerRef.current?.setStatuses(selectedCurrentFireStatuses)
  }, [selectedCurrentFireStatuses])

  useEffect(() => {
    if (
      !currentFiresVisible ||
      (popupData?.type === 'fire' &&
        !selectedCurrentFireStatuses.includes(popupData.attributes.fireStatus as CurrentFireStatus))
    ) {
      setPopupData(current => (current?.type === 'fire' ? null : current))
    }
  }, [currentFiresVisible, popupData, selectedCurrentFireStatuses])

  useEffect(() => {
    if (map && popupData?.open) {
      panMapToFitElement(map, popupRef.current)
    }
  }, [map, popupData])

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
          locationType: spotFeature.locationType,
          lon: spotFeature.lon,
          lat: spotFeature.lat
        })
    )

    featureSource.clear()
    featureSource.addFeatures(markers)
  }, [spotFeatures])

  useEffect(() => {
    const forecastLineSource = forecastLineLayerRef.current?.getSource()
    if (!forecastLineSource) {
      return
    }

    forecastLineSource.clear()

    if (!expandedSpotRequest) {
      return
    }

    const requestCoordinate = fromLonLat([
      expandedSpotRequest.request_instance.longitude,
      expandedSpotRequest.request_instance.latitude
    ])
    forecastLineSource.addFeatures(
      expandedForecastFeatures.map(
        forecastFeature =>
          new Feature({
            geometry: new LineString([requestCoordinate, fromLonLat([forecastFeature.lon, forecastFeature.lat])])
          })
      )
    )
  }, [expandedForecastFeatures, expandedSpotRequest])

  useEffect(() => {
    const forecastSource = forecastLayerRef.current?.getSource()
    if (!forecastSource) {
      return
    }

    const markers = expandedForecastFeatures.map(
      forecastFeature =>
        new Feature({
          geometry: new Point(fromLonLat([forecastFeature.lon, forecastFeature.lat])),
          id: forecastFeature.id,
          spotId: forecastFeature.spotId,
          status: forecastFeature.status,
          fireNumber: forecastFeature.fireNumber,
          spotRequest: forecastFeature.spotRequest,
          forecastCount: forecastFeature.forecastCount,
          forecasts: forecastFeature.forecasts,
          latestForecast: forecastFeature.latestForecast,
          lon: forecastFeature.lon,
          lat: forecastFeature.lat
        })
    )

    forecastSource.clear()
    forecastSource.addFeatures(markers)
  }, [expandedForecastFeatures])

  useEffect(() => {
    if (popupData?.type !== 'spot') return
    const statusFiltered = !selectedStatuses.includes(popupData.status)
    const fireNumberFiltered =
      selectedFireNumbers.length > 0 && !popupData.spotRequest.fire_number?.some(fn => selectedFireNumbers.includes(fn))
    if (statusFiltered || fireNumberFiltered) {
      setPopupData(null)
    }
  }, [popupData, selectedStatuses, selectedFireNumbers])

  useEffect(() => {
    if (expandedSpotRequestId === null || expandedSpotRequest) {
      return
    }

    setExpandedSpotRequestId(null)
    setPopupData(current => (current?.type === 'forecast' || current?.type === 'spot' ? null : current))
  }, [expandedSpotRequest, expandedSpotRequestId])

  useEffect(() => {
    if (popupData?.type !== 'forecast') {
      return
    }

    if (
      !expandedForecastFeatures.some(feature =>
        feature.forecasts.some(forecast => forecast.id === popupData.latestForecast.id)
      )
    ) {
      setPopupData(null)
    }
  }, [expandedForecastFeatures, popupData])

  // update marker styles when selectedCoordinates changes
  useEffect(() => {
    if (featureLayerRef.current) {
      featureLayerRef.current.setStyle(createSpotMarkerStyle(selectedCoordinates))

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
          selectedStatuses={selectedStatuses}
          currentFiresVisible={currentFiresVisible}
          selectedCurrentFireStatuses={selectedCurrentFireStatuses}
          allFireNumbers={allFireNumbers}
          selectedFireNumbers={selectedFireNumbers}
          onStatusChange={handleStatusFilterChange}
          onAllStatusesChange={handleAllStatusesChange}
          onCurrentFiresVisibleChange={setCurrentFiresVisible}
          onCurrentFireStatusChange={handleCurrentFireStatusChange}
          onFireNumbersChange={setSelectedFireNumbers}
        />
        <div
          ref={popupRef}
          className="ol-popup"
          style={{ display: popupData?.open ? 'block' : 'none', pointerEvents: 'auto', position: 'relative' }}
        >
          {/* rotated square pointer */}
          <Box
            sx={{
              position: 'absolute',
              bottom: -7,
              left: '50%',
              width: 14,
              height: 14,
              transform: 'translateX(-50%) rotate(45deg)',
              bgcolor: 'white',
              borderBottom: '1px solid #ddd',
              borderRight: '1px solid #ddd',
              pointerEvents: 'none',
              zIndex: 2
            }}
          />
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            {popupData?.type === 'spot' && (
              <SpotPopup
                popupData={popupData}
                canSubmitForecast={isForecaster}
                onOpenRequest={handleOpenRequest}
                onOpenForecast={handleOpenForecasts}
                onSubmitForecast={handleSubmitForecast}
              />
            )}
            {popupData?.type === 'forecast' && (
              <ForecastPopup
                popupData={popupData}
                canSubmitForecast={isForecaster}
                onOpenRequest={handleOpenRequest}
                onOpenForecast={handleOpenForecast}
                onSubmitForecast={handleSubmitForecastFromForecastLocation}
              />
            )}
            {popupData?.type === 'fire' && (
              <CurrentFirePolygonPopup attributes={popupData.attributes} onClose={() => setPopupData(null)} />
            )}
            {popupData?.type === 'map' && (
              <NewRequestPopup
                onConfirm={() => {
                  newRequestClickInteractionRef.current?.close()
                  navigate(SMURFI_NEW_REQUEST_ROUTE, {
                    state: { latitude: popupData.lat, longitude: popupData.lon }
                  })
                }}
                onCancel={() => {
                  newRequestClickInteractionRef.current?.close()
                  setPopupData(null)
                }}
              />
            )}
          </Box>
        </div>
      </Box>
    </MapContext.Provider>
  )
}

export default SMURFIMap
