import * as ol from 'ol'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import * as olpmtiles from 'ol-pmtiles'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { fromLonLat } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import XYZ from 'ol/source/XYZ'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectRunDates } from 'app/rootReducer'
import { source as baseMapSource, COG_TILE_SIZE, SFMS_MAX_ZOOM } from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import { FireCenter, FireZone, FireZoneArea } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCentreExtents'
import {
  fireCentreStyler,
  fireCentreLabelStyler,
  fireZoneStyler,
  fireZoneLabelStyler,
  stationStyler,
  hfiStyler
} from 'features/fba/components/map/featureStylers'
import { CENTER_OF_BC } from 'utils/constants'
import { DateTime } from 'luxon'
import { PMTILES_BUCKET, RASTER_SERVER_BASE_URL } from 'utils/env'
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
  selectedFireZone: FireZone | undefined
  forDate: DateTime
  setSelectedFireZone: React.Dispatch<React.SetStateAction<FireZone | undefined>>
  fireZoneAreas: FireZoneArea[]
  runType: RunType
  advisoryThreshold: number
}

export const hfiSourceFactory = (url: string) => {
  return new XYZ({
    url: `${RASTER_SERVER_BASE_URL}/tile/{z}/{x}/{y}?path=${url}&source=hfi`,
    interpolate: false,
    tileSize: COG_TILE_SIZE,
    maxZoom: SFMS_MAX_ZOOM
  })
}

export const ftlSourceFactory = (filter: string) => {
  return new XYZ({
    url: `${RASTER_SERVER_BASE_URL}/tile/{z}/{x}/{y}?path=gpdqha/ftl/ftl_2018_cloudoptimized.tif&source=ftl&filter=${filter}`,
    interpolate: true,
    tileSize: COG_TILE_SIZE
  })
}

export const hfiTileFactory = (url: string, layerName: string) => {
  return new Tile({ source: hfiSourceFactory(url), properties: { name: layerName } })
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
  const [showZoneStatus, setShowZoneStatus] = useState(true)
  const [showHFI, setShowHFI] = React.useState(false)
  const [map, setMap] = useState<ol.Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const { mostRecentRunDate } = useSelector(selectRunDates)

  const fireCentreVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentres.pmtiles`
  })
  const fireZoneVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZones.pmtiles`
  })
  const fireCentreLabelVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireCentreLabels.pmtiles`
  })
  const fireZoneLabelVectorSource = new olpmtiles.PMTilesVectorSource({
    url: `${PMTILES_BUCKET}fireZoneLabels.pmtiles`
  })

  const handleToggleLayer = (layerName: string, isVisible: boolean) => {
    if (map) {
      const layer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.name === layerName)

      if (layerName === 'fireZoneVector') {
        fireZoneVTL.setStyle(
          fireZoneStyler(cloneDeep(props.fireZoneAreas), props.advisoryThreshold, props.selectedFireZone, isVisible)
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
  const [fireZoneVTL] = useState(
    new VectorTileLayer({
      source: fireZoneVectorSource,
      style: fireZoneStyler(
        cloneDeep(props.fireZoneAreas),
        props.advisoryThreshold,
        props.selectedFireZone,
        showZoneStatus
      ),
      zIndex: 49,
      properties: { name: 'fireZoneVector' }
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
  const [fireZoneLabelVTL] = useState(
    new VectorTileLayer({
      declutter: true,
      source: fireZoneLabelVectorSource,
      style: fireZoneLabelStyler(props.selectedFireZone),
      zIndex: 99,
      minZoom: 6
    })
  )

  useEffect(() => {
    if (map) {
      map.on('click', event => {
        fireZoneVTL.getFeatures(event.pixel).then(features => {
          if (!features.length) {
            props.setSelectedFireZone(undefined)
            return
          }
          const feature = features[0]
          if (!feature) {
            return
          }
          const zoneExtent = feature.getGeometry()?.getExtent()
          if (!isUndefined(zoneExtent)) {
            map.getView().fit(zoneExtent)
          }
          const fireZone: FireZone = {
            mof_fire_zone_id: feature.get('MOF_FIRE_ZONE_ID'),
            mof_fire_zone_name: feature.get('MOF_FIRE_ZONE_NAME'),
            mof_fire_centre_name: feature.get('MOF_FIRE_CENTRE_NAME'),
            area_sqm: feature.get('FEATURE_AREA_SQM')
          }
          props.setSelectedFireZone(fireZone)
        })
      })
    }
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

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

    fireZoneVTL.setStyle(
      fireZoneStyler(cloneDeep(props.fireZoneAreas), props.advisoryThreshold, props.selectedFireZone, showZoneStatus)
    )
    fireZoneLabelVTL.setStyle(fireZoneLabelStyler(props.selectedFireZone))
    fireZoneVTL.changed()
    fireZoneLabelVTL.changed()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.selectedFireZone, props.fireZoneAreas, props.advisoryThreshold])

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
        fireZoneVTL,
        fireCentreLabelVTL,
        fireZoneLabelVTL
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
              showZoneStatus={showZoneStatus}
              setShowZoneStatus={setShowZoneStatus}
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
