import React, { useRef, useState, useEffect } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import * as ol from 'ol'
import 'ol/ol.css'
import { FeatureLike } from 'ol/Feature'
import OLOverlay from 'ol/Overlay'
import { MapOptions } from 'ol/PluggableMap'

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
    },
    '& .ol-popup': {
      position: 'absolute',
      backgroundColor: 'white',
      boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
      padding: 15,
      borderRadius: 10,
      border: '1px solid #cccccc',
      bottom: 12,
      whiteSpace: 'nowrap',

      // Center absolutely positioned content of unknown width
      // https://stackoverflow.com/a/9367930/11903963
      left: '50%',
      width: 'auto',
      transform: 'translateX(-50%)'
    }
  }
})

interface Props {
  children: React.ReactNode
  zoom: number
  center: number[]
  renderHoverTooltip?: (feature: FeatureLike | null) => React.ReactNode
}

const Map = ({ children, zoom, center, renderHoverTooltip }: Props) => {
  const classes = useStyles()
  const overlayRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [feature, setFeature] = useState<FeatureLike | null>(null)

  // on component mount
  useEffect(() => {
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({ zoom, center }),
      layers: [],
      overlays: []
    }
    let overlay: OLOverlay | undefined

    const mapObject = new ol.Map(options)
    mapObject.setTarget(mapRef.current)
    setMap(mapObject)

    // Wish we can separate this part, but adding a listener like this only works
    // in the context where map object is initialized
    if (overlayRef.current) {
      overlay = new OLOverlay({
        element: overlayRef.current,
        autoPan: true,
        autoPanAnimation: {
          duration: 250
        }
      })
      mapObject.addOverlay(overlay)
      mapObject.on('pointermove', e => {
        overlay?.setPosition(undefined)

        mapObject.forEachFeatureAtPixel(e.pixel, function(feature) {
          overlay?.setPosition(e.coordinate)
          setFeature(feature)

          return true
        })
      })
    }

    return () => {
      mapObject.setTarget(undefined)
      overlay && mapObject.removeOverlay(overlay)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
      {renderHoverTooltip && (
        <div ref={overlayRef} className="ol-popup">
          {renderHoverTooltip(feature)}
        </div>
      )}
    </MapContext.Provider>
  )
}

export default React.memo(Map)
