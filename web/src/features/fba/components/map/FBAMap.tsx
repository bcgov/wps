import { PMTilesVectorSource } from 'ol-pmtiles'
import { Map, View } from 'ol'
import 'ol/ol.css'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { fromLonLat } from 'ol/proj'
import { boundingExtent } from 'ol/extent'
import ScaleLine from 'ol/control/ScaleLine'
import VectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectRunDates } from 'app/rootReducer'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import TileLayer from 'ol/layer/Tile'
import { FireCenter, FireShape, FireShapeArea, FireZoneStatus, RunType } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCentreExtents'
import {
  fireCentreStyler,
  fireCentreLabelStyler,
  fireShapeStyler,
  fireShapeLineStyler,
  fireShapeLabelStyler,
  stationStyler,
  hfiStyler,
  fireCentreLineStyler
} from 'features/fba/components/map/featureStylers'
import { BC_EXTENT, CENTER_OF_BC } from 'utils/constants'
import { DateTime } from 'luxon'
import { PMTILES_BUCKET } from 'utils/env'
import { buildPMTilesURL } from 'features/fba/pmtilesBuilder'
import { isUndefined, cloneDeep, isNull } from 'lodash'
import { Box } from '@mui/material'
import Legend from 'features/fba/components/map/Legend'
import ScalebarContainer from 'features/fba/components/map/ScaleBarContainer'
import { fireZoneExtentsMap } from 'features/fba/fireZoneUnitExtents'
export const MapContext = React.createContext<Map | null>(null)

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

export const hfiLayerName = 'hfiVector'
export const zoneStatusLayerName = 'fireShapeVector'

export interface FBAMapProps {
  testId?: string
  selectedFireCenter: FireCenter | undefined
  selectedFireShape: FireShape | undefined
  forDate: DateTime
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
  fireZoneStatuses: FireZoneStatus[]
  runType: RunType
  zoomSource?: 'fireCenter' | 'fireShape'
  setZoomSource: React.Dispatch<React.SetStateAction<'fireCenter' | 'fireShape' | undefined>>
}

const removeLayerByName = (map: Map, layerName: string) => {
  const layer = map
    .getLayers()
    .getArray()
    .find(l => l.getProperties()?.name === layerName)
  if (layer) {
    map.removeLayer(layer)
  }
}

const FBAMap = (props: FBAMapProps) => {
  const { stations } = useSelector(selectFireWeatherStations)
  const [showShapeStatus, setShowShapeStatus] = useState(true)
  const [showHFI, setShowHFI] = useState(() => {
    const stored = localStorage.getItem(hfiLayerName)
    return stored === 'true'
  })
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const scaleRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const { mostRecentRunDate } = useSelector(selectRunDates)

  const fireCentreVectorSource = new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentres.pmtiles`
  })
  const fireShapeVectorSource = new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZoneUnits.pmtiles`
  })
  const fireCentreLabelVectorSource = new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentreLabels.pmtiles`
  })
  const fireShapeLabelVectorSource = new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZoneUnitLabels.pmtiles`
  })

  const handleToggleLayer = (layerName: string, isVisible: boolean) => {
    if (map) {
      const layer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.name === layerName)

      if (layerName === 'fireShapeVector') {
        fireShapeVTL.setStyle(fireShapeStyler(cloneDeep(props.fireZoneStatuses), isVisible))
      } else if (layer) {
        layer.setVisible(isVisible)
      }
    }
  }

  const [fireCentreVTL] = useState(
    new VectorTileLayer({
      source: fireCentreVectorSource,
      style: fireCentreStyler(props.selectedFireCenter),
      zIndex: 51
    })
  )

  const [fireCentreLineVTL] = useState(
    new VectorTileLayer({
      source: fireCentreVectorSource,
      style: fireCentreLineStyler(props.selectedFireCenter),
      zIndex: 52
    })
  )

  const [fireShapeVTL] = useState(
    new VectorTileLayer({
      source: fireShapeVectorSource,
      style: fireShapeStyler(cloneDeep(props.fireZoneStatuses), showShapeStatus),
      zIndex: 50,
      properties: { name: 'fireShapeVector' }
    })
  )
  const [fireShapeHighlightVTL] = useState(
    new VectorTileLayer({
      source: fireShapeVectorSource,
      style: fireShapeLineStyler(cloneDeep(props.fireZoneStatuses), props.selectedFireShape),
      zIndex: 53,
      properties: { name: 'fireShapeVector' }
    })
  )
  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const [fireCentreLabelVTL] = useState(
    new VectorTileLayer({
      source: fireCentreLabelVectorSource,
      style: fireCentreLabelStyler,
      zIndex: 100,
      maxZoom: 6
    })
  )
  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const [fireShapeLabelVTL] = useState(
    new VectorTileLayer({
      declutter: true,
      source: fireShapeLabelVectorSource,
      style: fireShapeLabelStyler(props.selectedFireShape),
      zIndex: 99,
      minZoom: 6
    })
  )

  useEffect(() => {
    const hfiLayerEnabled = localStorage.getItem(hfiLayerName)
    setShowHFI(hfiLayerEnabled === 'true')
  }, [])

  useEffect(() => {
    if (map) {
      map.on('click', event => {
        fireShapeVTL.getFeatures(event.pixel).then(features => {
          if (!features.length) {
            props.setSelectedFireShape(undefined)
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
          props.setZoomSource('fireShape')
          props.setSelectedFireShape(fireZone)
        })
      })
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // zoom to fire center or whole province
    if (!map) return

    if (props.selectedFireCenter && props.zoomSource === 'fireCenter') {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent, { duration: 400, padding: [50, 50, 50, 50] })
      }
    } else if (!props.selectedFireCenter) {
      // reset map view to full province
      map.getView().fit(bcExtent, { duration: 600, padding: [50, 50, 50, 50] })
    }
  }, [props.selectedFireCenter])

  useEffect(() => {
    // zoom to fire zone
    if (!map) return

    if (props.selectedFireShape && props.zoomSource === 'fireShape') {
      const zoneExtent = fireZoneExtentsMap.get(props.selectedFireShape.fire_shape_id.toString())
      if (!isUndefined(zoneExtent)) {
        map.getView().fit(zoneExtent, { duration: 400, padding: [100, 100, 100, 100], maxZoom: 8 })
      }
    }
  }, [props.selectedFireShape])

  useEffect(() => {
    if (!map) return

    fireCentreVTL.setStyle(fireCentreStyler(props.selectedFireCenter))
    fireShapeVTL.setStyle(fireShapeStyler(cloneDeep(props.fireZoneStatuses), showShapeStatus))
    fireShapeLabelVTL.setStyle(fireShapeLabelStyler(props.selectedFireShape))
    fireShapeHighlightVTL.setStyle(fireShapeLineStyler(cloneDeep(props.fireZoneStatuses), props.selectedFireShape))
    fireCentreLineVTL.setStyle(fireCentreLineStyler(props.selectedFireCenter))

    fireShapeVTL.changed()
    fireShapeHighlightVTL.changed()
    fireShapeLabelVTL.changed()
    fireCentreLineVTL.changed()
    fireCentreVTL.changed()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireCenter, props.selectedFireShape, props.fireZoneStatuses])

  useEffect(() => {
    if (!map) return
    removeLayerByName(map, hfiLayerName)
    if (!isNull(mostRecentRunDate)) {
      // The runDate for forecasts is the mostRecentRunDate. For Actuals, our API expects the runDate to be
      // the same as the forDate.
      const runDate = props.runType === RunType.FORECAST ? DateTime.fromISO(mostRecentRunDate) : props.forDate
      const hfiSource = new PMTilesVectorSource({
        url: buildPMTilesURL(props.forDate, props.runType, runDate)
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
  }, [showHFI, mostRecentRunDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new Map({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      }),
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
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
    return () => {
      mapObject.setTarget('')
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const stationsSource = new VectorSource({
      features: new GeoJSON().readFeatures(
        { type: 'FeatureCollection', features: stations },
        {
          featureProjection: 'EPSG:3857'
        }
      )
    })
    const stationsLayer = new VectorLayer({
      source: stationsSource,
      minZoom: 6,
      style: stationStyler,
      zIndex: 51
    })

    map?.addLayer(stationsLayer)
  }, [stations]) // eslint-disable-line react-hooks/exhaustive-deps

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
