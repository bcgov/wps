import { Box } from '@mui/material'
import { type FireShape, RunType } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { createHillshadeVectorTileLayer, createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { selectProvincialSummaryZones, selectRunDates } from 'app/rootReducer'
import {
  fireCentreLabelStyler,
  fireCentreLineStyler,
  fireCentreStyler,
  fireShapeLabelStyler,
  fireShapeLineStyler,
  fireShapeStyler,
  hfiStyler
} from 'features/fba/components/map/featureStylers'
import Legend from 'features/fba/components/map/Legend'
import ScalebarContainer from 'features/fba/components/map/ScaleBarContainer'
import { extentsMap } from 'features/fba/fireCentreExtents'
import { fireZoneExtentsMap } from 'features/fba/fireZoneUnitExtents'
import { buildPMTilesURL } from 'features/fba/pmtilesBuilder'
import { cloneDeep, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { Map as OlMap, View } from 'ol'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import ScaleLine from 'ol/control/ScaleLine'
import { boundingExtent } from 'ol/extent'
import VectorTileLayer from 'ol/layer/VectorTile'
import type MapBrowserEvent from 'ol/MapBrowserEvent'
import { PMTilesVectorSource } from 'ol-pmtiles'
import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import 'ol/ol.css'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import {
  BASEMAP_STYLE_URL,
  BASEMAP_TILE_URL,
  HILLSHADE_STYLE_URL,
  HILLSHADE_TILE_URL,
  PMTILES_BUCKET
} from '@wps/utils/env'
import { fromLonLat } from 'ol/proj'
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { MapContext } from '@/features/fba/context/MapContext'

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

export const hfiLayerName = 'hfiVector'
export const zoneStatusLayerName = 'fireShapeVector'

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

const createPMTilesVectorSource = (filename: string) =>
  new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}${filename}`
  })

const FBAMap = (props: FBAMapProps) => {
  const { forDate, selectedFireCentre, selectedFireShape, setSelectedFireShape, runType, zoomSource, setZoomSource } =
    props

  // store
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

  // stable OpenLayers sources and layers
  const fireCentreVectorSource = useMemo(() => createPMTilesVectorSource('fireCentres.pmtiles'), [])
  const fireShapeVectorSource = useMemo(() => createPMTilesVectorSource('fireZoneUnits.pmtiles'), [])
  const fireCentreLabelVectorSource = useMemo(() => createPMTilesVectorSource('fireCentreLabels.pmtiles'), [])
  const fireShapeLabelVectorSource = useMemo(() => createPMTilesVectorSource('fireZoneUnitLabels.pmtiles'), [])

  const fireCentreVTL = useMemo(
    () =>
      new VectorTileLayer({
        source: fireCentreVectorSource,
        style: fireCentreStyler(undefined),
        zIndex: 51
      }),
    [fireCentreVectorSource]
  )

  const fireCentreLineVTL = useMemo(
    () =>
      new VectorTileLayer({
        source: fireCentreVectorSource,
        style: fireCentreLineStyler(undefined),
        zIndex: 52
      }),
    [fireCentreVectorSource]
  )

  const fireShapeVTL = useMemo(
    () =>
      new VectorTileLayer({
        source: fireShapeVectorSource,
        style: fireShapeStyler([], true),
        zIndex: 50,
        properties: { name: zoneStatusLayerName }
      }),
    [fireShapeVectorSource]
  )

  const fireShapeHighlightVTL = useMemo(
    () =>
      new VectorTileLayer({
        source: fireShapeVectorSource,
        style: fireShapeLineStyler([], undefined),
        zIndex: 53,
        properties: { name: zoneStatusLayerName }
      }),
    [fireShapeVectorSource]
  )

  const fireCentreLabelVTL = useMemo(
    () =>
      new VectorTileLayer({
        source: fireCentreLabelVectorSource,
        style: fireCentreLabelStyler,
        zIndex: 100,
        maxZoom: 6
      }),
    [fireCentreLabelVectorSource]
  )

  const fireShapeLabelVTL = useMemo(
    () =>
      new VectorTileLayer({
        declutter: true,
        source: fireShapeLabelVectorSource,
        style: fireShapeLabelStyler(undefined),
        zIndex: 99,
        minZoom: 6
      }),
    [fireShapeLabelVectorSource]
  )

  // event handlers
  const handleToggleLayer = useCallback(
    (layerName: string, isVisible: boolean) => {
      if (map) {
        const layer = map
          .getLayers()
          .getArray()
          .find(l => l.getProperties()?.name === layerName)

        if (layerName === zoneStatusLayerName) {
          fireShapeVTL.setStyle(fireShapeStyler(cloneDeep(provincialSummaryZones), isVisible))
        } else if (layer) {
          layer.setVisible(isVisible)
        }
      }
    },
    [fireShapeVTL, map, provincialSummaryZones]
  )

  // effects
  useEffect(() => {
    const hfiLayerEnabled = localStorage.getItem(hfiLayerName)
    setShowHFI(hfiLayerEnabled === 'true')
  }, [])

  useEffect(() => {
    if (!map) return

    const handleMapClick = (event: MapBrowserEvent<UIEvent>) => {
      fireShapeVTL.getFeatures(event.pixel).then(features => {
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
  }, [fireShapeVTL, map, setSelectedFireShape, setZoomSource])

  useEffect(() => {
    if (!map) return

    if (selectedFireCentre && zoomSource === 'fireCentre') {
      const fireCentreExtent = extentsMap.get(selectedFireCentre.name)
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent, { duration: 400, padding: [50, 50, 50, 50] })
      }
    } else if (!selectedFireCentre && zoomSource !== 'fireShape') {
      map.getView().fit(bcExtent, { duration: 600, padding: [50, 50, 50, 50] })
    }
  }, [map, selectedFireCentre, zoomSource])

  useEffect(() => {
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

    fireCentreVTL.setStyle(fireCentreStyler(selectedFireCentre))
    fireShapeVTL.setStyle(fireShapeStyler(cloneDeep(provincialSummaryZones), showShapeStatus))
    fireShapeLabelVTL.setStyle(fireShapeLabelStyler(selectedFireShape))
    fireShapeHighlightVTL.setStyle(fireShapeLineStyler(cloneDeep(provincialSummaryZones), selectedFireShape))
    fireCentreLineVTL.setStyle(fireCentreLineStyler(selectedFireCentre))

    fireShapeVTL.changed()
    fireShapeHighlightVTL.changed()
    fireShapeLabelVTL.changed()
    fireCentreLineVTL.changed()
    fireCentreVTL.changed()
  }, [
    fireCentreLineVTL,
    fireCentreVTL,
    fireShapeHighlightVTL,
    fireShapeLabelVTL,
    fireShapeVTL,
    map,
    provincialSummaryZones,
    selectedFireCentre,
    selectedFireShape,
    showShapeStatus
  ])

  useEffect(() => {
    if (!map) return
    removeLayerByName(map, hfiLayerName)
    if (!isNull(mostRecentRunDate)) {
      const runDate = runType === RunType.FORECAST ? DateTime.fromISO(mostRecentRunDate) : forDate
      const hfiSource = new PMTilesVectorSource({
        url: buildPMTilesURL(forDate, runType, runDate)
      })

      const latestHFILayer = new VectorTileLayer({
        source: hfiSource,
        style: hfiStyler,
        zIndex: 100,
        minZoom: 4,
        properties: { name: hfiLayerName },
        visible: showHFI
      })
      map.addLayer(latestHFILayer)
    }
  }, [forDate, map, mostRecentRunDate, runType, showHFI])

  useEffect(() => {
    if (!mapRef.current) return

    const mapObject = new OlMap({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      }),
      layers: [
        fireCentreVTL,
        fireCentreLineVTL,
        fireShapeVTL,
        fireShapeHighlightVTL,
        fireCentreLabelVTL,
        fireShapeLabelVTL
      ],
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
  }, [fireCentreLabelVTL, fireCentreLineVTL, fireCentreVTL, fireShapeHighlightVTL, fireShapeLabelVTL, fireShapeVTL])

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
