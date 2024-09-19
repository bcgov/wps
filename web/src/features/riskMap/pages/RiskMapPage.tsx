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

      mapInstance?.addLayer(firePerimeterLayer)
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
