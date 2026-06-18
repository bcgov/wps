import { Box } from '@mui/material'
import { type FireShape, RunType } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { createHillshadeVectorTileLayer, createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { selectFireWeatherStations, selectProvincialSummaryZones, selectRunDates } from 'app/rootReducer'
import Legend from 'features/fba/components/map/Legend'
import {
  createFBAVectorLayers,
  createHFILayer,
  createStationsLayer,
  hfiLayerName,
  setFBASelectionStyles,
  zoneStatusLayerName
} from 'features/fba/components/map/layerDefinitions'
import ScalebarContainer from 'features/fba/components/map/ScaleBarContainer'
import { extentsMap } from 'features/fba/fireCentreExtents'
import { fireZoneExtentsMap } from 'features/fba/fireZoneUnitExtents'
import { cloneDeep, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { Map as OlMap, View } from 'ol'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import ScaleLine from 'ol/control/ScaleLine'
import { boundingExtent } from 'ol/extent'
import type MapBrowserEvent from 'ol/MapBrowserEvent'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import 'ol/ol.css'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL, HILLSHADE_STYLE_URL, HILLSHADE_TILE_URL } from '@wps/utils/env'
import { fromLonLat } from 'ol/proj'
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { MapContext } from '@/features/fba/context/MapContext'

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

export interface FBAMapProps {
  testId?: string
  selectedFireCentre: FireCentre | undefined
  selectedFireShape: FireShape | undefined
  forDate: DateTime
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
  runType: RunType
  zoomSource?: 'fireCentre' | 'fireShape'
  setZoomSource: React.Dispatch<React.SetStateAction<'fireCentre' | 'fireShape' | undefined>>
}

const removeLayerByName = (map: OlMap, layerName: string) => {
  const layer = map
    .getLayers()
    .getArray()
    .find(l => l.getProperties()?.name === layerName)
  if (layer) {
    map.removeLayer(layer)
  }
}

const FBAMap = (props: FBAMapProps) => {
  const { forDate, selectedFireCentre, selectedFireShape, setSelectedFireShape, runType, zoomSource, setZoomSource } =
    props

  // selectors
  const { stations } = useSelector(selectFireWeatherStations)
  const provincialSummaryZones = useSelector(selectProvincialSummaryZones)
  const { mostRecentRunDate } = useSelector(selectRunDates)

  // state
  const [showShapeStatus, setShowShapeStatus] = useState(true)
  const [showHFI, setShowHFI] = useState(() => {
    const stored = localStorage.getItem(hfiLayerName)
    return stored === 'true'
  })
  const [map, setMap] = useState<OlMap | null>(null)

  // refs
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const scaleRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>

  // layers
  const fbaLayers = useMemo(() => createFBAVectorLayers(), [])

  const handleToggleLayer = useCallback(
    (layerName: string, isVisible: boolean) => {
      if (map) {
        const layer = map
          .getLayers()
          .getArray()
          .find(l => l.getProperties()?.name === layerName)

        if (layerName === zoneStatusLayerName) {
          setFBASelectionStyles(
            fbaLayers,
            selectedFireCentre,
            selectedFireShape,
            cloneDeep(provincialSummaryZones),
            isVisible
          )
        } else if (layer) {
          layer.setVisible(isVisible)
        }
      }
    },
    [fbaLayers, map, provincialSummaryZones, selectedFireCentre, selectedFireShape]
  )

  useEffect(() => {
    const hfiLayerEnabled = localStorage.getItem(hfiLayerName)
    setShowHFI(hfiLayerEnabled === 'true')
  }, [])

  useEffect(() => {
    if (!map) return

    const handleMapClick = (event: MapBrowserEvent<UIEvent>) => {
      fbaLayers.fireShapeVTL.getFeatures(event.pixel).then(features => {
        if (!features.length) {
          setSelectedFireShape(undefined)
          return
        }
        const feature = features[0]
        if (!feature) {
          return
        }
        const zonePlacename = `${feature.getProperties().FIRE_ZONE_} - ${feature.getProperties().FIRE_ZON_1}`
        const fireZone: FireShape = {
          fire_shape_id: feature.getProperties().OBJECTID,
          mof_fire_zone_name: zonePlacename,
          mof_fire_centre_name: feature.getProperties().FIRE_CENTR,
          area_sqm: feature.getProperties().Shape_Area
        }
        setZoomSource('fireShape')
        setSelectedFireShape(fireZone)
      })
    }

    map.on('click', handleMapClick)
    return () => {
      map.un('click', handleMapClick)
    }
  }, [fbaLayers.fireShapeVTL, map, setSelectedFireShape, setZoomSource])

  useEffect(() => {
    // zoom to fire center or whole province
    if (!map) return

    if (selectedFireCentre && zoomSource === 'fireCentre') {
      const fireCentreExtent = extentsMap.get(selectedFireCentre.name)
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent, { duration: 400, padding: [50, 50, 50, 50] })
      }
    } else if (!selectedFireCentre && zoomSource !== 'fireShape') {
      // reset map view to full province
      map.getView().fit(bcExtent, { duration: 600, padding: [50, 50, 50, 50] })
    }
  }, [map, selectedFireCentre, zoomSource])

  useEffect(() => {
    // zoom to fire zone
    if (!map) return

    if (selectedFireShape && zoomSource === 'fireShape') {
      const zoneExtent = fireZoneExtentsMap.get(selectedFireShape.fire_shape_id.toString())
      if (!isUndefined(zoneExtent)) {
        map.getView().fit(zoneExtent, { duration: 400, padding: [100, 100, 100, 100], maxZoom: 8 })
      }
    }
  }, [map, selectedFireShape, zoomSource])

  useEffect(() => {
    if (!map) return

    setFBASelectionStyles(
      fbaLayers,
      selectedFireCentre,
      selectedFireShape,
      cloneDeep(provincialSummaryZones),
      showShapeStatus
    )
  }, [fbaLayers, map, provincialSummaryZones, selectedFireCentre, selectedFireShape, showShapeStatus])

  useEffect(() => {
    if (!map) return
    removeLayerByName(map, hfiLayerName)
    if (!isNull(mostRecentRunDate)) {
      // The runDate for forecasts is the mostRecentRunDate. For Actuals, our API expects the runDate to be
      // the same as the forDate.
      const runDate = runType === RunType.FORECAST ? DateTime.fromISO(mostRecentRunDate) : forDate
      map.addLayer(createHFILayer(forDate, runType, runDate, showHFI))
    }
  }, [forDate, map, mostRecentRunDate, runType, showHFI])

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new OlMap({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      }),
      layers: fbaLayers.baseLayers,
      overlays: [],
      controls: defaultControls().extend([new FullScreen()])
    })
    mapObject.setTarget(mapRef.current)

    const scaleBar = new ScaleLine({
      bar: true,
      minWidth: 160,
      steps: 4
    })
    scaleBar.setTarget(scaleRef.current)
    scaleBar.setMap(mapObject)

    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

    setMap(mapObject)

    const loadBaseMap = async () => {
      // Create and add the hillshade layer first so it renders below the vector basemap layer
      const hillshadeStyle = await getStyleJson(HILLSHADE_STYLE_URL)
      const hillshadeLayer = await createHillshadeVectorTileLayer(
        HILLSHADE_TILE_URL,
        hillshadeStyle,
        1,
        BASEMAP_LAYER_NAME
      )
      mapObject.addLayer(hillshadeLayer)
      const basemapStyle = await getStyleJson(BASEMAP_STYLE_URL)
      const basemapLayer = await createVectorTileLayer(BASEMAP_TILE_URL, basemapStyle, 0.8, BASEMAP_LAYER_NAME)
      mapObject.addLayer(basemapLayer)
    }
    loadBaseMap()

    return () => {
      mapObject.setTarget('')
    }
  }, [fbaLayers.baseLayers])

  useEffect(() => {
    if (!map) return

    const stationsLayer = createStationsLayer(stations)

    map.addLayer(stationsLayer)
    return () => {
      map.removeLayer(stationsLayer)
    }
  }, [map, stations])

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box
          ref={mapRef}
          data-testid="fba-map"
          sx={{
            display: 'flex',
            flex: 1,
            position: 'relative'
          }}
        >
          <Box sx={{ position: 'absolute', zIndex: '1', bottom: '0.5rem' }}>
            <Legend
              onToggleLayer={handleToggleLayer}
              showShapeStatus={showShapeStatus}
              setShowShapeStatus={setShowShapeStatus}
              showHFI={showHFI}
              setShowHFI={setShowHFI}
            />
          </Box>
          <ScalebarContainer ref={scaleRef} />
        </Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
