import 'ol/ol.css'

import React, { useRef, useState, useEffect, useCallback } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import * as ol from 'ol'
import { toLonLat } from 'ol/proj'
import { FeatureLike } from 'ol/Feature'
import OLOverlay from 'ol/Overlay'
import { MapOptions } from 'ol/PluggableMap'
import { defaults as defaultControls } from 'ol/control'

import { Button, ErrorBoundary } from 'components'
import { ObjectEvent } from 'ol/Object'
import { useDispatch } from 'react-redux'
import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import { selectStation } from 'features/stations/slices/stationsSlice'
import FireIndicesVectorLayer from 'features/fireWeather/components/maps/FireIndicesVectorLayer'

const zoom = 6

export const MapContext = React.createContext<ol.Map | null>(null)
export interface RedrawCommand {
  redraw: boolean
}

const useStyles = makeStyles({
  map: {
    position: 'relative',
    width: '100%',
    height: '100%',

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
  center: number[]
  isCollapsed: boolean
  selectedWxVariable: AccuracyWeatherVariableEnum
  toiFromQuery: string
  setMapCenter: (newCenter: number[]) => void
  redrawFlag?: RedrawCommand
}

const Map = ({ children, center, redrawFlag, isCollapsed, selectedWxVariable, toiFromQuery, setMapCenter }: Props) => {
  const classes = useStyles()
  const overlayRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null)
  const [map, setMap] = useState<ol.Map | null>(null)
  const [feature, setFeature] = useState<FeatureLike | null>(null)
  const [currentCenter, setCurrentCenter] = useState(center)

  // on component mount
  useEffect(() => {
    if (!mapRef.current) return

    const options: MapOptions = {
      view: new ol.View({ zoom, center }),
      layers: [],
      overlays: [],
      controls: defaultControls()
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
        autoPan: { animation: { duration: 250 } }
      })

      mapObject.addOverlay(overlay)

      // Hover listener for changing the mouse cursor when hovering features
      mapObject.on('pointermove', e => {
        mapObject.getViewport().style.cursor = ''
        mapObject.forEachFeatureAtPixel(e.pixel, () => {
          mapObject.getViewport().style.cursor = 'pointer'
        })
      })

      // Click listener for displaying the popup
      mapObject.on('singleclick', e => {
        // Hide the overlay if previously displayed
        overlay?.setPosition(undefined)

        mapObject.forEachFeatureAtPixel(e.pixel, (f: FeatureLike) => {
          overlay?.setPosition(e.coordinate)
          setFeature(f)

          return true
        })
      })
    }

    // Center change listener to update our current center
    mapObject.getView().on('change:center', (event: ObjectEvent) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setCurrentCenter((event.target as any).values_.center)
    })

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

  // center change if side panel collapses
  useEffect(() => {
    if (!map) return

    setMapCenter(toLonLat(currentCenter))
  }, [isCollapsed]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map) return

    // Wait for 0.1s the side panel to completely collapse then resize the map
    setTimeout(() => {
      map.updateSize()
    }, 100)
  }, [redrawFlag]) // eslint-disable-line react-hooks/exhaustive-deps

  const dispatch = useDispatch()
  const renderTooltip = useCallback(
    (featureToRender: FeatureLike | null) => {
      if (!featureToRender) return null

      return (
        <div data-testid={`station-${featureToRender.get('code')}-tooltip`}>
          <p>
            {featureToRender.get('name')} ({featureToRender.get('code')})
          </p>
          <Button
            variant="outlined"
            size="small"
            onClick={() => {
              dispatch(selectStation(featureToRender.get('code')))
            }}
            data-testid={`select-wx-station-${featureToRender.get('code')}-button`}
          >
            Select
          </Button>
        </div>
      )
    },
    [dispatch]
  )

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <div ref={mapRef} className={classes.map} data-testid="map">
          {children}
          <FireIndicesVectorLayer toiFromQuery={toiFromQuery} selectedWxVariable={selectedWxVariable} />
        </div>
        {renderTooltip && (
          <div ref={overlayRef} className="ol-popup">
            {renderTooltip(feature)}
          </div>
        )}
      </MapContext.Provider>
    </ErrorBoundary>
  )
}

export default React.memo(Map)
