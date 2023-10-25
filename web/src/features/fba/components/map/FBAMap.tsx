import * as ol from 'ol'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import * as olpmtiles from 'ol-pmtiles'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { fromLonLat } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectRunDates } from 'app/rootReducer'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import { FireCenter, FireShape, FireShapeArea } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCentreExtents'
import {
  fireCentreStyler,
  fireCentreLabelStyler,
  fireShapeStyler,
  fireShapeLabelStyler,
  stationStyler,
  hfiStyler
} from 'features/fba/components/map/featureStylers'
import { CENTER_OF_BC } from 'utils/constants'
import { DateTime } from 'luxon'
import { PMTILES_BUCKET } from 'utils/env'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { buildPMTilesURL } from 'features/fba/pmtilesBuilder'
import { isUndefined, cloneDeep, isNull } from 'lodash'
import { Box } from '@mui/material'
import Legend from 'features/fba/components/map/Legend'

export const MapContext = React.createContext<ol.Map | null>(null)

const zoom = 6

export interface FBAMapProps {
  testId?: string
  selectedFireCenter: FireCenter | undefined
  selectedFireShape: FireShape | undefined
  forDate: DateTime
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
  fireShapeAreas: FireShapeArea[]
  runType: RunType
  advisoryThreshold: number
  showSummaryPanel: boolean
  setShowSummaryPanel: React.Dispatch<React.SetStateAction<boolean>>
}

const removeLayerByName = (map: ol.Map, layerName: string) => {
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
  const [showHFI, setShowHFI] = React.useState(false)
  const [map, setMap] = useState<ol.Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const { mostRecentRunDate } = useSelector(selectRunDates)

  const fireCentreVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentres.pmtiles`
  })
  const fireShapeVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZoneUnits.pmtiles`
  })
  const fireCentreLabelVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentreLabels.pmtiles`
  })
  const fireShapeLabelVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZoneUnitLabels.pmtiles`
  })

  const handleToggleLayer = (layerName: string, isVisible: boolean) => {
    if (map) {
      const layer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.name === layerName)

      if (layerName === 'fireShapeVector') {
        fireShapeVTL.setStyle(
          fireShapeStyler(cloneDeep(props.fireShapeAreas), props.advisoryThreshold, props.selectedFireShape, isVisible)
        )
      } else if (layer) {
        layer.setVisible(isVisible)
      }
    }
  }

  const [fireCentreVTL] = useState(
    new VectorTileLayer({
      source: fireCentreVectorSource,
      style: fireCentreStyler,
      zIndex: 50
    })
  )
  const [fireShapeVTL] = useState(
    new VectorTileLayer({
      source: fireShapeVectorSource,
      style: fireShapeStyler(
        cloneDeep(props.fireShapeAreas),
        props.advisoryThreshold,
        props.selectedFireShape,
        showShapeStatus
      ),
      zIndex: 49,
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
          const zoneExtent = feature.getGeometry()?.getExtent()
          if (!isUndefined(zoneExtent)) {
            map.getView().fit(zoneExtent, { duration: 400, padding: [50, 50, 50, 50], maxZoom: 7.4 })
          }
          const fireZone: FireShape = {
            fire_shape_id: feature.getProperties().OBJECTID,
            mof_fire_zone_name: feature.getProperties().OBJECTID.FIRE_ZONE,
            mof_fire_centre_name: feature.getProperties().FIRE_CENTR,
            area_sqm: feature.getProperties().Shape_Area
          }
          props.setShowSummaryPanel(true)
          props.setSelectedFireShape(fireZone)
        })
      })
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return

    if (!props.showSummaryPanel) {
      props.setSelectedFireShape(undefined)
    }
  }, [props.showSummaryPanel]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return

    if (props.selectedFireCenter) {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCentreExtent) {
        map.getView().fit(fireCentreExtent.extent)
      }
    } else {
      // reset map view to full province
      map.getView().setCenter(fromLonLat(CENTER_OF_BC))
      map.getView().setZoom(zoom)
    }
  }, [props.selectedFireCenter]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return

    fireShapeVTL.setStyle(
      fireShapeStyler(
        cloneDeep(props.fireShapeAreas),
        props.advisoryThreshold,
        props.selectedFireShape,
        showShapeStatus
      )
    )
    fireShapeLabelVTL.setStyle(fireShapeLabelStyler(props.selectedFireShape))
    fireShapeVTL.changed()
    fireShapeLabelVTL.changed()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireShape, props.fireShapeAreas, props.advisoryThreshold])

  useEffect(() => {
    if (!map) return
    const layerName = 'hfiVector'
    removeLayerByName(map, layerName)
    if (!isNull(mostRecentRunDate)) {
      // The runDate for forecasts is the mostRecentRunDate. For Actuals, our API expects the runDate to be
      // the same as the forDate.
      const runDate = props.runType === RunType.FORECAST ? DateTime.fromISO(mostRecentRunDate) : props.forDate
      const hfiSource = new olpmtiles.PMTilesVectorSource({
        url: buildPMTilesURL(props.forDate, props.runType, runDate)
      })

      const latestHFILayer = new VectorTileLayer({
        source: hfiSource,
        style: hfiStyler,
        zIndex: 100,
        minZoom: 4,
        properties: { name: layerName },
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
    const mapObject = new ol.Map({
      view: new ol.View({
        zoom,
        center: fromLonLat(CENTER_OF_BC)
      }),
      layers: [
        new Tile({
          source: baseMapSource
        }),
        fireCentreVTL,
        fireShapeVTL,
        fireCentreLabelVTL,
        fireShapeLabelVTL
      ],
      overlays: [],
      controls: defaultControls().extend([new FullScreen()])
    })
    mapObject.setTarget(mapRef.current)

    if (props.selectedFireCenter) {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCentreExtent) {
        mapObject.getView().fit(fireCentreExtent.extent)
      }
    }

    setMap(mapObject)
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
    const stationsLayer = new OLVectorLayer({
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
              showZoneStatus={showShapeStatus}
              setShowShapeStatus={setShowShapeStatus}
              showHFI={showHFI}
              setShowHFI={setShowHFI}
            />
          </Box>
        </Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
