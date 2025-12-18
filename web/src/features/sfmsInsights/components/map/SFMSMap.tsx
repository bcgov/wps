import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env'
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { Box, CircularProgress } from '@mui/material'
import { ErrorBoundary } from '@sentry/react'
import {
  BASEMAP_LAYER_NAME,
  fuelCOGTiles,
  getFireWeatherRasterLayer,
  FWI_LAYER_NAME,
  getSnowPMTilesLayer,
  SNOW_LAYER_NAME
} from 'features/sfmsInsights/components/map/layerDefinitions'
import RasterTooltip from 'features/sfmsInsights/components/map/RasterTooltip'
import RasterLegend from 'features/sfmsInsights/components/map/RasterLegend'
import { FireWeatherRasterType, RASTER_CONFIG } from 'features/sfmsInsights/components/map/rasterConfig'
import {
  RasterTooltipInteraction,
  RasterTooltipData
} from '@/features/sfmsInsights/components/map/rasterTooltipInteraction'
import { LayerManager, RasterError } from '@/features/sfmsInsights/components/map/layerManager'
import RasterErrorNotification from '@/features/sfmsInsights/components/map/RasterErrorNotification'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { Map, View } from 'ol'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import React, { useEffect, useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { selectToken } from 'app/rootReducer'

const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

interface SFMSMapProps {
  snowDate: DateTime | null
  rasterDate: DateTime
  rasterType?: FireWeatherRasterType
  showSnow?: boolean
}

const SFMSMap = ({ snowDate, rasterDate, rasterType = 'fwi', showSnow = true }: SFMSMapProps) => {
  const token = useSelector(selectToken)
  const [map, setMap] = useState<Map | null>(null)
  const [rasterTooltipData, setRasterTooltipData] = useState<RasterTooltipData>({
    value: null,
    label: 'FWI',
    pixel: null
  })
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [rasterError, setRasterError] = useState<RasterError | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const rasterLayerManagerRef = useRef<LayerManager | null>(null)
  const snowLayerManagerRef = useRef<LayerManager | null>(null)

  const handleLoadingChange = (isLoading: boolean, error?: RasterError) => {
    setIsLoading(isLoading)
    if (error) {
      setRasterError(error)
    } else if (!isLoading) {
      // Clear error on successful load
      setRasterError(null)
    }
  }

  const handleErrorClose = () => {
    setRasterError(null)
  }

  useEffect(() => {
    if (!mapRef.current) return

    const mapObject = new Map({
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

    // Initialize fire weather raster layer manager
    const rasterLayerManager = new LayerManager({
      onLoadingChange: handleLoadingChange,
      trackLoading: true
    })
    rasterLayerManager.setMap(mapObject)
    rasterLayerManager.updateLayer(getFireWeatherRasterLayer(rasterDate, rasterType, token))
    rasterLayerManagerRef.current = rasterLayerManager

    // Initialize snow layer manager
    const snowLayerManager = new LayerManager({
      layerName: SNOW_LAYER_NAME,
      trackLoading: false // Snow layers load quickly, no need to track
    })
    snowLayerManager.setMap(mapObject)
    snowLayerManager.updateLayer(!isNull(snowDate) && showSnow ? getSnowPMTilesLayer(snowDate) : null)
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
  }, [])

  useEffect(() => {
    if (snowLayerManagerRef.current) {
      snowLayerManagerRef.current.updateLayer(
        !isNull(snowDate) && showSnow ? getSnowPMTilesLayer(snowDate) : null
      )
    }
  }, [snowDate, showSnow])

  useEffect(() => {
    // Clear any existing errors when changing date/type
    setRasterError(null)

    if (rasterLayerManagerRef.current) {
      rasterLayerManagerRef.current.updateLayer(getFireWeatherRasterLayer(rasterDate, rasterType, token))
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
