import { Box, Checkbox, FormControlLabel, FormGroup, Paper, Typography } from '@mui/material'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Feature, Map, View } from 'ol'
import { fromLonLat, toLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import 'ol/ol.css'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { boundingExtent } from 'ol/extent'
import VectorLayer from 'ol/layer/Vector'
import { Circle as CircleStyle, Fill, Icon, Stroke, Style } from 'ol/style'
import { Point } from 'ol/geom'
import VectorSource from 'ol/source/Vector'
import SpotPopup, { statusToPath } from './SpotPopup'
import { FeatureLike } from 'ol/Feature'
import { BC_EXTENT, CENTER_OF_BC, SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'
import { BC_EXTENT, CENTER_OF_BC, SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from '@/app/store'
import { fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { useNavigate } from 'react-router-dom'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'

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
const formatFireNumbers = (fireNumbers: string[] | null | undefined) => fireNumbers?.join(', ') ?? ''

const buildSpotFeature = (spotRequest: SpotRequestOutput): SpotFeature => ({
  lon: spotRequest.longitude,
  lat: spotRequest.latitude,
  status: spotRequest.status,
  id: String(spotRequest.id),
  spotId: spotRequest.id,
  fireNumber: formatFireNumbers(spotRequest.fire_number),
  spotRequest
})

interface SMURFIMapProps {
  selectedCoordinates?: SelectedCoordinates | null
  spotRequests?: SpotRequestOutput[]
  spotRequests?: SpotRequestOutput[]
}

const SMURFIMap = ({ selectedCoordinates, spotRequests: propSpotRequests }: SMURFIMapProps) => {
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { spotRequests } = useSelector(selectSmurfi)
  const { isForecaster } = useSpotPermissions(undefined)
  const mapSpotRequests = propSpotRequests ?? spotRequests
  const [selectedStatuses, setSelectedStatuses] = useState<SpotRequestStatus[]>(STATUS_FILTER_OPTIONS)
  const filteredSpotRequests = useMemo(
    () => mapSpotRequests.filter(spotRequest => selectedStatuses.includes(spotRequest.status)),
    [mapSpotRequests, selectedStatuses]
  )
  const spotFeatures = useMemo(() => filteredSpotRequests.map(buildSpotFeature), [filteredSpotRequests])
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const featureLayerRef = useRef<VectorLayer<VectorSource<Feature<Point>>> | null>(null)
  const [popupData, setPopupData] = useState<{
    open: boolean
    position: number[]
    lat: number
    lng: number
    status: SpotRequestStatus
    fireNumber: string
    spotId: number
    spotRequest: SpotRequestOutput
  } | null>(null)

  const handleOpenForecasts = (spotRequestId: number) => {
    navigate(`${SMURFI_DASHBOARD_ROUTE}/${spotRequestId}/forecasts`)
  }

  const handleSubmitForecast = (spotRequest: SpotRequestOutput) => {
    navigate(`${SMURFI_DASHBOARD_ROUTE}/${spotRequest.id}/forecasts/new`)
  }

  const handleStatusFilterChange = (status: SpotRequestStatus, checked: boolean) => {
    setSelectedStatuses(current =>
      checked ? [...current, status] : current.filter(selectedStatus => selectedStatus !== status)
    )
  }

  const handleAllStatusesChange = (checked: boolean) => {
    setSelectedStatuses(checked ? STATUS_FILTER_OPTIONS : [])
  }

  // Create highlight style for selected marker
  const createHighlightStyle = () => {
    return new Style({
      image: new CircleStyle({
        radius: 20,
        fill: new Fill({ color: 'rgba(255, 255, 0, 0.3)' }),
        stroke: new Stroke({ color: '#FFD700', width: 3 })
      })
    })
  }

  // Create marker style function that checks if feature is selected
  const createMarkerStyle = (selectedCoords: SelectedCoordinates | null | undefined) => {
    return (feature: FeatureLike) => {
      const status = feature.get('status') as SpotRequestStatus
      const featureLon = feature.get('lon') as number
      const featureLat = feature.get('lat') as number

      const baseStyle = new Style({
        image: new Icon({
          anchor: [0.5, 1],
          src: statusToPath[status]
        })
      })

      // Check if this feature is selected
      if (
        selectedCoords &&
        Math.abs(featureLon - selectedCoords.longitude) < COORDINATE_TOLERANCE &&
        Math.abs(featureLat - selectedCoords.latitude) < COORDINATE_TOLERANCE
      ) {
        // Return both highlight and base style for selected marker
        return [createHighlightStyle(), baseStyle]
      }

      return baseStyle
    }
  }

  useEffect(() => {
    if (propSpotRequests === undefined) {
      dispatch(fetchSpotRequests())
    }
  }, [dispatch, propSpotRequests])

  useEffect(() => {
    if (propSpotRequests === undefined) {
      dispatch(fetchSpotRequests())
    }
  }, [dispatch, propSpotRequests])

  useEffect(() => {
    if (!mapRef.current) return

    const featureSource = new VectorSource<Feature<Point>>({
      features: []
    const featureSource = new VectorSource<Feature<Point>>({
      features: []
    })
    const featureLayer = new VectorLayer({
      source: featureSource,
      style: createMarkerStyle(null),
      zIndex: 50
    })
    featureLayerRef.current = featureLayer

    const mapObject = new Map({
      target: mapRef.current,
      layers: [featureLayer], // known-good baseline
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

    // Add popup overlay
    const overlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: true,
      offset: [0, -10]
    })
    mapObject.addOverlay(overlay)

    // Add click handler
    mapObject.on('click', event => {
      const feature = mapObject.forEachFeatureAtPixel(event.pixel, (f, layer) =>
        layer === featureLayer ? f : undefined
      )
      if (feature) {
        const coord = event.coordinate
        const [lng, lat] = toLonLat(coord)
        overlay.setPosition(coord)
        setPopupData({
          open: true,
          position: coord,
          lat,
          lng,
          status: feature.get('status') as SpotRequestStatus,
          fireNumber: feature.get('fireNumber'),
          spotId: feature.get('spotId') as number,
          spotRequest: feature.get('spotRequest') as SpotRequestOutput
        })
      } else {
        overlay.setPosition(undefined)
        setPopupData(null)
      }
    })

    setMap(mapObject)

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObject.setTarget('')
    }
  }, [])

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
    if (popupData && !selectedStatuses.includes(popupData.status)) {
      setPopupData(null)
    }
  }, [popupData, selectedStatuses])

  // Update marker styles when selectedCoordinates changes
  useEffect(() => {
    if (featureLayerRef.current) {
      featureLayerRef.current.setStyle(createMarkerStyle(selectedCoordinates))

      // If coordinates are selected, pan to them
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
        <Paper
          elevation={3}
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            zIndex: 2,
            p: 1.5,
            maxWidth: 240
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Status
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={
                <Checkbox
                  size="small"
                  checked={selectedStatuses.length === STATUS_FILTER_OPTIONS.length}
                  indeterminate={selectedStatuses.length > 0 && selectedStatuses.length < STATUS_FILTER_OPTIONS.length}
                  onChange={event => handleAllStatusesChange(event.target.checked)}
                />
              }
              label="All"
            />
            {STATUS_FILTER_OPTIONS.map(status => (
              <FormControlLabel
                key={status}
                control={
                  <Checkbox
                    size="small"
                    checked={selectedStatuses.includes(status)}
                    onChange={event => handleStatusFilterChange(status, event.target.checked)}
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      component="img"
                      src={statusToPath[status]}
                      alt=""
                      sx={{ width: 18, height: 18, objectFit: 'contain' }}
                    />
                    <Typography variant="body2">{status}</Typography>
                  </Box>
                }
              />
            ))}
          </FormGroup>
        </Paper>
        <div
          ref={popupRef}
          className="ol-popup"
          style={{ display: popupData?.open ? 'block' : 'none', pointerEvents: 'auto' }}
        >
          {popupData && (
            <SpotPopup
              lat={popupData.lat}
              lng={popupData.lng}
              status={popupData.status}
              fireNumber={popupData.fireNumber}
              spotId={popupData.spotId}
              spotRequest={popupData.spotRequest}
              canSubmitForecast={isForecaster}
              onOpenForecast={handleOpenForecasts}
              onSubmitForecast={handleSubmitForecast}
            />
          )}
        </div>
      </Box>
    </MapContext.Provider>
  )
}

export default SMURFIMap
