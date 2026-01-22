import { Box, Dialog, DialogContent, DialogTitle, IconButton, Typography } from '@mui/material'
import React, { useEffect, useRef, useState } from 'react'
import { Feature, Map, View } from 'ol'
import { fromLonLat, toLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import 'ol/ol.css'
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { boundingExtent } from 'ol/extent'
import VectorLayer from 'ol/layer/Vector'
import { Circle as CircleStyle, Fill, Icon, Stroke, Style } from 'ol/style'
import { Geometry, Point } from 'ol/geom'
import VectorSource from 'ol/source/Vector'
import SpotPopup, { statusToPath } from './SpotPopup'
import { FeatureLike } from 'ol/Feature'
import CloseIcon from '@mui/icons-material/Close'
import SpotForecastForm from '@/features/smurfi/components/forecast_form/SpotForecastForm'

export interface SelectedCoordinates {
  latitude: number
  longitude: number
}

type SpotRequestStatus = 'ACTIVE' | 'COMPLETE' | 'PENDING' | 'PAUSED'

type SpotFeature = {
  lon: number
  lat: number
  status: SpotRequestStatus
  id: string
  fireNumber: string
  fireCentre?: string
}

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const mockFeatures: SpotFeature[] = [
  {
    lon: -125.0313,
    lat: 49.6188,
    status: 'PENDING' as SpotRequestStatus,
    id: '1',
    fireNumber: 'V0800168',
    fireCentre: 'Coastal'
  },
  {
    lon: -122.7497,
    lat: 53.9171,
    status: 'ACTIVE' as SpotRequestStatus,
    id: '2',
    fireNumber: 'G0700234',
    fireCentre: 'Prince George'
  },
  {
    lon: -122.7497,
    lat: 50.9171,
    status: 'PAUSED' as SpotRequestStatus,
    id: '125',
    fireNumber: 'K0300789',
    fireCentre: 'Kamloops'
  },
  {
    lon: -125.7497,
    lat: 54.9171,
    status: 'COMPLETE' as SpotRequestStatus,
    id: '126',
    fireNumber: 'C092346',
    fireCentre: 'Cariboo'
  },
  {
    lon: -125.7497,
    lat: 50.9171,
    status: 'COMPLETE' as SpotRequestStatus,
    id: '127',
    fireNumber: 'C092347',
    fireCentre: 'Southeast'
  }
]

// Tolerance for coordinate matching (in degrees)
const COORDINATE_TOLERANCE = 0.0001

interface SMURFIMapProps {
  selectedCoordinates?: SelectedCoordinates | null
}

const SMURFIMap = ({ selectedCoordinates }: SMURFIMapProps) => {
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
  } | null>(null)
  const [forecastModalOpen, setForecastModalOpen] = useState(false)
  const [selectedFireNumber, setSelectedFireNumber] = useState<string>('')
  const [selectedSpotCoords, setSelectedSpotCoords] = useState<{ lat: number; lng: number } | null>(null)

  const handleOpenForecastModal = (fireNumber: string, lat?: number, lng?: number) => {
    setSelectedFireNumber(fireNumber)
    if (lat !== undefined && lng !== undefined) {
      setSelectedSpotCoords({ lat, lng })
    }
    setForecastModalOpen(true)
  }

  const handleCloseForecastModal = () => {
    setForecastModalOpen(false)
    setSelectedFireNumber('')
    setSelectedSpotCoords(null)
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
    if (!mapRef.current) return

    const createMarker = (spotFeature: SpotFeature) => {
      return new Feature({
        geometry: new Point(fromLonLat([spotFeature.lon, spotFeature.lat])),
        id: spotFeature.id,
        status: spotFeature.status,
        fireNumber: spotFeature.fireNumber,
        fireCentre: spotFeature.fireCentre,
        lon: spotFeature.lon,
        lat: spotFeature.lat
      })
    }

    const mockMarkers = mockFeatures.map(feat => createMarker(feat))

    const featureSource = new VectorSource({
      features: mockMarkers
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
          fireNumber: feature.get('fireNumber')
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
              onOpenForecast={handleOpenForecastModal}
            />
          )}
        </div>
      </Box>

      {/* Forecast Modal - rendered outside the overlay */}
      <Dialog
        open={forecastModalOpen}
        onClose={handleCloseForecastModal}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Spot Forecast - {selectedFireNumber}</Typography>
          <IconButton aria-label="close" onClick={handleCloseForecastModal} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <SpotForecastForm
            readOnly={true}
            fireId={selectedFireNumber}
            latitude={selectedSpotCoords?.lat}
            longitude={selectedSpotCoords?.lng}
          />
        </DialogContent>
      </Dialog>
    </MapContext.Provider>
  )
}

export default SMURFIMap
