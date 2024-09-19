import { FireMap } from '@/features/riskMap/pages/components/FireMap'
import { ValuesImportButton } from '@/features/riskMap/pages/components/UploadButton'
import { Box, CircularProgress, Grid, Modal, Typography } from '@mui/material'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { Fill, Stroke, Style, Text } from 'ol/style'
import { Map } from 'ol'
import axios from 'api/axios'
import { useState } from 'react'
import firePerimeterData from './components/PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './components/FirespotArea_canada_c6.1_48.json'
import { GrowFireButton } from '@/features/riskMap/pages/components/GrowFireButton'
import { theme } from '@/app/theme'

export const RiskMapPage = () => {
  const [file, setFile] = useState<File | null>(null)
  const [mapInstance, setMapInstance] = useState<Map | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [growthDay, setGrowthDay] = useState<number>(0)

  const getGrowthColor = () => {
    const a = 0.6 // Fixed alpha for transparency (60% opacity)
    let currentGrowthDay = growthDay
    setGrowthDay(currentGrowthDay++)
    switch (currentGrowthDay) {
      case 0:
        return `rgba(255, 98, 0, ${a})`
      case 1:
        return `rgba(253, 127, 44, ${a})`
      case 2:
        return `rgba(253, 147, 70, ${a})`
      case 3:
        return `rgba(253, 167, 102, ${a})`
      default:
        return `rgba(253, 183, 119, ${a})`
    }
  }

  // Method to trigger the fetch request
  const growFire = async () => {
    try {
      setLoading(true)
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
      setLoading(false)

      // Set the initial zIndex to a high value
      let initialZIndex = 45

      data.forEach((firePerimeterDataItem: any, index: number) => {
        const firePerimeterLayer = new VectorLayer({
          style: new Style({
            fill: new Fill({
              color: getGrowthColor()
            })
          }),
          source: new VectorSource({
            features: new GeoJSON().readFeatures(firePerimeterDataItem, {
              featureProjection: 'EPSG:3857'
            })
          })
        })

        firePerimeterLayer.set('layerName', `firePerimDay${index + 1}`)
        firePerimeterLayer.setZIndex((initialZIndex -= 1))

        // Add the layer to the map
        mapInstance?.addLayer(firePerimeterLayer)
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }
  return (
    <>
      <Modal open={loading}>
        <Box>
          <Grid
            container
            direction={'column'}
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100vh' // Full viewport height
            }}
          >
            <Grid item>
              <CircularProgress color="secondary" />
            </Grid>
            <Grid item>
              <Typography sx={{ mt: 2, color: theme.palette.primary.contrastText }}>Growing your fire...</Typography>
            </Grid>
          </Grid>
        </Box>
      </Modal>
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
    </>
  )
}
