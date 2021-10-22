import { ErrorBoundary } from 'components'
import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import React, { useEffect, useRef } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { fromLonLat } from 'ol/proj'
import { Fill, Stroke, Style } from 'ol/style'
import OLTileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'

import { VERNON_FIRECENTER } from 'features/fbaCalculator/data/data'
import { source } from 'features/fireWeather/components/maps/constants'
import Polygon from 'ol/geom/Polygon'
import { selectFireWeatherStations } from 'app/rootReducer'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { get } from 'ol/proj'
import OLVectorLayer from 'ol/layer/Vector'
import CircleStyle from 'ol/style/Circle'

import { useSelector } from 'react-redux'

export const fbaMapContext = React.createContext<ol.Map | null>(null)

const zoom = 6

export interface FBAMapProps {
  testId?: string
  center: number[]
}

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

  return new VectorLayer({
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

const FBAMap = (props: FBAMapProps) => {
  const useStyles = makeStyles({
    main: {
      height: '100%',
      width: '100%'
    },
    map: {
      position: 'relative',
      width: 'inherit',
      height: 'inherit'
    }
  })
  const classes = useStyles()
  const { stations } = useSelector(selectFireWeatherStations)
  const mapRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (!mapRef.current) return

    const stationsSource = new olSource.Vector({
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

    const options: MapOptions = {
      view: new ol.View({ zoom, center: fromLonLat(props.center) }),
      layers: [
        new OLTileLayer({
          source
        }),
        buildHFILayers(),
        stationsLayer
      ],
      overlays: [],
      controls: defaultControls()
    }

    const mapObject = new ol.Map(options)

    mapObject.setTarget(mapRef.current)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <ErrorBoundary>
      <div className={classes.main}>
        <div ref={mapRef} data-testid="fba-map" className={classes.map}></div>
      </div>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
