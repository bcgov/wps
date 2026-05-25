import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import { BC_EXTENT } from '@wps/utils/constants'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Box } from '@mui/material'
import { boundingExtent } from 'ol/extent'
import { Feature, Map, View } from 'ol'
import { fromLonLat } from 'ol/proj'
import Overlay from 'ol/Overlay'
import { Icon, Style } from 'ol/style'
import { Point } from 'ol/geom'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import 'ol/ol.css'
import { useEffect, useRef, useState } from 'react'
import startedSpot from './styles/activeSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import requestedSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'
import {
  CurrentFirePolygonAttributes,
  createCurrentFirePolygonsLayer,
  getCurrentFirePolygonAttributes
} from '@/features/smurfi/components/map/currentFirePolygonsLayer'
import CurrentFirePolygonPopup from '@/features/smurfi/components/map/CurrentFirePolygonPopup'

interface SmurfiRequestsMapProps {
  spotRequest: SpotRequestOutput
}

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const statusToPath: Record<SpotRequestStatus, string> = {
  [SpotRequestStatus.STARTED]: startedSpot,
  [SpotRequestStatus.COMPLETE]: completeSpot,
  [SpotRequestStatus.REQUESTED]: requestedSpot,
  [SpotRequestStatus.SUSPENDED]: pausedSpot,
  [SpotRequestStatus.ARCHIVED]: completeSpot
}

const getMarkerStyle = (status: SpotRequestStatus) =>
  new Style({
    image: new Icon({
      anchor: [0.5, 1],
      src: statusToPath[status]
    })
  })

const SmurfiRequestsMap = ({ spotRequest }: SmurfiRequestsMapProps) => {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const popupRef = useRef<HTMLDivElement | null>(null)
  const [firePopupAttributes, setFirePopupAttributes] = useState<CurrentFirePolygonAttributes | null>(null)

  useEffect(() => {
    if (!mapRef.current) return

    const coord = fromLonLat([Number(spotRequest.longitude), Number(spotRequest.latitude)])

    const marker = new Feature({ geometry: new Point(coord) })
    marker.setStyle(getMarkerStyle(spotRequest.status as SpotRequestStatus))

    const vectorLayer = new VectorLayer({
      source: new VectorSource({ features: [marker] }),
      zIndex: 50
    })
    const currentFirePolygonsLayer = createCurrentFirePolygonsLayer()

    const mapObject = new Map({
      target: mapRef.current,
      layers: [currentFirePolygonsLayer, vectorLayer],
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

    mapObject.on('click', event => {
      const fireFeature = mapObject.forEachFeatureAtPixel(event.pixel, (feature, layer) =>
        layer === currentFirePolygonsLayer ? feature : undefined
      )
      if (fireFeature) {
        overlay.setPosition(event.coordinate)
        setFirePopupAttributes(getCurrentFirePolygonAttributes(fireFeature))
        return
      }

      overlay.setPosition(undefined)
      setFirePopupAttributes(null)
    })

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    mapObject.getView().animate({ center: coord, zoom: 10, duration: 0 })

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObject.setTarget('')
    }
  }, [spotRequest.latitude, spotRequest.longitude])

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
