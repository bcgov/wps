import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Map, View } from 'ol'
import { PMTilesVectorSource } from 'ol-pmtiles'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import { PMTILES_BUCKET } from 'utils/env'

import React, { useEffect, useRef, useState } from 'react'

import { styleFuelGrid } from '@/features/psuInsights/components/map/psuFeatureStylers'
import { Box } from '@mui/material'
import { ErrorBoundary } from '@sentry/react'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import TileLayer from 'ol/layer/Tile'
import VectorTileLayer from 'ol/layer/VectorTile'

const MapContext = React.createContext<Map | null>(null)

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const PSUMap = () => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>

  const fuelGridVectorSource = new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fuel/fbp2024.pmtiles`
  })

  const [fuelGridVTL] = useState(
    new VectorTileLayer({
      source: fuelGridVectorSource,
      style: styleFuelGrid(),
      zIndex: 51,
      opacity: 0.6
    })
  )

  useEffect(() => {
    if (!mapRef.current) return

    const mapObject = new Map({
      target: mapRef.current,
      layers: [new TileLayer({ source: baseMapSource }), fuelGridVTL],
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

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box
          ref={mapRef}
          data-testid={'psu-map'}
          sx={{
            width: '100%',
            height: '100%'
          }}
        ></Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default PSUMap
