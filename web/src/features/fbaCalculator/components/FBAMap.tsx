import { ErrorBoundary } from 'components'
import * as ol from 'ol'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'
import React, { useEffect, useRef, useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import TileLayer from 'ol/layer/Tile'
import { fromLonLat } from 'ol/proj'
import OSM from 'ol/source/OSM'

const zoom = 6
const context = React.createContext<ol.Map | null>(null)

export interface FBAMapProps {
  testId?: string
  center: number[]
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
  const mapRef = useRef<HTMLDivElement | null>(null)
  const [map, setMap] = useState<ol.Map | null>(null)
  useEffect(() => {
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({ zoom, center: fromLonLat(props.center) }),
      layers: [
        new TileLayer({
          source: new OSM()
        })
      ],
      overlays: [],
      controls: defaultControls()
    }

    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)
    setMap(mapObject)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ErrorBoundary>
      <div className={classes.main}>
        <context.Provider value={map}>
          <div ref={mapRef} data-testid="fba-map" className={classes.map}></div>
        </context.Provider>
      </div>
    </ErrorBoundary>
  )
}

export default React.memo(FBAMap)
