import { ErrorBoundary } from '@/components'
import { removeLayerByName } from '@/features/fba/components/map/FBAMap'
import { closestFeatureStats } from '@/features/riskMap/components/featureDistance'
import { firePerimeterStyler, highlightFeature, resetLayerStyle } from '@/features/riskMap/components/fireMapStylers'
import { findLayerByName, getFeatureIdsInViewport, zoomToFeatureWithBuffer } from '@/features/riskMap/mapFunctions'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Box } from '@mui/material'
import { buffer } from '@turf/turf'
import { selectHotSpots } from 'app/rootReducer'
import { Feature, Map, View } from 'ol'
import { boundingExtent } from 'ol/extent'
import GeoJSON from 'ol/format/GeoJSON'
import { Geometry, Point } from 'ol/geom'
import { Select } from 'ol/interaction'
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

export const MapContext = React.createContext<Map | null>(null)
const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

export interface FireMapProps {
  values: Feature<Geometry>[]
  setMapInstance: React.Dispatch<React.SetStateAction<Map | null>>
  setFilteredValues: React.Dispatch<React.SetStateAction<number[]>>
  spreadDistance: number
  selectedID: number | null
}

export const FireMap: React.FC<FireMapProps> = ({
  values,
  setMapInstance,
  setFilteredValues,
  spreadDistance,
  selectedID
}: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)
  const { hotSpotPoints } = useSelector(selectHotSpots)

  const [map, setMap] = useState<Map | null>(null)

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
    if (values && values.length > 0) {
      const vectorSource = new VectorSource({
        features: values
      })

      const vectorLayer = new VectorLayer({
        source: vectorSource,
        zIndex: 1000,
        properties: { name: 'uploadedValues' }
      })

      mapInstanceRef.current?.addLayer(vectorLayer)
    }
  }, [values])

  useEffect(() => {
    if (!selectedID || !map) return

    resetLayerStyle(map, 'uploadedValues')
    highlightFeature(map, 'uploadedValues', selectedID)

    zoomToFeatureWithBuffer(map, selectedID, 15)
  }, [selectedID])

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

      // Attach a listener to detect when the map stops moving
      map.on('moveend', () => {
        const filtered = getFeatureIdsInViewport(map, 'uploadedValues')

        setFilteredValues(filtered)
      })

      // Optional: React to zoom level changes specifically
      map.getView().on('change:resolution', () => {
        const filtered = getFeatureIdsInViewport(map, 'uploadedValues')
        setFilteredValues(filtered)
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
            console.log(feature.getProperties())

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
                // setClosestDistance(closestResult.closestDistance)
                // setClosestDirection(getCompassDirection(closestResult.closestBearing))
                // setOpen(true) // Open the dialog
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

  return (
    <ErrorBoundary>
      <MapContext.Provider value={map}>
        <Box
          ref={mapRef}
          data-testid="risk-map"
          sx={{
            display: 'flex',
            flexGrow: 1,
            height: '100%'
          }}
        />
      </MapContext.Provider>
    </ErrorBoundary>
  )
}
