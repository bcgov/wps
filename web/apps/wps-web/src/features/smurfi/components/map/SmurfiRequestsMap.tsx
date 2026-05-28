import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import { BC_EXTENT } from '@wps/utils/constants'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { SpotRequestInstanceOutput, SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Box } from '@mui/material'
import { boundingExtent } from 'ol/extent'
import { Feature, Map, View } from 'ol'
import { fromLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import { Style } from 'ol/style'
import { Point } from 'ol/geom'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import 'ol/ol.css'
import { useEffect, useRef, useState } from 'react'
import {
  CurrentFireAttributes,
  createCurrentFirePointsLayer,
  createCurrentFirePolygonsLayer
} from '@/features/currentFires/map/currentFireLayers'
import { CurrentFiresClickInteraction } from '@/features/currentFires/map/CurrentFiresClickInteraction'
import CurrentFirePolygonPopup from '@/features/smurfi/components/map/CurrentFirePolygonPopup'
import { createSpotStatusIcon } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { panMapToFitElement } from '@/features/map/mapPopupUtils'
import { getVisibleCurrentFireStatusDefaults } from '@/features/currentFires/map/layerVisibility'

interface SmurfiRequestsMapProps {
  spotRequest: SpotRequestOutput
  spotRequestInstance?: SpotRequestInstanceOutput
}

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const getMarkerStyle = (status: SpotRequestStatus) =>
  new Style({
    image: createSpotStatusIcon(status)
  })

const SmurfiRequestsMap = ({ spotRequest, spotRequestInstance }: SmurfiRequestsMapProps) => {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const mapObjectRef = useRef<Map | null>(null)
  const [firePopupAttributes, setFirePopupAttributes] = useState<CurrentFireAttributes | null>(null)
  const spotInstance = spotRequestInstance ?? spotRequest.current_instance

  useEffect(() => {
    if (!mapRef.current) return

    const coord = fromLonLat([Number(spotInstance.longitude), Number(spotInstance.latitude)])

    const marker = new Feature({ geometry: new Point(coord) })
    marker.setStyle(getMarkerStyle(spotRequest.status as SpotRequestStatus))

    const vectorLayer = new VectorLayer({
      source: new VectorSource({ features: [marker] }),
      zIndex: 50
    })
    const visibleCurrentFireStatuses = getVisibleCurrentFireStatusDefaults()
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer(visibleCurrentFireStatuses)
    const currentFirePointsLayer = createCurrentFirePointsLayer(visibleCurrentFireStatuses)

    const mapObject = new Map({
      target: mapRef.current,
      layers: [currentFirePolygonsLayer, currentFirePointsLayer, vectorLayer],
      view: new View({
        center: coord,
        zoom: 10
      })
    })

    const overlay = new Overlay({
      element: popupRef.current!,
      positioning: 'bottom-center',
      stopEvent: true,
      offset: [0, -10]
    })
    mapObject.addOverlay(overlay)
    mapObjectRef.current = mapObject

    const currentFiresClickInteraction = new CurrentFiresClickInteraction({
      currentFirePointsLayer,
      currentFirePolygonsLayer,
      onFireClick: ({ attributes, coordinate }) => {
        overlay.setPosition(coordinate)
        setFirePopupAttributes(attributes)
      },
      onMapMiss: () => {
        overlay.setPosition(undefined)
        setFirePopupAttributes(null)
      }
    })
    mapObject.addInteraction(currentFiresClickInteraction)

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    mapObject.getView().animate({ center: coord, zoom: 10, duration: 0 })

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObjectRef.current = null
      mapObject.removeInteraction(currentFiresClickInteraction)
      mapObject.setTarget('')
    }
  }, [spotInstance.latitude, spotInstance.longitude, spotRequest.status])

  useEffect(() => {
    if (mapObjectRef.current && firePopupAttributes) {
      panMapToFitElement(mapObjectRef.current, popupRef.current)
    }
  }, [firePopupAttributes])

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 300 }}>
      <Box ref={mapRef} sx={{ width: '100%', height: '100%' }} />
      <div
        ref={popupRef}
        className="ol-popup"
        style={{ display: firePopupAttributes ? 'block' : 'none', pointerEvents: 'auto' }}
      >
        {firePopupAttributes && (
          <CurrentFirePolygonPopup attributes={firePopupAttributes} onClose={() => setFirePopupAttributes(null)} />
        )}
      </div>
    </Box>
  )
}

export default SmurfiRequestsMap
