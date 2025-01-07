import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Map, View } from 'ol'
import { PMTilesVectorSource } from 'ol-pmtiles'
import { defaults as defaultControls } from 'ol/control'
import { boundingExtent } from 'ol/extent'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import VectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { PMTILES_BUCKET } from 'utils/env'

import React, { useEffect, useRef, useState } from 'react'

import { styleFuelGrid } from '@/features/psuInsights/components/map/psuFeatureStylers'
import { Box } from '@mui/material'
import { ErrorBoundary } from '@sentry/react'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import TileLayer from 'ol/layer/Tile'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations } from 'app/rootReducer'
import { getStations, StationSource } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'

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
import { AppDispatch } from '@/app/store'

const MapContext = React.createContext<Map | null>(null)

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const SkillMap = () => {
  const { stations } = useSelector(selectFireWeatherStations)
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const dispatch: AppDispatch = useDispatch()

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

  const [fireCentreVTL] = useState(
    new VectorTileLayer({
      source: fireCentreVectorSource,
      style: fireCentreStyler(undefined),
      zIndex: 51
    })
  )

  const [fireCentreLineVTL] = useState(
    new VectorTileLayer({
      source: fireCentreVectorSource,
      style: fireCentreLineStyler(undefined),
      zIndex: 52
    })
  )

  //   const [fireShapeVTL] = useState(
  //     new VectorTileLayer({
  //       source: fireShapeVectorSource,
  //       style: fireShapeStyler(cloneDeep(props.fireShapeAreas), props.advisoryThreshold, showShapeStatus),
  //       zIndex: 50,
  //       properties: { name: 'fireShapeVector' }
  //     })
  //   )
  //   const [fireShapeHighlightVTL] = useState(
  //     new VectorTileLayer({
  //       source: fireShapeVectorSource,
  //       style: fireShapeLineStyler(cloneDeep(props.fireShapeAreas), props.advisoryThreshold, props.selectedFireShape),
  //       zIndex: 53,
  //       properties: { name: 'fireShapeVector' }
  //     })
  //   )
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
      style: fireShapeLabelStyler(undefined),
      zIndex: 99,
      minZoom: 6
    })
  )

  useEffect(() => {
    if (!mapRef.current) return

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({ source: baseMapSource }),
        fireCentreVTL,
        fireCentreLineVTL,
        fireCentreLabelVTL,
        fireShapeLabelVTL
      ],
      controls: defaultControls(),
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })
    mapObject.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })
    setMap(mapObject)

    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))

    return () => {
      mapObject.setTarget('')
    }
  }, [])

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

export default SkillMap
