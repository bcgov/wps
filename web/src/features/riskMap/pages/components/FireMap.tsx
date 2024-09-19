import React, { useEffect, useRef } from 'react'
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat } from 'ol/proj'
import { CENTER_OF_BC } from '@/utils/constants'
import { Fill, Style } from 'ol/style'
import axios from 'api/axios'

import { GrowControl } from '@/features/riskMap/pages/components/GrowControl'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './FirespotArea_canada_c6.1_48.json'

export const FireMap: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  useEffect(() => {
    console.log(firePerimeterData)
    console.log(hotspots)
    if (!mapInstanceRef.current) {
      const map = new Map({
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          }),
          new VectorLayer({
            style: new Style({
              fill: new Fill({
                color: 'rgba(0, 0, 255, 0.6)' // Blue fill with 60% opacity
              })
            }),
            source: new VectorSource({
              features: new GeoJSON().readFeatures(firePerimeterData, {
                featureProjection: 'EPSG:3857'
              })
            })
          }),
          new VectorLayer({
            style: new Style({
              fill: new Fill({
                color: 'rgba(255, 0, 0, 0.6)' // Red fill with 60% opacity
              })
            }),
            source: new VectorSource({
              features: new GeoJSON().readFeatures(hotspots, {
                featureProjection: 'EPSG:3857'
              })
            })
          })
        ],
        view: new View({
          center: fromLonLat(CENTER_OF_BC),
          zoom: 5
        })
      })

      // Method to trigger the fetch request
      const growFire = async () => {
        try {
          const url = `risk-map/grow`
          const { data } = await axios.post(url, {
            fire_perimeter: {
              // @ts-ignore
              features: firePerimeterData.features
            },
            hotspots: {
              features: hotspots.features
            }
          })

          const firePerimeterLayer = new VectorLayer({
            style: new Style({
              fill: new Fill({
                color: 'rgba(255, 222, 0, 0.6)' // Red fill with 60% opacity
              })
            }),
            source: new VectorSource({
              features: new GeoJSON().readFeatures(data, {
                featureProjection: 'EPSG:3857'
              })
            })
          })

          map.addLayer(firePerimeterLayer)
        } catch (error) {
          console.error('Error fetching data:', error)
        }
      }

      map.addControl(new GrowControl({ apiCallback: growFire }))

      mapInstanceRef.current = map
    }
  }, [])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
