import { ErrorBoundary } from '@/components'
import { removeLayerByName } from '@/features/fba/components/map/FBAMap'
import { firePerimeterStyler } from '@/features/riskMap/components/fireMapStylers'
import { closestFeatureStats } from '@/features/riskMap/components/featureDistance'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle } from '@mui/material'
import { buffer } from '@turf/turf'
import { selectHotSpots, selectRepStations } from 'app/rootReducer'
import { DateTime } from 'luxon'
import { Feature, Map, View } from 'ol'
import { boundingExtent } from 'ol/extent'
import GeoJSON from 'ol/format/GeoJSON'
import { Geometry, Point, Polygon } from 'ol/geom'
import { DragBox, Select } from 'ol/interaction'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import { Fill, Stroke, Style } from 'ol/style'
import React, { useEffect, useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import { platformModifierKeyOnly } from 'ol/events/condition'
import { collectFeaturesWithin } from '@/features/riskMap/components/selectionDragBox'
import { DetailsDrawer } from '@/features/riskMap/components/DetailsDrawer'

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const findLayerByName = (map: Map, layerName: string): VectorLayer | undefined => {
  const layers = map.getLayers().getArray()
  return layers.find(layer => layer.get('name') === layerName) as VectorLayer | undefined
}

const getCompassDirection = (bearing: number) => {
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const index = Math.round((((bearing % 360) + 360) % 360) / 45)
  return directions[index]
}

export interface FireMapProps {
  valuesFile: File | null
  setMapInstance: React.Dispatch<React.SetStateAction<Map | null>>
  dateOfInterest: DateTime
  spreadDistance: number
}

export const FireMap: React.FC<FireMapProps> = ({
  valuesFile,
  setMapInstance,
  dateOfInterest,
  spreadDistance
}: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)
  const { hotSpotPoints } = useSelector(selectHotSpots)
  const { repStations } = useSelector(selectRepStations)

  const [map, setMap] = useState<Map | null>(null)
  const [open, setOpen] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [featureSelection, setFeatureSelection] = useState<Feature<Geometry>[]>([])
  const [valuesFeatures, setValuesFeatures] = useState<Feature<Geometry>[]>([])
  const [closestDistance, setClosestDistance] = useState<number | null>(null)
  const [closestDirection, setClosestDirection] = useState<string>('')
  const [uploadedFeatureDetails, setUploadedFeatureDetails] = useState<any | null>(null)

  // Create a vector layer to hold the selection boxes
  const boxLayerSource = new VectorSource()
  const boxLayer = new VectorLayer({
    source: boxLayerSource,
    style: new Style({
      stroke: new Stroke({
        color: 'blue',
        width: 2
      }),
      fill: new Fill({
        color: 'rgba(0, 0, 255, 0.2)'
      })
    })
  })

  const firePerimeterSource = new VectorSource({
    features: new GeoJSON().readFeatures(firePerimeterData, {
      featureProjection: 'EPSG:3857'
    })
  })

  const firePerimeterLayer = new VectorLayer({
    style: firePerimeterStyler,
    source: firePerimeterSource,
    zIndex: 50,
    properties: { name: 'firePerimeter' }
  })

  useEffect(() => {
    if (!map) return
    const layerName = 'hotSpots'
    removeLayerByName(map, layerName)

    if (hotSpotPoints) {
      const features = new GeoJSON().readFeatures(hotSpotPoints)
      const geoJSON = new GeoJSON().writeFeaturesObject(features, {
        featureProjection: 'EPSG:4326'
      })

      const buffered = buffer(geoJSON, spreadDistance, { units: 'meters' })
      const bufferedFeature = new GeoJSON().readFeatures(buffered, {
        featureProjection: 'EPSG:3857'
      })

      const hotSpotsLayer = new VectorLayer({
        style: new Style({
          fill: new Fill({
            color: 'rgba(255, 0, 13, 0.27)' // Semi-transparent green
          }),
          stroke: new Stroke({
            color: '#FF0000', // Red border
            width: 3
          })
        }),
        source: new VectorSource({
          features: bufferedFeature
        }),
        zIndex: 52,
        properties: { name: layerName }
      })
      map.addLayer(hotSpotsLayer)
    }
  }, [spreadDistance, hotSpotPoints])

  // uploaded values layer manager
  useEffect(() => {
    if (valuesFile && mapInstanceRef.current) {
      const reader = new FileReader()

      reader.onload = e => {
        if (e.target && e.target.result) {
          try {
            const geojsonData = JSON.parse(e.target.result as string)
            const valuesGeoJson = new GeoJSON().readFeatures(geojsonData, {
              featureProjection: 'EPSG:3857'
            })
            const vectorSource = new VectorSource({
              features: valuesGeoJson
            })

            const vectorLayer = new VectorLayer({
              source: vectorSource,
              zIndex: 1000,
              properties: { name: 'uploadedValues' }
            })

            mapInstanceRef.current?.addLayer(vectorLayer)

            setValuesFeatures(valuesGeoJson)
          } catch (error) {
            console.error('Error parsing GeoJSON data:', error)
          }
        }
      }

      reader.readAsText(valuesFile)
    }
  }, [valuesFile, featureSelection, mapInstanceRef.current])

  // create and set featureDetails
  useEffect(() => {
    if (!map) return

    const hotSpotsLayer = findLayerByName(map, 'hotSpots')
    const source = hotSpotsLayer?.getSource()
    const hotSpotFeatures = source?.getFeatures()
    if (!hotSpotFeatures) return

    const featureDetails = valuesFeatures.map(feature => {
      const geometry = feature.getGeometry() as Point
      const geometryType = geometry?.getType()
      return {
        id: feature.getId(),
        properties: feature.getProperties(),
        geometryType: geometryType,
        extent: geometry?.getExtent(),
        riskDetails: closestFeatureStats(hotSpotFeatures, geometry.getCoordinates())
      }
    })
    setUploadedFeatureDetails(featureDetails)
  }, [valuesFeatures, hotSpotPoints, spreadDistance, map])

  useEffect(() => {
    console.log('yes')
  }, [valuesFeatures, featureSelection])

  useEffect(() => {
    if (!mapInstanceRef.current) {
      const map = new Map({
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          }),
          firePerimeterLayer
        ],
        view: new View({
          center: fromLonLat(CENTER_OF_BC),
          zoom: 5
        })
      })

      map.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

      map.addLayer(boxLayer)

      // a normal select interaction to handle click
      const select = new Select()
      map.addInteraction(select)

      const selectedFeatures = select.getFeatures()

      // a DragBox interaction used to select features by drawing boxes
      const dragBox = new DragBox({
        condition: platformModifierKeyOnly
      })

      map.addInteraction(dragBox)

      dragBox.on('boxend', function (event) {
        const hotspotsLayer = findLayerByName(map, 'hotSpots')
        const source = hotspotsLayer!.getSource()
        if (source) {
          const newSelectedFeatures = collectFeaturesWithin(dragBox, map, source, selectedFeatures)
          if (newSelectedFeatures) {
            console.log(newSelectedFeatures)
            setFeatureSelection(newSelectedFeatures)
          }
          setDetailsOpen(true)
        }

        // Get the geometry of the drag box
        const boxGeometry = dragBox.getGeometry()

        // Create a new feature with the box geometry
        const boxFeature = new Feature({
          geometry: new Polygon(boxGeometry.getCoordinates())
        })

        // Add the feature to the vector layer
        boxLayerSource.addFeature(boxFeature)
      })

      // clear selection when drawing a new box and when clicking on the map
      dragBox.on('boxstart', function () {
        selectedFeatures.clear()
        boxLayerSource.clear() // Clear all rendered boxes
        // setFeatureSelection([])
      })

      // Clear boxes on double click
      map.on('dblclick', () => {
        selectedFeatures.clear()
        boxLayerSource.clear() // Clear all rendered boxes
        setFeatureSelection([])
      })

      const selectClick = new Select({
        condition: event => {
          return event.type === 'singleclick'
        }
      })

      selectClick.on('select', event => {
        if (event.selected.length > 0) {
          const selectedFeature = event.selected[0]
          map.forEachFeatureAtPixel(event.mapBrowserEvent.pixel, (feature, layer) => {
            if (layer.get('name') === 'representativeStationLayer') {
              console.log(feature.getProperties())
            }
            if (layer.get('name') === 'uploadedValues' && findLayerByName(map, 'hotSpots')) {
              const selectedGeometry = selectedFeature.getGeometry() as Point

              const selectedPointCoords = selectedGeometry?.getCoordinates()

              const hotspotsLayer = findLayerByName(map, 'hotSpots')
              const source = hotspotsLayer!.getSource()
              const features = source!.getFeatures()

              const closestResult = closestFeatureStats(features, selectedPointCoords)

              if (closestResult.closestFeature) {
                setClosestDistance(closestResult.closestDistance)
                setClosestDirection(getCompassDirection(closestResult.closestBearing))
                setOpen(true) // Open the dialog
              }
            }
          })
          //   if (layer.getProperties().name === 'firePerimeter') {
          //     const fireGeom = selectedFeature.getGeometry()
          //     if (fireGeom) {
          //       const firePolygon = new GeoJSON().writeFeatureObject(selectedFeature)
          //       console.log('buffering')
          //       const bufferedFirePolygon = buffer(firePolygon, 2, { units: 'kilometers' })
          //       console.log('calculating')
          //       const filteredHotspots = pointsWithinPolygon(hotspotFeatureCollection, bufferedFirePolygon!)
          //       console.log(filteredHotspots)
          //     }
          //   }
          // })

          // --------------------
        }
      })

      mapInstanceRef.current = map
      setMapInstance(map)
      setMap(map)
      map.addInteraction(selectClick)
    }
  }, [])

  const handleClose = () => {
    setOpen(false)
    setClosestDistance(null)
    setClosestDirection('')
  }

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box
          ref={mapRef}
          data-testid="risk-map"
          sx={{
            display: 'flex',
            flex: 1,
            position: 'relative'
          }}
        >
          <DetailsDrawer
            values={valuesFeatures}
            hotspots={featureSelection}
            setOpen={setDetailsOpen}
            open={detailsOpen}
          />

          <Dialog open={open} onClose={handleClose} sx={{ position: 'absolute', zIndex: '1', bottom: '0.5rem' }}>
            <DialogTitle>Closest Distance</DialogTitle>
            <DialogContent>
              {closestDistance !== null && closestDirection ? (
                <>
                  <p>Closest Distance: {closestDistance.toPrecision(2)} km</p>
                  <p>Direction: {closestDirection}</p>
                  <p>
                    Risk Level:
                    <span
                      style={{
                        color: closestDistance < 5 ? 'red' : closestDistance <= 10 ? 'orange' : 'black'
                      }}
                    >
                      {closestDistance < 5 ? ' High Risk' : closestDistance <= 10 ? ' Mid Risk' : ' Low Risk'}
                    </span>
                  </p>
                </>
              ) : (
                <p>No distance calculated.</p>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={handleClose} color="primary">
                Close
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </MapContext.Provider>
    </ErrorBoundary>
  )
}
