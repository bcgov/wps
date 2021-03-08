import React, { useRef, useState, useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import * as ol from 'ol'
import 'ol/ol.css'

export const MapContext = React.createContext<ol.Map | null>(null)

const useStyles = makeStyles({
  map: {
    width: '100%',
    height: 500,

    '& .ol-control': {
      position: 'absolute',
      backgroundColor: 'rgba(255,255,255,0.7)',
      borderRadius: 4,
      padding: 2
    }
  }
})

interface Props {
  children: React.ReactNode
  zoom: number
  center: number[]
}

const Map = ({ children, zoom, center }: Props) => {
  const classes = useStyles()
  const mapRef = useRef<HTMLDivElement | null>(null)
  const [map, setMap] = useState<ol.Map | null>(null)

  // on component mount
  useEffect(() => {
    const options = {
      view: new ol.View({ zoom, center }),
      layers: [],
      overlays: []
    }

    const mapObject = new ol.Map(options)

    if (mapRef.current) {
      mapObject.setTarget(mapRef.current)
      setMap(mapObject)
    }

    return () => mapObject.setTarget(undefined)
  }, [mapRef.current]) // eslint-disable-line react-hooks/exhaustive-deps

  // zoom change handler
  useEffect(() => {
    if (!map) return

    map.getView().setZoom(zoom)
  }, [zoom]) // eslint-disable-line react-hooks/exhaustive-deps

  // center change handler
  useEffect(() => {
    if (!map) return

    map.getView().setCenter(center)
  }, [center]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <MapContext.Provider value={map}>
      <div ref={mapRef} className={classes.map}>
        {children}
      </div>
    </MapContext.Provider>
  )
}

export default React.memo(Map)
