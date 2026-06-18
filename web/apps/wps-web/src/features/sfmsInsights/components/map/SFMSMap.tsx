import { Box, CircularProgress } from '@mui/material'
import { ErrorBoundary } from '@sentry/react'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@wps/utils/env'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import {
  BASEMAP_LAYER_NAME,
  getRasterLayer,
  getSnowPMTilesLayer
} from 'features/sfmsInsights/components/map/layerDefinitions'
import RasterLegend from 'features/sfmsInsights/components/map/RasterLegend'
import RasterTooltip from 'features/sfmsInsights/components/map/RasterTooltip'
import { RASTER_CONFIG, type RasterType } from 'features/sfmsInsights/components/map/rasterConfig'
import { isNull } from 'lodash'
import type { DateTime } from 'luxon'
import { Map as OlMap, View } from 'ol'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import { LayerManager, type RasterError } from '@/features/sfmsInsights/components/map/layerManager'
import RasterErrorNotification from '@/features/sfmsInsights/components/map/RasterErrorNotification'
import {
  type RasterTooltipData,
  RasterTooltipInteraction
} from '@/features/sfmsInsights/components/map/rasterTooltipInteraction'
import 'ol/ol.css'
import { selectToken } from 'app/rootReducer'
import { fromLonLat } from 'ol/proj'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useSelector } from 'react-redux'

const MapContext = React.createContext<OlMap | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

interface SFMSMapProps {
  snowDate: DateTime | null
  rasterDate: DateTime | null
  rasterType?: RasterType
  showSnow?: boolean
}

const SFMSMap = ({ snowDate, rasterDate, rasterType = 'fwi', showSnow = true }: SFMSMapProps) => {
  const token = useSelector(selectToken)
  const [map, setMap] = useState<OlMap | null>(null)
  const [rasterTooltipData, setRasterTooltipData] = useState<RasterTooltipData>({
    value: null,
    label: 'FWI',
    pixel: null
  })
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [rasterError, setRasterError] = useState<RasterError | null>(null)
  // Initialized to a detached div so the type is non-nullable — React replaces it with the
  // rendered element during commit, which always happens before effects fire.
  const mapRef = useRef<HTMLDivElement>(document.createElement('div'))
  const rasterLayerManagerRef = useRef<LayerManager | null>(null)
  const snowLayerManagerRef = useRef<LayerManager | null>(null)

  const handleLoadingChange = useCallback((isLoading: boolean, error?: RasterError) => {
    setIsLoading(isLoading)
    if (error) {
      setRasterError(error)
    } else if (!isLoading) {
      // Clear error on successful load
      setRasterError(null)
    }
  }, [])

  const handleErrorClose = () => {
    setRasterError(null)
  }

  useEffect(() => {
    const mapObject = new OlMap({
      target: mapRef.current,
      layers: [],
      controls: defaultControls(),
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    setMap(mapObject)

    // Add raster tooltip interaction
    const tooltipInteraction = new RasterTooltipInteraction({
      onTooltipChange: setRasterTooltipData
    })
    mapObject.addInteraction(tooltipInteraction)

    // Initialize layer managers — initial layer load is handled by the effects below
    const rasterLayerManager = new LayerManager({
      onLoadingChange: handleLoadingChange,
      trackLoading: true
    })
    rasterLayerManager.setMap(mapObject)
    rasterLayerManagerRef.current = rasterLayerManager

    const snowLayerManager = new LayerManager({
      trackLoading: false
    })
    snowLayerManager.setMap(mapObject)
    snowLayerManagerRef.current = snowLayerManager

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObject.setTarget('')
    }
  }, [handleLoadingChange])

  useEffect(() => {
    if (snowLayerManagerRef.current) {
      snowLayerManagerRef.current.updateLayer(
        !isNull(snowDate) && showSnow ? getSnowPMTilesLayer(snowDate, token) : null
      )
    }
  }, [snowDate, showSnow, token])

  useEffect(() => {
    // Clear any existing errors when changing date/type
    setRasterError(null)

    if (rasterLayerManagerRef.current) {
      // Only load raster layer if we have a date (for fire weather) or if type is fuel (date-independent)
      if (rasterDate || rasterType === 'fuel') {
        rasterLayerManagerRef.current.updateLayer(getRasterLayer(rasterDate, rasterType, token))
      } else {
        rasterLayerManagerRef.current.updateLayer(null)
      }
    }
  }, [rasterDate, rasterType, token])

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
          <Box
            ref={mapRef}
            data-testid={'sfms-map'}
            sx={{
              width: '100%',
              height: '100%'
            }}
          ></Box>
          <RasterTooltip
            label={rasterTooltipData.label}
            value={rasterTooltipData.value}
            pixelCoords={rasterTooltipData.pixel}
          />
          <RasterLegend rasterType={rasterType} />
          {isLoading && (
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 2000,
                bgcolor: 'rgba(255, 255, 255, 0.9)',
                padding: 3,
                borderRadius: 2,
                boxShadow: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2
              }}
            >
              <CircularProgress />
              <Box sx={{ fontSize: '14px', fontWeight: 'medium' }}>Loading {RASTER_CONFIG[rasterType].label}...</Box>
            </Box>
          )}
          <RasterErrorNotification
            error={rasterError}
            onClose={handleErrorClose}
            rasterLabel={RASTER_CONFIG[rasterType].label}
          />
        </Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default SFMSMap
