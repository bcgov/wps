import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import { fromLonLat, get } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorTileSource from 'ol/source/VectorTile'
import MVT from 'ol/format/MVT'
import VectorSource from 'ol/source/Vector'

import GeoJSON from 'ol/format/GeoJSON'

import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations } from 'app/rootReducer'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import { FireCenter } from 'api/fbaAPI'
import { extentsMap } from 'features/fba/fireCenterExtents'
import {
  fireCenterStyler,
  fireCenterLableStyler,
  fireZoneStyler,
  fireZoneLableStyler,
  stationStyler,
  thessianPolygonStyler
} from 'features/fba/components/featureStylers'

export const fbaMapContext = React.createContext<ol.Map | null>(null)

const zoom = 5.45
const BC_CENTER_FIRE_CENTERS = [-124.16748046874999, 54.584796743678744]
const TILE_SERVER_URL = 'https://wps-prod-tileserv.apps.silver.devops.gov.bc.ca'

export interface FBAMapProps {
  testId?: string
  className: string
  selectedFireCenter: FireCenter | undefined
}

const FBAMap = (props: FBAMapProps) => {
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    }
  })
  const classes = useStyles()
  const { stations } = useSelector(selectFireWeatherStations)
  const [map, setMap] = useState<ol.Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)

  const fireZoneVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: 'Government of British Columbia',
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_zones/{z}/{x}/{y}.pbf`
    }),
    style: fireZoneStyler,
    zIndex: 49
  })

  const fireZoneLabel = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: 'Government of British Columbia',
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_zones_labels_ext/{z}/{x}/{y}.pbf`
    }),
    style: fireZoneLableStyler,
    zIndex: 99
  })

  const fireCenterLabel = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: 'Government of British Columbia',
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_centres_labels/{z}/{x}/{y}.pbf`
    }),
    style: fireCenterLableStyler,
    zIndex: 100
  })

  const fireCenterVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: 'Government of British Columbia',
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_centres/{z}/{x}/{y}.pbf`
    }),
    style: fireCenterStyler,
    zIndex: 50
  })

  const thesianVector = new VectorTileLayer({
    source: new VectorTileSource({
      attributions: 'Government of British Columbia',
      format: new MVT(),
      url: `${TILE_SERVER_URL}/public.fire_area_thessian_polygons/{z}/{x}/{y}.pbf`
    }),
    style: thessianPolygonStyler,
    zIndex: 50
  })

  useEffect(() => {
    if (!map) return

    if (props.selectedFireCenter) {
      const fireCenterExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCenterExtent) {
        map.getView().fit(fireCenterExtent.extent)
      }
    } else {
      // reset map view to full province
      map.getView().setCenter(fromLonLat(BC_CENTER_FIRE_CENTERS))
      map.getView().setZoom(zoom)
    }
  }, [props.selectedFireCenter]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({
        zoom,
        center: fromLonLat(BC_CENTER_FIRE_CENTERS)
      }),
      layers: [
        new Tile({
          source: baseMapSource
        }),
        fireZoneVector,
        fireCenterVector,
        thesianVector,
        fireZoneLabel,
        fireCenterLabel
      ],
      overlays: [],
      controls: defaultControls()
    }
    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)

    if (props.selectedFireCenter) {
      const fireCenterExtent = extentsMap.get(props.selectedFireCenter.name)
      if (fireCenterExtent) {
        mapObject.getView().fit(fireCenterExtent.extent)
      }
    }
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
      </div>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
