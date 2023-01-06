import * as ol from 'ol'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { Coordinate } from 'ol/coordinate'
import XYZ from 'ol/source/XYZ'
import OLOverlay from 'ol/Overlay'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { ErrorBoundary } from 'components'
import { selectValueAtCoordinate } from 'app/rootReducer'
import Tile from 'ol/layer/Tile'
import { LayerControl } from 'features/fba/components/map/layerControl'
import FBATooltip from 'features/fba/components/map/FBATooltip'
import { RASTER_SERVER_BASE_URL } from 'utils/env'
import { GeoTIFF } from 'ol/source'
import TileLayer from 'ol/layer/WebGLTile'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import View from 'ol/View';
import { CENTER_OF_BC } from 'utils/constants' 
import { fromLonLat } from 'ol/proj'

export const MapContext = React.createContext<ol.Map | null>(null)

export const SFMS_MAX_ZOOM = 8 // The SFMS data is so coarse, there's not much point in zooming in further
export const COG_TILE_SIZE = [512, 512] // COG tiffs are 512x512 pixels - reading larger chunks should in theory be faster?

export interface SnowCoverageMapProps {
  testId?: string
  className: string
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

const SnowCoverageMap = (props: SnowCoverageMapProps) => {
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    }
  })
  const classes = useStyles()
  const { values, loading } = useSelector(selectValueAtCoordinate)
  const [showRawHFI, setShowRawHFI] = useState(false)
  const [showFTL, setShowFTL] = useState(false)
  const [showFTL_M, setShowFTL_M] = useState(false)
  const [showSfmsFtl, setShowSfmsFtl] = useState(false)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [overlayPosition, setOverlayPosition] = useState<Coordinate | undefined>(undefined)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    const source = new GeoTIFF({
      interpolate: false,
      sources: [
        {
          url: 'https://nrs.objectstore.gov.bc.ca/gpdqha/snow_coverage/2022-10-25/snow_coverage_cog.tif?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=nr-wps-dev/20221229/us-east-1/s3/aws4_request&X-Amz-Date=20221229T210006Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=a105de35c47a37746f0147cfb8acda5f927fe8b3e2dcb3aa6bd7d4b49023902e'
        }
      ]
    })
    const snowCoverageLayer = new TileLayer({
      source: source,
      style: {
        color: [
          'case',
          ['==', ['band', 2], 0],
          [0, 0, 0, 0],
          [255, 255, 255, 0.85]
        ]
      }
    })

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new ol.Map({
      view: new View({
        center: fromLonLat(CENTER_OF_BC),
        zoom: 5
      }),
      layers: [
        new Tile({
          source: baseMapSource
        }),
        snowCoverageLayer
        // fireZoneVector,
        // fireCentreVector,
        // // thessianVector,
        // fireZoneLabel,
        // fireCentreLabel
      ],
      overlays: [],
      controls: defaultControls().extend([
        new FullScreen(),
        LayerControl.buildLayerCheckbox('FTL 2018', setShowFTL, showFTL),
        LayerControl.buildLayerCheckbox('FTL 2018 M1/M2', setShowFTL_M, showFTL_M),
        LayerControl.buildLayerCheckbox('FTL SFMS', setShowSfmsFtl, showSfmsFtl),
        LayerControl.buildLayerCheckbox('Raw HFI', setShowRawHFI, showRawHFI)
      ])
    })

    mapObject.setTarget(mapRef.current)

    if (overlayRef.current) {
      const overlay = new OLOverlay({
        element: overlayRef.current,
        autoPan: { animation: { duration: 250 } },
        id: 'popup'
      })

      mapObject.addOverlay(overlay)
    }

    setMap(mapObject)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return
    const overlay = map.getOverlayById('popup')
    if (overlay) overlay.setPosition(overlayPosition)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overlayPosition])

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <div className={classes.main}>
          <div ref={mapRef} data-testid="fba-map" className={props.className}></div>
          <FBATooltip ref={overlayRef} valuesAtCoordinate={values} loading={loading} onClose={setOverlayPosition} />
        </div>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(SnowCoverageMap)
