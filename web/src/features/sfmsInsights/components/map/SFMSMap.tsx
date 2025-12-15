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
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { Map, View } from 'ol'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import WebGLTileLayer from 'ol/layer/WebGLTile'
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
  const [rasterValue, setRasterValue] = useState<number | null>(null)
  const [rasterLabel, setRasterLabel] = useState<string>('FWI')
  const [pixelCoords, setPixelCoords] = useState<[number, number] | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
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
      layers: [],
      controls: defaultControls(),
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    setMap(mapObject)

    const loadBaseMap = async () => {
      const style = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, style, 1, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }

    const loadRasterLayer = async () => {
      const rasterLayer = getFireWeatherRasterLayer(rasterDate, rasterType, token, FWI_LAYER_NAME)
      mapObject.addLayer(rasterLayer)
    }
    loadBaseMap()
    loadRasterLayer()

    return () => {
      mapObject.setTarget('')
    }
  }, [])

  // Add hover listener to get raster pixel values
  useEffect(() => {
    if (!map) return

    const handlePointerMove = (evt: any) => {
      const pixel = map.getEventPixel(evt.originalEvent)
      setPixelCoords([pixel[0], pixel[1]])

      // Find any fire weather raster layer (has a rasterType property)
      const rasterLayer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.rasterType !== undefined) as WebGLTileLayer | undefined

      if (rasterLayer) {
        const data = rasterLayer.getData(pixel) as Float32Array | Uint8Array | null
        const properties = rasterLayer.getProperties()
        const rasterType = properties?.rasterType as FireWeatherRasterType | undefined

        if (data && data.length > 0 && data[0] !== undefined) {
          setRasterValue(Math.round(data[0]))
          setRasterLabel(rasterType ? RASTER_CONFIG[rasterType].label : 'FWI')
        } else {
          setRasterValue(null)
        }
      }
    }

    map.on('pointermove', handlePointerMove)

    return () => {
      map.un('pointermove', handlePointerMove)
    }
  }, [map])

  useEffect(() => {
    if (!map) {
      return
    }
    removeLayerByName(map, SNOW_LAYER_NAME)
    if (!isNull(snowDate) && showSnow) {
      map.addLayer(getSnowPMTilesLayer(snowDate))
    }
  }, [snowDate, showSnow, map])

  useEffect(() => {
    if (!map) {
      return
    }
    removeLayerByName(map, FWI_LAYER_NAME)
    setIsLoading(true)
    const rasterLayer = getFireWeatherRasterLayer(rasterDate, rasterType, token, FWI_LAYER_NAME)

    // Listen for when the source finishes loading
    const source = rasterLayer.getSource()
    if (source) {
      source.on('tileloadend', () => {
        setIsLoading(false)
      })
      source.on('tileloaderror', () => {
        setIsLoading(false)
      })
    }

    map.addLayer(rasterLayer)
  }, [rasterDate, rasterType, map, token])

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
          <RasterTooltip label={rasterLabel} value={rasterValue} pixelCoords={pixelCoords} />
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
        </Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default SFMSMap
