import * as ol from 'ol'
import * as proj from 'ol/proj'
import { defaults as defaultControls, FullScreen } from 'ol/control'
import { Coordinate } from 'ol/coordinate'
import { fromLonLat } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import XYZ from 'ol/source/XYZ'
import OLOverlay from 'ol/Overlay'
import VectorTileSource from 'ol/source/VectorTile'
import MVT from 'ol/format/MVT'
import VectorSource from 'ol/source/Vector'
import Select from 'ol/interaction/Select'
import GeoJSON from 'ol/format/GeoJSON'
import { useDispatch, useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectFireZoneAreas, selectValueAtCoordinate } from 'app/rootReducer'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
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
import { LayerControl } from 'features/fba/components/map/layerControl'
import FBATooltip from 'features/fba/components/map/FBATooltip'
import { RASTER_SERVER_BASE_URL } from 'utils/env'
import { EventsKey } from 'ol/events'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { buildHFICql } from 'features/fba/cqlBuilder'
import { Style } from 'ol/style'
import Fill from 'ol/style/Fill'
import { isNull } from 'lodash'
import { fetchFireZoneAreas } from 'features/fba/slices/fireZoneAreasSlice'

export const MapContext = React.createContext<ol.Map | null>(null)

const zoom = 6
const TILE_SERVER_URL = 'https://wps-prod-tileserv.apps.silver.devops.gov.bc.ca'
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
  const [showHighHFI, setShowHighHFI] = useState(true)
  const [selectedZoneID, setSelectedZoneID] = useState(undefined)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [singleClickKey, setSingleClickKey] = useState<EventsKey | null>(null)
  const [overlayPosition, setOverlayPosition] = useState<Coordinate | undefined>(undefined)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)

  let selectedFireZone: string | number | void | Style | Style[] | undefined = undefined

  const selectedFireZoneStyle = new Style({
    fill: new Fill({
      color: 'rgba(200,20,20,0.4)'
    })
  })

  const fireZoneVectorSource = new VectorTileSource({
    attributions: ['BC Wildfire Service'],
    format: new MVT(),
    url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
  })

  const [fireZoneVTL, setFireZoneVector] = useState(
    new VectorTileLayer({
      source: fireZoneVectorSource,
      style: fireZoneStyler,
      zIndex: 49,
      properties: { name: 'fireZoneVector' }
    })
  )

  const selectionLayer = new VectorTileLayer({
    map: !isNull(map) ? map : undefined,
    renderMode: 'vector',
    source: fireZoneVectorSource,
    style: feature => {
      if (feature.getId() == selectedFireZone) {
        return selectedFireZoneStyle
      }
    }
  })

  const { fireZoneAreas } = useSelector(selectFireZoneAreas)

  useEffect(() => {
    dispatch(fetchFireZoneAreas(props.runType, props.runDate.toISO(), props.forDate.toISODate()))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.forDate, props.runDate, props.runType])

  useEffect(() => {
    if (map) {
      const layer = map
        .getLayers()
        .getArray()
        .find(l => l.getProperties()?.name === 'fireZoneVector')
      if (layer) {
        map.removeLayer(layer)
      }
      map.addLayer(fireZoneVTL)

      map.on('click', event => {
        fireZoneVTL.getFeatures(event.pixel).then(features => {
          if (!features.length) {
            selectedFireZone = undefined
            selectionLayer.changed()
            return
          }
          const feature = features[0]
          if (!feature) {
            return
          }
          const fid = feature.getId()
          selectedFireZone = fid
          selectionLayer.changed()
        })
      })

      // map.on('click', e => {
      //   map.getFeaturesAtPixel(e.pixel).forEach(feature => {
      //     console.log(feature.getProperties())
      //     setSelectedZoneID(feature.get('mof_fire_zone_id'))
      //   })
      // })
    }
  }, [map, fireZoneVTL]) // eslint-disable-line react-hooks/exhaustive-deps

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

  const hfiVTL = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?${buildHFICql(props.forDate, props.runType)}`
    }),
    style: hfiStyler,
    zIndex: 100,
    properties: { name: 'hfiVector' }
  })

  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const fireZoneLabelVTL = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_zones_labels/{z}/{x}/{y}.pbf`
    }),
    style: fireZoneLabelStyler,
    zIndex: 99,
    minZoom: 6
  })

  const fireCentreVTL = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_centres/{z}/{x}/{y}.pbf`
    }),
    style: fireCentreStyler,
    zIndex: 50
  })

  // Seperate layer for polygons and for labels, to avoid duplicate labels.
  const fireCentreLabelVTL = new VectorTileLayer({
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
        url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?${buildHFICql(props.forDate, props.runType)}`,
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
        fireZoneVTL,
        hfiVTL,
        fireCentreVTL,
        // thessianVector,
        fireZoneLabelVTL,
        fireCentreLabelVTL
      ],
      overlays: [],
      controls: defaultControls().extend([
        new FullScreen(),
        LayerControl.buildLayerCheckbox('High HFI', setShowHighHFI, showHighHFI)
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
    const overlay = map.getOverlayById('popup')
    if (overlay) overlay.setPosition(overlayPosition)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overlayPosition])

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
          <FBATooltip ref={overlayRef} valuesAtCoordinate={values} loading={loading} onClose={setOverlayPosition} />
        </div>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
