import { Box } from '@mui/material'
import React, { useEffect, useRef, useState } from 'react'
import { Feature, Map, View, Overlay } from 'ol'
import { fromLonLat, toLonLat } from 'ol/proj'
import 'ol/ol.css'
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { boundingExtent } from 'ol/extent'
import VectorLayer from 'ol/layer/Vector'
import { Icon, Style } from 'ol/style'
import { Point } from 'ol/geom'
import './styles/styles.css'
import VectorSource from 'ol/source/Vector'
import activeSpot from './styles/activeSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import pendingSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'

type SpotRequestStatus = 'ACTIVE' | 'COMPLETE' | 'PENDING' | 'PAUSED'

type SpotFeature = {
  lon: number
  lat: number
  status: SpotRequestStatus
  id: string
  fireNumber: string
  fireCentre?: string
}

const statusToPath: Record<SpotRequestStatus, string> = {
  ACTIVE: activeSpot,
  COMPLETE: completeSpot,
  PENDING: pendingSpot,
  PAUSED: pausedSpot
}

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const SMURFIMap = () => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const popupContentRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!mapRef.current) return

    const featureSource = new VectorSource({})

    const createMarker = (spotFeature: SpotFeature) => {
      return new Feature({
        geometry: new Point(fromLonLat([spotFeature.lon, spotFeature.lat])),
        id: spotFeature.id,
        status: spotFeature.status,
        fireNumber: spotFeature.fireNumber,
        fireCentre: spotFeature.fireCentre
      })
    }

    const markerStyle = (feature: Feature) => {
      const status = feature.get('status') as SpotRequestStatus

      return new Style({
        image: new Icon({
          anchor: [0.5, 1],
          src: statusToPath[status]
        })
      })
    }

    if (!popupRef.current) return // safety in case the ref hasn't mounted yet when map creates

    const popupOverlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: false,
      offset: [0, -20]
    })

    const generatePopupContent = (feature: Feature): string => {
      const fireNumber = feature.get('fireNumber') ?? '-'
      const status = feature.get('status') ?? 'Status Unknown'
      const fireCentre = feature.get('fireCentre') ?? '-'

      const geometry = feature.getGeometry() as Point
      const [x, y] = geometry.getCoordinates()
      const [lon, lat] = toLonLat([x, y])

      return `
        <div class="spot-popup">
          <div class="spot-popup__header">
            <div class="spot-popup__id">${fireNumber}</div>

            <div class="spot-popup__actions">
              <button class="spot-popup__subscribe">
                <span class="icon">👤</span> Subscribe
              </button>

              <span class="spot-popup__status spot-popup__status--${status.toLowerCase()}">
                ${status}
              </span>
            </div>
          </div>

          <div class="spot-popup__meta">
            <div class="spot-popup__centre">${fireCentre}</div>
            <a
              class="spot-popup__coords"
              href="https://www.google.com/maps?q=${lat},${lon}"
              target="_blank"
              rel="noopener noreferrer"
            >
              ${lat.toFixed(6)}, ${lon.toFixed(6)}
            </a>
          </div>

          <button class="spot-popup__forecast">
            📄 New Spot Forecast (dd/mm/yyyy - 00:00)
          </button>

          <div class="spot-popup__footer">
            <a href="#" class="spot-popup__view-more">VIEW MORE</a>
          </div>
        </div>
      `
    }

    const mockFeatures = [
      {
        lon: -123.202,
        lat: 49.696,
        status: 'ACTIVE' as SpotRequestStatus,
        id: 'spot-1',
        fireNumber: 'V34869',
        fireCentre: 'Coastal Fire Centre'
      },
      {
        lon: -122.36,
        lat: 53.243,
        status: 'PAUSED' as SpotRequestStatus,
        id: 'spot-2',
        fireNumber: 'G81356',
        fireCentre: 'Prince George Fire Centre'
      },
      {
        lon: -119.843,
        lat: 49.998,
        status: 'PENDING' as SpotRequestStatus,
        id: 'spot-3',
        fireNumber: 'V34869',
        fireCentre: 'Kamloops Fire Centre'
      },
      {
        lon: -128.202,
        lat: 51.735,
        status: 'COMPLETE' as SpotRequestStatus,
        id: 'spot-4',
        fireNumber: 'V34869',
        fireCentre: 'Coastal Fire Centre'
      }
    ]
    const mockMarkers = mockFeatures.map(feat => createMarker(feat))

    featureSource.addFeatures(mockMarkers)

    const featureLayer = new VectorLayer({
      source: featureSource,
      style: markerStyle,
      zIndex: 50
    })

    const mapObject = new Map({
      target: mapRef.current,
      layers: [featureLayer], // known-good baseline
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    mapObject.addOverlay(popupOverlay)

    mapObject.on('singleclick', event => {
      const feature = mapObject.forEachFeatureAtPixel(event.pixel, f => f)
      if (!feature) {
        popupOverlay.setPosition(undefined)
        return
      }
      const geometry = feature.getGeometry() as Point
      const coordinates = geometry.getCoordinates()

      popupContentRef.current!.innerHTML = generatePopupContent(feature)

      popupOverlay.setPosition(coordinates)
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

  return (
    <MapContext.Provider value={map}>
      <Box sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 0, flex: 1 }}>
        <Box
          ref={popupRef}
          sx={{
            background: 'white',
            padding: 1,
            borderRadius: 1,
            boxShadow: 3,
            position: 'absolute',
            transform: 'translate(-50%, -100%)',
            pointerEvents: 'auto'
          }}
        >
          <div ref={popupContentRef} />
        </Box>
        <Box ref={mapRef} data-testid={'smurfi-map'} sx={{ width: '100%', height: '100%' }} />
      </Box>
    </MapContext.Provider>
  )
}

export default SMURFIMap
