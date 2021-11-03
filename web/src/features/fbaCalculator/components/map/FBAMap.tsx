import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import { fromLonLat, get } from 'ol/proj'
import { Fill, Stroke, Style } from 'ol/style'
import OLVectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'

import Polygon from 'ol/geom/Polygon'
import GeoJSON from 'ol/format/GeoJSON'
import CircleStyle from 'ol/style/Circle'

import { VERNON_FIRECENTER } from 'features/fbaCalculator/data/data'
import { useSelector } from 'react-redux'
import React, { useEffect, useRef, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ErrorBoundary } from 'components'
import { selectFireWeatherStations } from 'app/rootReducer'
import { source } from 'features/fireWeather/components/maps/constants'
import Tile from 'ol/layer/Tile'
import TileWMS from 'ol/source/TileWMS'

export const fbaMapContext = React.createContext<ol.Map | null>(null)

const zoom = 5.45
const BC_CENTER_FIRE_CENTERS = [-124.16748046874999, 54.584796743678744]

export interface FBAMapProps {
  testId?: string
  className: string
}

// Will be parameterized based on fire center in the future
const buildHFILayers = () => {
  const polygonFeature = new ol.Feature(
    new Polygon(VERNON_FIRECENTER.features[0].geometry.coordinates).transform(
      'EPSG:4326',
      'EPSG:3857'
    )
  )

  const vernonSource = new VectorSource({
    features: [polygonFeature]
  })

  return new OLVectorLayer({
    source: vernonSource,
    style: [
      new Style({
        stroke: new Stroke({
          color: 'red',
          width: 3
        }),
        fill: new Fill({
          color: 'rgba(255, 0, 0, 0.5)'
        })
      })
    ]
  })
}

const buildBCTileLayer = (extent: number[]) => {
  return new Tile({
    extent,
    opacity: 0.5,
    preload: Infinity,
    source: new TileWMS({
      url: 'http://openmaps.gov.bc.ca/geo/pub/wms',
      params: {
        LAYERS: 'WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_CENTRES_SP',
        TILED: true
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
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({
        zoom,
        center: fromLonLat(BC_CENTER_FIRE_CENTERS)
      }),
      layers: [
        new Tile({
          source
        }),
        buildHFILayers()
      ],
      overlays: [],
      controls: defaultControls()
    }

    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)

    const extent = mapObject.getView().calculateExtent(mapObject.getSize())
    mapObject.addLayer(buildBCTileLayer(extent))
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
