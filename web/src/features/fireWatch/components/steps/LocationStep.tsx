import { FireWatch } from '@/features/fireWatch/interfaces'
import React, { SetStateAction, useEffect, useRef, useState } from 'react'
import { Collection, Map, MapBrowserEvent, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import { fromLonLat } from 'ol/proj'
import { CENTER_OF_BC } from '@/utils/constants'
import { Alert, Box, Snackbar, Step, Typography } from '@mui/material'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import { theme } from 'app/theme'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import Feature from 'ol/Feature.js'
import VectorSource from 'ol/source/Vector.js'
import VectorLayer from 'ol/layer/Vector.js'
import { Icon, Style } from 'ol/style'
import { Geometry, Point } from 'ol/geom'
import Translate from 'ol/interaction/Translate.js'
import { isUndefined } from 'lodash'
import { defaults as defaultInteractions } from 'ol/interaction/defaults'

export const MapContext = React.createContext<Map | null>(null)

interface LocationStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
  showLocationError?: boolean
  onCloseLocationError?: () => void
}

const LocationStep = ({ fireWatch, setFireWatch, showLocationError, onCloseLocationError }: LocationStepProps) => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>
  const [marker, setMarker] = useState<Feature<Geometry>[]>(
    !isUndefined(fireWatch.geometry) ? [new Feature({ geometry: new Point(fireWatch.geometry) })] : []
  )
  const [featureSource] = useState<VectorSource>(new VectorSource({ features: marker }))

  // Clear all interactions in order to remove the Translate interaction
  // and restore the original interactions in the correct order.
  const resetMapInteractions = () => {
    map?.getInteractions().clear()
    defaultInteractions({}).forEach(interaction => map?.addInteraction(interaction))
  }

  useEffect(() => {
    // Clear and update the feature source so the newly created feature renders on the map.
    featureSource.clear()
    featureSource.addFeatures(marker)

    // Clear out the old translate interaction and add a new one for the new feature.
    resetMapInteractions()
    const newTranslate = new Translate({
      features: new Collection(marker)
    })
    newTranslate.on('translateend', evt => {
      handleFormUpdate({ geometry: evt.coordinate })
    })
    map?.addInteraction(newTranslate)
  }, [marker])

  useEffect(() => {
    if (!mapRef.current) {
      return
    }
    const featureLayer = new VectorLayer({
      source: featureSource,
      style: new Style({
        image: new Icon({
          anchor: [0.5, 1],
          height: 32,
          src: '/images/redMarker.png'
        })
      }),
      zIndex: 50
    })
    const mapObject = new Map({
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      }),
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        featureLayer
      ]
    })
    mapObject.setTarget(mapRef.current)
    setMap(mapObject)
    return () => {
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    // Click handler to allow user to click on map to place a marker.
    const handleMapClick = (evt: MapBrowserEvent<UIEvent>) => {
      handleFormUpdate({ geometry: evt.coordinate })
      const newFeature = new Feature({
        geometry: new Point(evt.coordinate)
      })
      setMarker([newFeature])
    }
    map?.on('singleclick', evt => handleMapClick(evt))

    // Allow dragging of the marker.
    const translate = new Translate({
      features: new Collection(marker)
    })
    translate.on('translateend', evt => {
      handleFormUpdate({ geometry: evt.coordinate })
    })
    map?.addInteraction(translate)
  }, [map]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleFormUpdate = (partialFireWatch: Partial<FireWatch>) => {
    const newFireWatch = { ...fireWatch, ...partialFireWatch }
    setFireWatch(newFireWatch)
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Box sx={{ pb: theme.spacing(2) }}>
          <Typography sx={{ pb: theme.spacing(2) }} variant="h6">
            Step 2: Burn Location
          </Typography>
          <Typography variant="body1">Click on the map to choose the approximate location of the burn.</Typography>
        </Box>
        <MapContext.Provider value={map}>
          <Box
            ref={mapRef}
            data-testid="fba-map"
            sx={{ height: 0.65 * FORM_MAX_WIDTH, width: 0.9 * FORM_MAX_WIDTH }}
          ></Box>
        </MapContext.Provider>
      </Box>
      <Snackbar
        open={showLocationError}
        autoHideDuration={4000}
        onClose={onCloseLocationError}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={onCloseLocationError} severity="error" sx={{ width: '100%' }}>
          Please select a burn location before continuing.
        </Alert>
      </Snackbar>
    </Step>
  )
}

export default LocationStep
