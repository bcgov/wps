import { FireWatch } from '@/features/fireWatch/interfaces'
import React, { SetStateAction, useEffect, useRef, useState } from 'react'
import { Collection, Map, MapBrowserEvent, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import { fromLonLat, toLonLat } from 'ol/proj'
import { CENTER_OF_BC } from '@/utils/constants'
import { Box, Step, TextField, Typography } from '@mui/material'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import { theme } from 'app/theme'
import Feature from 'ol/Feature.js'
import VectorSource from 'ol/source/Vector.js'
import VectorLayer from 'ol/layer/Vector.js'
import { Icon, Style } from 'ol/style'
import { Geometry, Point } from 'ol/geom'
import Translate from 'ol/interaction/Translate.js'
import { defaults as defaultInteractions } from 'ol/interaction/defaults'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/constants'

export const MapContext = React.createContext<Map | null>(null)

interface LocationStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const LocationStep = ({ fireWatch, setFireWatch }: LocationStepProps) => {
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>

  const isValidGeometry =
    Array.isArray(fireWatch.geometry) &&
    fireWatch.geometry.length === 2 &&
    typeof fireWatch.geometry[0] === 'number' &&
    typeof fireWatch.geometry[1] === 'number'

  const [marker, setMarker] = useState<Feature<Geometry>[]>(
    isValidGeometry ? [new Feature({ geometry: new Point(fireWatch.geometry) })] : []
  )
  const [featureSource] = useState<VectorSource>(new VectorSource({ features: marker }))
  const [latInput, setLatInput] = useState(isValidGeometry ? toLonLat(fireWatch.geometry)[1].toFixed(6) : '')
  const [lonInput, setLonInput] = useState(isValidGeometry ? toLonLat(fireWatch.geometry)[0].toFixed(6) : '')
  const [editingField, setEditingField] = useState<'lat' | 'lon' | null>(null)

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

  // sync textfields with marker coords
  useEffect(() => {
    if (marker.length && marker[0].getGeometry()) {
      const [lon, lat] = toLonLat((marker[0].getGeometry() as Point).getCoordinates())
      setLatInput(lat.toFixed(6))
      setLonInput(lon.toFixed(6))
    }
  }, [marker])

  // when user finishes editing both fields, update marker
  const updateMarkerFromInputs = () => {
    if (!latInput || !lonInput) {
      setMarker([])
      handleFormUpdate({ geometry: undefined })
      return
    }
    const lat = parseFloat(latInput)
    const lon = parseFloat(lonInput)
    if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
      const coords = fromLonLat([lon, lat])
      setMarker([new Feature({ geometry: new Point(coords) })])
      handleFormUpdate({ geometry: coords })
    }
  }

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
          <Typography variant="body1">
            Click on the map to choose the approximate location of the burn OR enter latitude and longitude in decimal
            degrees.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            required
            label="Latitude"
            value={latInput}
            onChange={e => {
              setLatInput(e.target.value)
            }}
            onFocus={() => setEditingField('lat')}
            onBlur={() => {
              setEditingField(null)
              if (editingField !== 'lon') updateMarkerFromInputs()
            }}
            inputProps={{ 'data-testid': 'lat-input' }}
            size="small"
          />
          <TextField
            required
            label="Longitude"
            value={lonInput}
            onChange={e => {
              setLonInput(e.target.value)
            }}
            onFocus={() => setEditingField('lon')}
            onBlur={() => {
              setEditingField(null)
              if (editingField !== 'lat') updateMarkerFromInputs()
            }}
            inputProps={{ 'data-testid': 'lon-input' }}
            size="small"
          />
        </Box>
        <MapContext.Provider value={map}>
          <Box
            ref={mapRef}
            data-testid="fba-map"
            sx={{ height: 0.65 * FORM_MAX_WIDTH, width: 0.9 * FORM_MAX_WIDTH }}
          ></Box>
        </MapContext.Provider>
      </Box>
    </Step>
  )
}

export default LocationStep
