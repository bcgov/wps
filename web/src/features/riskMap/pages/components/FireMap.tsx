import React, { useEffect, useRef } from 'react'
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat, toLonLat } from 'ol/proj'
import { CENTER_OF_BC } from '@/utils/constants'
import { Fill, Style } from 'ol/style'
import { Feature, FeatureCollection } from 'geojson'
import { Select, DragBox } from 'ol/interaction'
import { shiftKeyOnly } from 'ol/events/condition'
import { defaults as defaultControls } from 'ol/control'
import axios, { raster } from 'api/axios'

import { shiftPolygon, spreadInDirection } from '@/features/riskMap/pages/components/fireSpreader'
import { getCoords, polygon } from '@turf/turf'
import Polygon from 'ol/geom/Polygon'
import { GrowControl } from '@/features/riskMap/pages/components/GrowControl'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './FirespotArea_canada_c6.1_48.json'

const HOTSPOT_LAYER = 'Hotspot_Layer'
const SPREAD_HOTSPOT_LAYER = 'Spread_Hotspot_Layer'
const FIRE_PERIMETER_LAYER = 'Fire_Perimeter_Layer'

// Method to trigger the fetch request
const growFire = async () => {
  try {
    const url = `risk-map/grow`
    const { data } = await axios.post(url, {
      fire_perimeter: {
        features: firePerimeterData.features
      },
      hostpots: {
        features: hotspots.features
      }
    })
    return data
  } catch (error) {
    console.error('Error fetching data:', error)
  }
}

export const FireMap: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  const loadGeoJSON = async (fileName: string, style: Style, spreader?: (feature: Feature) => VectorLayer[]) => {
    try {
      const response = await fetch(fileName)
      const geojsonData: FeatureCollection = await response.json()
      const firePerimeterLayer = new VectorLayer({
        style,
        source: new VectorSource({
          features: new GeoJSON().readFeatures(geojsonData, {
            featureProjection: 'EPSG:3857'
          })
        })
      })
      firePerimeterLayer.set('name', FIRE_PERIMETER_LAYER)

      const layers = spreader ? geojsonData.features.map(feature => spreader(feature)) : [firePerimeterLayer]

      layers.flat().forEach(layer => mapInstanceRef.current?.addLayer(layer))
      return geojsonData
    } catch (error) {
      console.error('Error loading GeoJSON data:', error)
    }
  }

  useEffect(() => {
    console.log(firePerimeterData)
    console.log(hotspots)
    if (!mapInstanceRef.current) {
      const map = new Map({
        controls: defaultControls().extend([new GrowControl({ apiCallback: growFire })]),
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          })
        ],
        view: new View({
          center: fromLonLat(CENTER_OF_BC),
          zoom: 5
        })
      })

      // Enable selection of polygons
      const select = new Select()
      map.addInteraction(select)

      // Enable box dragging to select polygons
      const dragBox = new DragBox({
        condition: shiftKeyOnly // Hold down shift or control key while dragging
      })
      map.addInteraction(dragBox)

      dragBox.on('boxend', () => {
        const boxExtent = dragBox.getGeometry().getExtent()

        // Loop through each layer on the map
        map.getLayers().forEach(layer => {
          if (layer.get('name') === FIRE_PERIMETER_LAYER) {
            if (layer instanceof VectorLayer) {
              const vectorSource: VectorSource = layer.getSource()

              // Get features in the drag box extent
              const featuresInExtent = vectorSource.getFeaturesInExtent(boxExtent)

              if (featuresInExtent.length > 0) {
                console.log('Layer within extent:', layer.get('name'))

                // Optional: Log the features if needed
                featuresInExtent.forEach(feature => {
                  const geometry = feature.getGeometry()
                  if (geometry instanceof Polygon) {
                    // Convert OpenLayers Polygon to Turf.js Polygon
                    const lonLatCoordinates = geometry.getCoordinates()[0].map(coord => toLonLat(coord))
                    const turfPolygon = polygon([lonLatCoordinates])

                    const shifted = shiftPolygon(turfPolygon, 45, 1000)

                    if (shifted) {
                      // 2. Get the coordinates from the Turf.js polygon
                      // @ts-ignore
                      const turfCoordinates = getCoords(shifted)[0].map(coord => fromLonLat(coord))

                      // 4. Create an OpenLayers Polygon
                      const bufferedGeometry = new Polygon([turfCoordinates])

                      // Optionally, update the feature with the new buffered geometry
                      feature.setGeometry(bufferedGeometry)
                      feature.changed() // Notify OpenLayers that the feature has changed
                    }
                  }
                })
              }
            }
          }
        })
      })

      mapInstanceRef.current = map

      const firePerimeters = loadGeoJSON(
        '/PROT_CURRENT_FIRE_POLYS_SP.geojson',
        new Style({
          fill: new Fill({
            color: 'rgba(0, 0, 255, 0.6)' // Blue fill with 60% opacity
          })
        })
      )

      const hotspots = loadGeoJSON(
        '/FirespotArea_canada_c6.1_48.geojson',
        new Style({
          fill: new Fill({
            color: 'rgba(255, 0, 0, 0.6)' // Red fill with 60% opacity
          })
        }),
        feature => {
          const [originalLayer, spreadLayer] = spreadInDirection(feature, 'north', 1000)
          originalLayer.set('name', HOTSPOT_LAYER)
          spreadLayer.set('name', SPREAD_HOTSPOT_LAYER)
          return [originalLayer]
        }
      )
    }
  }, [])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
