import { AppDispatch } from '@/app/store'
import { ErrorBoundary } from '@/components'
import { removeLayerByName } from '@/features/fba/components/map/FBAMap'
import { firePerimeterStyler } from '@/features/riskMap/components/fireMapStylers'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle } from '@mui/material'
import { bearing, distance, point, buffer } from '@turf/turf'
import { getDetailedStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations, selectHotSpots, selectRepStations } from 'app/rootReducer'
import { DateTime } from 'luxon'
import { Feature, Map, View } from 'ol'
import { boundingExtent } from 'ol/extent'
import GeoJSON from 'ol/format/GeoJSON'
import { Geometry, Point } from 'ol/geom'
import { DragBox, Select } from 'ol/interaction'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import 'ol/ol.css'
import { fromLonLat, toLonLat } from 'ol/proj'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import { Fill, Stroke, Style } from 'ol/style'
import CircleStyle from 'ol/style/Circle'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import { groupBy, partition } from 'lodash'
import { decorateRepStations } from '@/features/riskMap/components/representativeStations'
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
}

export const FireMap: React.FC<FireMapProps> = ({ valuesFile, setMapInstance, dateOfInterest }: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)
  const { hotSpotPoints } = useSelector(selectHotSpots)
  const { repStations } = useSelector(selectRepStations)

  const [map, setMap] = useState<Map | null>(null)
  const [open, setOpen] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [featureSelection, setFeatureSelection] = useState<Feature<Geometry>[]>([])
  const [closestDistance, setClosestDistance] = useState<number | null>(null)
  const [closestDirection, setClosestDirection] = useState<string>('')
  const { stations } = useSelector(selectFireWeatherStations)
  const dispatch: AppDispatch = useDispatch()

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
    dispatch(fetchWxStations(getDetailedStations, StationSource.unspecified))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const memoizedSelectedFeatures = useMemo(() => [...featureSelection], [featureSelection])
  useEffect(() => {
    if (repStations.length > 0 && memoizedSelectedFeatures.length > 0) {
      const selectedFires = memoizedSelectedFeatures.map(feat => feat.getProperties()['FIRE_NUMBER'])
      console.log(selectedFires)
      const repStationsByFireNumber = groupBy(repStations, repStation => repStation.fire_number)
      console.log(selectedFires.map(sf => repStationsByFireNumber[sf][0]))
    }
  }, [memoizedSelectedFeatures, repStations])

  useEffect(() => {
    if (stations.length !== 0 || repStations.length !== 0) {
      const repStationCodes = repStations.map(repStation => repStation.station_code)
      const [rStations, nonRStations] = partition(stations, station =>
        repStationCodes.includes(station.properties.code)
      )
      const res = decorateRepStations(rStations, repStations)
      const stationLayer = new VectorLayer({
        style: () =>
          new Style({
            image: new CircleStyle({
              radius: 4,
              fill: new Fill({ color: 'black' }),
              stroke: new Stroke({ color: 'black', width: 1 })
            })
          }),
        source: new VectorSource({
          features: new GeoJSON().readFeatures(
            { type: 'FeatureCollection', features: nonRStations },
            {
              featureProjection: 'EPSG:3857'
            }
          )
        }),
        zIndex: 99,
        properties: { name: 'stationLayer' }
      })
      const repStationLayer = new VectorLayer({
        style: () =>
          new Style({
            image: new CircleStyle({
              radius: 4,
              fill: new Fill({ color: 'purple' }),
              stroke: new Stroke({ color: 'purple', width: 1 })
            })
          }),
        source: new VectorSource({
          features: new GeoJSON().readFeatures(
            { type: 'FeatureCollection', features: res },
            {
              featureProjection: 'EPSG:3857'
            }
          )
        }),
        zIndex: 100,
        properties: { name: 'representativeStationLayer' }
      })
      mapInstanceRef.current?.addLayer(stationLayer)
      mapInstanceRef.current?.addLayer(repStationLayer)
    }
  }, [stations, repStations])

  useEffect(() => {
    if (!map) return
    const layerName = 'hotSpots'
    removeLayerByName(map, layerName)

    if (hotSpotPoints) {
      const features = new GeoJSON().readFeatures(hotSpotPoints)
      const geoJSON = new GeoJSON().writeFeaturesObject(features, {
        featureProjection: 'EPSG:4326'
      })

      const buffered = buffer(geoJSON, 20, { units: 'kilometers' })
      const bufferedFeature = new GeoJSON().readFeatures(buffered, {
        featureProjection: 'EPSG:3857'
      })

      const hotSpotsLayer = new VectorLayer({
        style: new Style({
          fill: new Fill({
            color: 'rgba(0, 255, 0, 0.5)' // Semi-transparent green
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
      console.log(hotSpotsLayer.getSource()?.getFeatures())
      console.log(hotSpotsLayer.getVisible())
      map.addLayer(hotSpotsLayer)
    }
  })

  useEffect(() => {
    if (valuesFile && mapInstanceRef.current) {
      const reader = new FileReader()

      reader.onload = e => {
        if (e.target && e.target.result) {
          try {
            const geojsonData = JSON.parse(e.target.result as string)

            const vectorSource = new VectorSource({
              features: new GeoJSON().readFeatures(geojsonData, {
                featureProjection: 'EPSG:3857'
              })
            })

            const vectorLayer = new VectorLayer({
              source: vectorSource,
              properties: { name: 'uploadedValues' }
            })

            mapInstanceRef.current?.addLayer(vectorLayer)
          } catch (error) {
            console.error('Error parsing GeoJSON data:', error)
          }
        }
      }

      reader.readAsText(valuesFile)
    }
  }, [valuesFile, mapInstanceRef.current])

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

      const selectedStyle = new Style({
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.6)'
        }),
        stroke: new Stroke({
          color: 'rgba(255, 255, 255, 0.7)',
          width: 2
        })
      })

      // a normal select interaction to handle click
      const select = new Select({
        style: function () {
          selectedStyle.getFill()?.setColor('#eeeeee')
          return selectedStyle
        }
      })
      map.addInteraction(select)

      const selectedFeatures = select.getFeatures()

      // a DragBox interaction used to select features by drawing boxes
      const dragBox = new DragBox({
        condition: platformModifierKeyOnly
      })

      map.addInteraction(dragBox)

      dragBox.on('boxend', function (event) {
        const featureSelection = collectFeaturesWithin(dragBox, map, firePerimeterSource, selectedFeatures)
        if (featureSelection) {
          setFeatureSelection(featureSelection)
        }
        setDetailsOpen(true)
      })

      // clear selection when drawing a new box and when clicking on the map
      dragBox.on('boxstart', function () {
        selectedFeatures.clear()
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
            if (layer.get('name') === 'uploadedValues' && findLayerByName(map, 'firePerimDay4')) {
              const selectedGeometry = selectedFeature.getGeometry() as Point

              const selectedPointCoords = selectedGeometry?.getCoordinates()
              const lonLatCoords = toLonLat(selectedPointCoords)

              const fireLayer = findLayerByName(map, 'firePerimDay4')
              const source = fireLayer!.getSource()
              const features = source!.getFeatures()

              let closestDistance = Infinity
              let closestFeature = null
              let closestBearing = 0

              features.forEach((layerFeature: Feature) => {
                const geometry = layerFeature.getGeometry()
                if (geometry) {
                  const closestPoint = geometry.getClosestPoint(selectedPointCoords)
                  const closestPointLonLat = toLonLat(closestPoint)

                  const turfPointA = point(lonLatCoords)
                  const turfPointB = point(closestPointLonLat)

                  const dist = distance(turfPointA, turfPointB, { units: 'kilometers' })
                  const bearingAngle = bearing(turfPointA, turfPointB)

                  if (dist < closestDistance) {
                    closestDistance = dist
                    closestFeature = layerFeature
                    closestBearing = bearingAngle
                  }
                }
              })

              if (closestFeature) {
                setClosestDistance(closestDistance)
                setClosestDirection(getCompassDirection(closestBearing))
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
            repStations={repStations}
            featureSelection={featureSelection}
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
