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
import View from 'ol/View'
import { CENTER_OF_BC } from 'utils/constants'
import { fromLonLat } from 'ol/proj'
import MVT from 'ol/format/MVT'
import VectorTileSource from 'ol/source/VectorTile'
import VectorTileLayer from 'ol/layer/VectorTile'
import {
  fireCentreStyler,
  fireCentreLabelStyler,
  fireZoneStyler,
  fireZoneLabelStyler,
  hfiStyler
} from 'features/fba/components/map/featureStylers'
import { DateTime } from 'luxon'
import { FireCenter } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCentreExtents'

export const MapContext = React.createContext<ol.Map | null>(null)

export const SFMS_MAX_ZOOM = 8 // The SFMS data is so coarse, there's not much point in zooming in further
export const COG_TILE_SIZE = [512, 512] // COG tiffs are 512x512 pixels - reading larger chunks should in theory be faster?
const TILE_SERVER_URL = 'https://wps-pr-2500-tileserv.apps.silver.devops.gov.bc.ca'
const DEFAULT_ZOOM = 6

export interface SnowCoverageMapProps {
  forDate: DateTime
  testId?: string
  className: string
  selectedFireCenter: FireCenter | undefined
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

const SnowCoverageMap = (props: SnowCoverageMapProps) => {
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    }
  })
  const classes = useStyles()
  const { values, loading } = useSelector(selectValueAtCoordinate)
  const [showHighHFI, setShowHighHFI] = useState(true)
  const [showSnowMaskedHighHFI, setShowSnowMaskedHighHFI] = useState(false)
  const [showSnowCoverage, setShowSnowCoverage] = useState(true)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [overlayPosition, setOverlayPosition] = useState<Coordinate | undefined>(undefined)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)

  const fireZoneVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
    }),
    style: fireZoneStyler,
    zIndex: 49,
    properties: { name: 'fireZoneVector' }
  })

  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const fireZoneLabel = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_zones_labels_ext/{z}/{x}/{y}.pbf`
    }),
    style: fireZoneLabelStyler,
    zIndex: 99,
    minZoom: 6
  })

  const fireCentreVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_centres/{z}/{x}/{y}.pbf`
    }),
    style: fireCentreStyler,
    zIndex: 50
  })

  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const fireCentreLabel = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_centres_labels/{z}/{x}/{y}.pbf`
    }),
    style: fireCentreLabelStyler,
    zIndex: 100,
    maxZoom: 6
  })

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

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
        fireZoneVector,
        fireCentreVector,
        fireZoneLabel,
        fireCentreLabel
      ],
      overlays: [],
      controls: defaultControls().extend([
        new FullScreen(),
        LayerControl.buildLayerCheckbox('Snow Coverage', setShowSnowCoverage, showSnowCoverage),
        LayerControl.buildLayerCheckbox('Snow Masked High HFI', setShowSnowMaskedHighHFI, showSnowMaskedHighHFI),
        LayerControl.buildLayerCheckbox('High HFI', setShowHighHFI, showHighHFI)
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

  useEffect(() => {
    if (!map) return
    const layerName = 'snow'
    removeLayerByName(map, layerName)
    if (showSnowCoverage) {
      const source = new GeoTIFF({
        interpolate: false,
        sources: [
          {
            url: `https://nrs.objectstore.gov.bc.ca/gpdqha/snow_coverage/${props.forDate.toISODate()}/snow_coverage_cog.tif`
          }
        ]
      })
      const snowCoverageLayer = new TileLayer({
        source: source,
        style: {
          color: ['case', ['==', ['band', 2], 0], [0, 0, 0, 0], [255, 255, 255, 0.85]]
        }
      })
      snowCoverageLayer.setProperties({ name: layerName })
      map.addLayer(snowCoverageLayer)
    }
  }, [props.forDate, showSnowCoverage, map])

  useEffect(() => {
    if (!map) return
    const layerName = 'hfiVector'
    removeLayerByName(map, layerName)
    if (showHighHFI) {
      const source = new VectorTileSource({
        attributions: ['BC Wildfire Service'],
        format: new MVT(),
        url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=for_date='${props.forDate.toISODate()}' AND run_type='forecast' AND run_date='${props.forDate.toISODate()}' AND snow_masked=false`,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tileLoadFunction: function (tile: any, url) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          tile.setLoader(function (extent: any, _resolution: any, projection: any) {
            fetch(url).then(function (response) {
              response.arrayBuffer().then(function (data) {
                const format = tile.getFormat()
                const features = format.readFeatures(data, {
                  extent: extent,
                  featureProjection: projection
                })
                tile.setFeatures(features)
              })
            })
          })
        }
      })
      const latestHFILayer = new VectorTileLayer({
        source,
        style: hfiStyler,
        zIndex: 100,
        properties: { name: layerName }
      })
      map.addLayer(latestHFILayer)
    }
  }, [props.forDate, showHighHFI]) // eslint-disable-line react-hooks/exhaustive-deps

  // Snow masked high HFI
  useEffect(() => {
    if (!map) return
    const layerName = 'snowMaskedHfiVector'
    removeLayerByName(map, layerName)
    if (showSnowMaskedHighHFI) {
      const source = new VectorTileSource({
        attributions: ['BC Wildfire Service'],
        format: new MVT(),
        url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=for_date='${props.forDate.toISODate()}' AND run_type='forecast' AND run_date='${props.forDate.toISODate()}' AND snow_masked=true`,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tileLoadFunction: function (tile: any, url) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          tile.setLoader(function (extent: any, _resolution: any, projection: any) {
            fetch(url).then(function (response) {
              response.arrayBuffer().then(function (data) {
                const format = tile.getFormat()
                const features = format.readFeatures(data, {
                  extent: extent,
                  featureProjection: projection
                })
                tile.setFeatures(features)
              })
            })
          })
        }
      })
      const latestHFILayer = new VectorTileLayer({
        source,
        style: hfiStyler,
        zIndex: 100,
        properties: { name: layerName }
      })
      map.addLayer(latestHFILayer)
    }
  }, [props.forDate, showSnowMaskedHighHFI]) // eslint-disable-line react-hooks/exhaustive-deps

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
      map.getView().setZoom(DEFAULT_ZOOM)
    }
  }, [props.selectedFireCenter]) // eslint-disable-line react-hooks/exhaustive-deps

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
