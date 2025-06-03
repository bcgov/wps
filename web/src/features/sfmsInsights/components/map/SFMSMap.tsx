import React, { useEffect, useRef, useState } from 'react'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Map, View } from 'ol'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import { Box } from '@mui/material'
import { ErrorBoundary } from '@sentry/react'
import {
  basemapLayer,
  fuelCOGTiles,
  getSnowPMTilesLayer,
  SNOW_LAYER_NAME
} from 'features/sfmsInsights/components/map/layerDefinitions'
import { DateTime } from 'luxon'
import { isNull } from 'lodash'

const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

interface SFMSMapProps {
  snowDate: DateTime | null
}

const SFMSMap = ({ snowDate }: SFMSMapProps) => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>

  const removeLayerByName = (map: Map, layerName: string) => {
    const layer = map
      .getLayers()
      .getArray()
      .find(l => l.getProperties()?.name === layerName)
    if (layer) {
      map.removeLayer(layer)
    }
  }

  useEffect(() => {
    if (!mapRef.current) return

    const mapObject = new Map({
      target: mapRef.current,
      layers: [basemapLayer, fuelCOGTiles],
      controls: defaultControls(),
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    setMap(mapObject)

    return () => {
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    if (!map) {
      return
    }
    removeLayerByName(map, SNOW_LAYER_NAME)
    if (!isNull(snowDate)) {
      map.addLayer(getSnowPMTilesLayer(snowDate))
    }
  }, [snowDate])

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box
          ref={mapRef}
          data-testid={'sfms-map'}
          sx={{
            width: '100%',
            height: '100%'
          }}
        ></Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default SFMSMap
