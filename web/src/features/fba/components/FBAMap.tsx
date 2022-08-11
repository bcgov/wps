import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import { fromLonLat, get } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorLayer from 'ol/layer/Vector'
import OLOverlay from 'ol/Overlay'
import VectorTileSource from 'ol/source/VectorTile'
import MVT from 'ol/format/MVT'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations, selectFireZoneAreas } from 'app/rootReducer'
import { hfiSource as baseMapSource } from 'features/fireWeather/components/maps/constants'
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
} from 'features/fba/components/featureStylers'
import { CENTER_OF_BC } from 'utils/constants'
import { DateTime } from 'luxon'

export const fbaMapContext = React.createContext<ol.Map | null>(null)

const zoom = 6
const TILE_SERVER_URL = 'https://tileserv-dev.apps.silver.devops.gov.bc.ca'

export interface FBAMapProps {
  testId?: string
  className: string
  selectedFireCenter: FireCenter | undefined
  date: DateTime
}

const FBAMap = (props: FBAMapProps) => {
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    }
  })
  const classes = useStyles()
  // const dispatch: AppDispatch = useDispatch()
  const { stations } = useSelector(selectFireWeatherStations)
  const [map, setMap] = useState<ol.Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)
  // const [fireZoneStyle, setFireZoneStyle] = useState(fireZoneStyler)
  // const [prevFireZoneVector, setPrevFireZoneVector] = useState<VectorTileLayer | null>(null)
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
    // setPrevFireZoneVector(fireZoneVector)
    setFireZoneVector(
      new VectorTileLayer({
        source: new VectorTileSource({
          attributions: ['BC Wildfire Service'],
          format: new MVT(),
          url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
        }),
        style: createFireZoneStyler(fireZoneAreas),
        zIndex: 49,
        properties: { name: 'fireZoneVector' }
      })
    )
  }, [fireZoneAreas])

  const hfiVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: ['BC Wildfire Service'],
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=date=${props.date.toISODate()}'`
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

    const latestHFILayer = new VectorTileLayer({
      source: new VectorTileSource({
        attributions: ['BC Wildfire Service'],
        format: new MVT(),
        url: `${TILE_SERVER_URL}/public.hfi/{z}/{x}/{y}.pbf?filter=date=${props.date.toISODate()}'`
      }),
      style: hfiStyler,
      zIndex: 100,
      properties: { name: 'hfiVector' }
    })

    const layer = map
      .getLayers()
      .getArray()
      .find(l => l.getProperties()?.name === 'hfiVector')
    if (layer) {
      map.removeLayer(layer)
    }
    map.addLayer(latestHFILayer)
  }, [props.date]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    const options: MapOptions = {
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
      controls: defaultControls()
    }
    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)

    if (props.selectedFireCenter) {
      const fireCentreExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCentreExtent) {
        mapObject.getView().fit(fireCentreExtent.extent)
      }
    }

    const source = new VectorSource()
    const layer = new VectorLayer({
      source: source
    })

    if (overlayRef.current) {
      const hoverOverlay = new OLOverlay({
        element: overlayRef.current,
        autoPan: true,
        autoPanAnimation: {
          duration: 250
        }
      })

      mapObject.addOverlay(hoverOverlay)

      mapObject.on('pointermove', function (event) {
        source.clear()
        hoverOverlay?.setPosition(undefined)
        mapObject.forEachFeatureAtPixel(
          event.pixel,
          function (feature) {
            const geometry = feature.getGeometry()
            if (geometry) {
              const overlayCurrent = overlayRef.current
              if (overlayCurrent) {
                const hfiRange = feature.get('hfi')
                if (hfiRange) {
                  overlayCurrent.innerHTML = hfiRange
                  hoverOverlay.setPosition(event.coordinate)
                }
              }
            }
          },
          {
            hitTolerance: 2
          }
        )
      })
    }

    mapObject.addLayer(layer)

    setMap(mapObject)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const stationsSource = new VectorSource({
      features: new GeoJSON().readFeatures(
        { type: 'FeatureCollection', features: stations },
        {
          featureProjection: get('EPSG:3857')
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
      <div className={classes.main}>
        <div ref={mapRef} data-testid="fba-map" className={props.className}></div>
        <div ref={overlayRef} id="feature-overlay"></div>
      </div>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
