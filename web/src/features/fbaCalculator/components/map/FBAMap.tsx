import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import { fromLonLat, get } from 'ol/proj'
import { Fill, Stroke, Style } from 'ol/style'
import OLVectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'

import GeoJSON from 'ol/format/GeoJSON'
import CircleStyle from 'ol/style/Circle'

import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations } from 'app/rootReducer'
import { source } from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import { tile as tileStrategy } from 'ol/loadingstrategy'
import { createXYZ } from 'ol/tilegrid'
import { getFireCenterVectorSource } from 'api/fbaVectorSourceAPI'
import { TileWMS } from 'ol/source'

export const fbaMapContext = React.createContext<ol.Map | null>(null)

const zoom = 5.45
const BC_CENTER_FIRE_CENTERS = [-124.16748046874999, 54.584796743678744]

export interface FBAMapProps {
  testId?: string
  className: string
}

const vectorSource = new VectorSource({
  loader: async (extent, _resolution, projection) => {
    getFireCenterVectorSource(extent, projection, vectorSource)
  },
  strategy: tileStrategy(
    createXYZ({
      tileSize: 512
    })
  )
})

const vector = new OLVectorLayer({
  source: vectorSource,
  style: () => {
    return new Style({
      stroke: new Stroke({
        color: 'blue',
        width: 4
      })
    })
  }
})

const buildFireZoneTileLayer = () => {
  return new Tile({
    opacity: 1,
    preload: Infinity,
    source: new TileWMS({
      url: 'https://openmaps.gov.bc.ca/geo/pub/wms',
      params: {
        LAYERS: 'WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_ZONES_SP',
        TILED: true,
        STYLES: '3460'
      },
      serverType: 'geoserver',
      transition: 0
    })
  })
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
  useEffect(() => {
    // The React ref is used to attach to the div rendered in our
    // return statement of which this map's target is set to.
    // The ref is a div of type  HTMLDivElement.

    // Pattern copied from web/src/features/map/Map.tsx
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({
        center: fromLonLat(BC_CENTER_FIRE_CENTERS),
        zoom
      }),
      layers: [
        new Tile({
          source
        }),
        vector,
        buildFireZoneTileLayer()
      ],
      overlays: [],
      controls: defaultControls()
    }

    // Create the map with the options above and set the target
    // To the ref above so that it is rendered in that div
    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)

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
      style: new Style({
        image: new CircleStyle({
          radius: 5,
          fill: new Fill({
            color: 'black'
          })
        })
      })
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
