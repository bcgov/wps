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
  const loadGeoJson = async () => {
    try {
      const response = await fetch('/PROT_CURRENT_FIRE_POLYS_SP.geojson')
      const geojsonData = await response.json()
      const geojsonSource = new VectorSource({
        features: new GeoJSON().readFeatures(geojsonData, {
          featureProjection: 'EPSG:3857'
        })
      })

      const layer = new VectorLayer({
        source: geojsonSource
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
      loadGeoJson()
    }
  }, [])

  useEffect(() => {
    if (file) {
      handleFile(file)
    }
  }, [file])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
