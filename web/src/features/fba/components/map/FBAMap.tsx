import * as ol from 'ol'
import * as proj from 'ol/proj'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { fromLonLat } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import XYZ from 'ol/source/XYZ'
import OLOverlay from 'ol/Overlay'
import VectorTileSource from 'ol/source/VectorTile'
import MVT from 'ol/format/MVT'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { useDispatch, useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectFireZoneAreas, selectValueAtCoordinate } from 'app/rootReducer'
import {
  sfmsElevationSource,
  twelveArcElevationSource,
  ftlSource,
  sfmsFtlSource,
  sfmsSlopeSource,
  sfmsAspectSource,
  source as baseMapSource
} from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import { FireCenter } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCentreExtents'
import {
  fireCentreStyler,
  fireCentreLabelStyler,
  fireZoneStyler,
  fireZoneLabelStyler,
  stationStyler,
  hfiStyler,
  createFireZoneStyler
} from 'features/fba/components/map/featureStylers'
import { CENTER_OF_BC } from 'utils/constants'
import { DateTime } from 'luxon'
import { AppDispatch } from 'app/store'
import { fetchValuesAtCoordinate } from 'features/fba/slices/valueAtCoordinateSlice'
import { LayerControl } from 'features/fba/components/map/layerControl'
import FBATooltip from 'features/fba/components/map/FBATooltip'
import { RASTER_SERVER_BASE_URL } from 'utils/env'
import { EventsKey } from 'ol/events'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

export const MapContext = React.createContext<ol.Map | null>(null)

const zoom = 6
const TILE_SERVER_URL = 'https://tileserv-dev.apps.silver.devops.gov.bc.ca'
export const SFMS_MAX_ZOOM = 8 // The SFMS data is so coarse, there's not much point in zooming in further
export const COG_TILE_SIZE = [512, 512] // COG tiffs are 512x512 pixels - reading larger chunks should in theory be faster?

export interface FBAMapProps {
  testId?: string
  className: string
  selectedFireCenter: FireCenter | undefined
  forDate: DateTime
  runDate: DateTime
  setIssueDate: React.Dispatch<React.SetStateAction<DateTime | null>>
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
  console.log(`New run type from FBAMap: ${props.runType}`)
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    }
  })
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { stations } = useSelector(selectFireWeatherStations)
  const { values, loading } = useSelector(selectValueAtCoordinate)
  const [showRawHFI, setShowRawHFI] = useState(false)
  const [showFTL, setShowFTL] = useState(false)
  const [showFTL_M, setShowFTL_M] = useState(false)
  const [showSfmsFtl, setShowSfmsFtl] = useState(false)
  const [showHighHFI, setShowHighHFI] = useState(true)
  const [showSfmsElevation, setShowSfmsElevation] = useState(false)
  const [show12arcElevation, setShow12arcElevation] = useState(false)
  const [showSfmsSlope, setShowSfmsSlope] = useState(false)
  const [showSfmsAspect, setShowSfmsAspect] = useState(false)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [singleClickKey, setSingleClickKey] = useState<EventsKey | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)
  const [fireZoneVector, setFireZoneVector] = useState(
    new VectorTileLayer({
      source: new VectorTileSource({
        attributions: ['BC Wildfire Service'],
        format: new MVT(),
        url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
      }),
      style: fireZoneStyler,
      zIndex: 49,
      properties: { name: 'fireZoneVector' }
    })
  )

  const { fireZoneAreas } = useSelector(selectFireZoneAreas)

  useEffect(() => {
    if (map) {
      const layer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.name === 'fireZoneVector')
      if (layer) {
        map.removeLayer(layer)
      }
      map.addLayer(fireZoneVector)
    }
  }, [map, fireZoneVector])

  useEffect(() => {
    setFireZoneVector(
      new VectorTileLayer({
        source: new VectorTileSource({
          attributions: ['BC Wildfire Service'],
          format: new MVT(),
          url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
        }),
        style: createFireZoneStyler(fireZoneAreas, props.advisoryThreshold),
        zIndex: 49,
        properties: { name: 'fireZoneVector' }
      })
    )
  }, [fireZoneAreas, props.advisoryThreshold])

  const hfiVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=for_date='${props.forDate.toISODate()}'&run_type=${props.runType
        .toString()
        .toLowerCase()}&run_date='${props.runDate.toISODate()}'`
    }),
    style: hfiStyler,
    zIndex: 100,
    properties: { name: 'hfiVector' }
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
    const layerName = 'hfiVector'
    removeLayerByName(map, layerName)
    if (showHighHFI) {
      const source = new VectorTileSource({
        attributions: ['BC Wildfire Service'],
        format: new MVT(),
        url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=for_date='${props.forDate.toISODate()}'&run_type='${props.runType
          .toString()
          .toLowerCase()}'&run_date='${props.runDate.toISODate()}'`,
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
                if (features.length > 0) {
                  props.setIssueDate(DateTime.fromSQL(features[0].getProperties()['run_date'], { zone: 'utc' }))
                }
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
  }, [props.forDate, showHighHFI, props.setIssueDate, props.runType]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return
    const layerName = 'hfiRaw'
    removeLayerByName(map, layerName)
    if (showRawHFI) {
      const isoDate = props.forDate.toISODate().replaceAll('-', '')
      const layer = hfiTileFactory(`gpdqha/sfms/cog/cog_hfi${isoDate}.tif`, layerName)
      map.addLayer(layer)
    }
  }, [props.forDate, showRawHFI]) // eslint-disable-line react-hooks/exhaustive-deps

  const addRemoveLayer = (map: ol.Map | null, show: boolean, layerName: string, source: XYZ) => {
    if (!map) return
    if (show) {
      map.addLayer(new Tile({ source: source, properties: { name: layerName } }))
    } else {
      removeLayerByName(map, layerName)
    }
  }

  useEffect(() => {
    addRemoveLayer(map, showFTL, 'ftl', ftlSource)
  }, [showFTL]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    addRemoveLayer(map, showSfmsElevation, 'sfmsElevation', sfmsElevationSource)
  }, [showSfmsElevation]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    addRemoveLayer(map, show12arcElevation, '12arcElevation', twelveArcElevationSource)
  }, [show12arcElevation]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    addRemoveLayer(map, showSfmsFtl, 'sfmsFtl', sfmsFtlSource)
  }, [showSfmsFtl]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    addRemoveLayer(map, showSfmsAspect, 'sfmsAspect', sfmsAspectSource)
  }, [showSfmsAspect]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    addRemoveLayer(map, showSfmsSlope, 'sfmsSlope', sfmsSlopeSource)
  }, [showSfmsSlope]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return
    const layerName = 'ftlM'
    if (showFTL_M) {
      map.addLayer(new Tile({ source: ftlSourceFactory('m1/m2'), properties: { name: layerName } }))
    } else {
      removeLayerByName(map, layerName)
    }
  }, [showFTL_M]) // eslint-disable-line react-hooks/exhaustive-deps

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
        fireZoneVector,
        hfiVector,
        fireCentreVector,
        // thessianVector,
        fireZoneLabel,
        fireCentreLabel
      ],
      overlays: [],
      controls: defaultControls().extend([
        new FullScreen(),
        LayerControl.buildLayerCheckbox('FTL 2018', setShowFTL, showFTL),
        LayerControl.buildLayerCheckbox('FTL 2018 M1/M2', setShowFTL_M, showFTL_M),
        LayerControl.buildLayerCheckbox('FTL SFMS', setShowSfmsFtl, showSfmsFtl),
        LayerControl.buildLayerCheckbox('High HFI', setShowHighHFI, showHighHFI),
        LayerControl.buildLayerCheckbox('Raw HFI', setShowRawHFI, showRawHFI),
        LayerControl.buildLayerCheckbox('SFMS Elevation', setShowSfmsElevation, showSfmsElevation),
        LayerControl.buildLayerCheckbox('12 arc Elevation', setShow12arcElevation, show12arcElevation),
        LayerControl.buildLayerCheckbox('SFMS Slope', setShowSfmsSlope, showSfmsSlope),
        LayerControl.buildLayerCheckbox('SFMS Aspect', setShowSfmsAspect, showSfmsAspect)
      ])
    })
    mapObject.setTarget(mapRef.current)

    if (props.selectedFireCenter) {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCentreExtent) {
        mapObject.getView().fit(fireCentreExtent.extent)
      }
    }

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
    if (singleClickKey) {
      map.un('singleclick', singleClickKey.listener)
    }
    const newKey = map.on('singleclick', e => {
      const overlay = map.getOverlayById('popup')
      if (overlay) {
        const coordinate = proj.transform(e.coordinate, 'EPSG:3857', 'EPSG:4326')
        // fetch hfi at coordinate
        dispatch(fetchValuesAtCoordinate(coordinate[1], coordinate[0], props.forDate))
        overlay.setPosition(e.coordinate)
      }
    })
    setSingleClickKey(newKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.forDate, map, dispatch])

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
        <div className={classes.main}>
          <div ref={mapRef} data-testid="fba-map" className={props.className}></div>
          <FBATooltip ref={overlayRef} valuesAtCoordinate={values} loading={loading} />
        </div>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
