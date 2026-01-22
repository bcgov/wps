import { Box } from '@mui/material'
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
import { Icon, Style } from 'ol/style'
import { Geometry, Point } from 'ol/geom'
import VectorSource from 'ol/source/Vector'
import activeSpot from './styles/activeSpot.svg'
import SpotPopup from './SpotPopup'

type SpotRequestStatus = 'ACTIVE' | 'COMPLETE' | 'PENDING' | 'PAUSED'

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const SMURFIMap = () => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const [popupData, setPopupData] = useState<{
    open: boolean
    position: number[]
    lat: number
    lng: number
    status: SpotRequestStatus
  } | null>(null)

  useEffect(() => {
    if (!mapRef.current) return

    const svgMarkup = activeSpot
    const marker = new Feature<Geometry>({
      geometry: new Point(fromLonLat([-123.20205688476564, 49.69664476418803]))
    })
    const featureSourceWithMarker = new VectorSource({
      features: [marker]
    })
    const featureLayer = new VectorLayer({
      source: featureSourceWithMarker,
      style: new Style({
        image: new Icon({
          anchor: [0.5, 1], //center horizontally, bottom vertically
          crossOrigin: 'anonymous',
          src: svgMarkup
        })
      }),
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

    // Add popup overlay
    const overlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: false,
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
        setPopupData({ open: true, position: coord, lat, lng, status: 'ACTIVE' })
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

  return (
    <MapContext.Provider value={map}>
      <Box sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 0, flex: 1 }}>
        <Box ref={mapRef} data-testid={'smurfi-map'} sx={{ width: '100%', height: '100%' }} />
        <div
          ref={popupRef}
          className="ol-popup"
          style={{ display: popupData?.open ? 'block' : 'none', pointerEvents: 'auto' }}
        >
          {popupData && <SpotPopup lat={popupData.lat} lng={popupData.lng} status={popupData.status} />}
        </div>
      </Box>
    </MapContext.Provider>
  )
}

export default SMURFIMap
