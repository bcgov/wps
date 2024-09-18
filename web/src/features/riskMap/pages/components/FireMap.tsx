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
import { Fill, Stroke, Style } from 'ol/style'

interface FireMapProps {
  file: File | null
}

export const FireMap: React.FC<FireMapProps> = ({ file }) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  const handleFile = async (file: File) => {
    const reader = new FileReader()

    reader.onload = () => {
      try {
        const geojsonData = fetch('FirespotArea_canada_c6.1_48.geojson')
        const geojsonSource = new VectorSource({
          features: new GeoJSON().readFeatures(geojsonData, {
            featureProjection: 'EPSG:3857'
          })
        })

        const layer = new VectorLayer({
          source: geojsonSource
        })

        mapInstanceRef.current?.addLayer(layer)

        const extent = geojsonSource.getExtent()
        mapInstanceRef.current?.getView().fit(extent, { size: mapInstanceRef.current.getSize() })
      } catch (error) {
        console.error('Error reading GeoJSON file:', error)
      }
    }

    reader.readAsText(file)
  }
  const loadGeoJSON = async (fileName: string, style: Style) => {
    try {
      const response = await fetch(fileName)
      const geojsonData = await response.json()
      const geojsonSource = new VectorSource({
        features: new GeoJSON().readFeatures(geojsonData, {
          featureProjection: 'EPSG:3857'
        })
      })

      const layer = new VectorLayer({
        source: geojsonSource,
        style
      })
      mapInstanceRef.current?.addLayer(layer)
    } catch (error) {
      console.error('Error loading GeoJSON data:', error)
    }
  }

  useEffect(() => {
    if (!mapInstanceRef.current) {
      const map = new Map({
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
      mapInstanceRef.current = map
      loadGeoJSON(
        '/PROT_CURRENT_FIRE_POLYS_SP.geojson',
        new Style({
          fill: new Fill({
            color: 'rgba(0, 0, 255, 0.6)' // Red fill with 60% opacity
          })
        })
      )
      loadGeoJSON(
        '/FirespotArea_canada_c6.1_48.geojson', // Define the style for the polygons with red fill and optional black stroke
        new Style({
          fill: new Fill({
            color: 'rgba(255, 0, 0, 0.6)' // Red fill with 60% opacity
          })
        })
      )
    }
  }, [])

  useEffect(() => {
    if (file) {
      handleFile(file)
    }
  }, [file])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
