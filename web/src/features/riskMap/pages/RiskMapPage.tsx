import { FireMap } from '@/features/riskMap/pages/components/FireMap'
import { ValuesImportButton } from '@/features/riskMap/pages/components/UploadButton'
import { Grid, Typography } from '@mui/material'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { Fill, Style } from 'ol/style'
import { Map } from 'ol'
import axios from 'api/axios'
import { useState } from 'react'
import firePerimeterData from './components/PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './components/FirespotArea_canada_c6.1_48.json'
import { GrowFireButton } from '@/features/riskMap/pages/components/GrowFireButton'

const getRandomColor = () => {
  const r = Math.floor(Math.random() * 256) // Random red value
  const g = Math.floor(Math.random() * 256) // Random green value
  const b = Math.floor(Math.random() * 256) // Random blue value
  const a = 0.6 // Fixed alpha for transparency (60% opacity)
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

export const RiskMapPage = () => {
  const [file, setFile] = useState<File | null>(null)
  const [mapInstance, setMapInstance] = useState<Map | null>(null)

  // Method to trigger the fetch request
  const growFire = async () => {
    try {
      const url = 'risk-map/grow'
      const { data } = await axios.post(url, {
        fire_perimeter: {
          // @ts-ignore
          features: firePerimeterData.features
        },
        hotspots: {
          features: hotspots.features
        }
      })

      // Set the initial zIndex to a high value
      let initialZIndex = 45

      data.forEach((firePerimeterDataItem: any) => {
        const firePerimeterLayer = new VectorLayer({
          style: new Style({
            fill: new Fill({
              color: getRandomColor()
            })
          }),
          source: new VectorSource({
            features: new GeoJSON().readFeatures(firePerimeterDataItem, {
              featureProjection: 'EPSG:3857'
            })
          })
        })

        // Set a decreasing zIndex for each layer
        firePerimeterLayer.setZIndex((initialZIndex -= 1))

        // Add the layer to the map
        mapInstance?.addLayer(firePerimeterLayer)
      })
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }
  return (
    <Grid
      container
      spacing={1}
      direction={'column'}
      justifyContent="center"
      alignItems="center"
      style={{ minHeight: '100vh' }}
    >
      <Grid item>
        <Typography variant="h5">Choose the values GeoJSON file to generate a risk map</Typography>
      </Grid>
      <Grid item>
        <Grid container direction={'row'} spacing={1}>
          <Grid item>
            <ValuesImportButton setFile={setFile} />
          </Grid>
          <Grid item>
            <GrowFireButton growFire={growFire} />
          </Grid>
        </Grid>
      </Grid>
      <Grid item>
        <FireMap valuesFile={file} setMapInstance={setMapInstance} />
      </Grid>
    </Grid>
  )
}
