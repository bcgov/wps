import { FireMap } from '@/features/riskMap/components/FireMap'
import { GrowFireButton } from '@/features/riskMap/components/GrowFireButton'
import { ValuesImportButton } from '@/features/riskMap/components/UploadButton'
import { Box, CircularProgress, Grid, Modal, Typography } from '@mui/material'
import axios from 'api/axios'
import { AppDispatch } from 'app/store'
import { Feature, Map } from 'ol'
import GeoJSON from 'ol/format/GeoJSON'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Fill, Style } from 'ol/style'
import { useEffect, useState } from 'react'
import firePerimeterData from '../components/PROT_CURRENT_FIRE_POLYS_SP.json'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { getDetailedStations, StationSource } from 'api/stationAPI'
import { selectFireGrowthDay, selectHotSpots } from '@/app/rootReducer'
import { GeneralHeader } from '@/components'
import DayControl from '@/features/riskMap/components/DayControl'
import DistanceSlider from '@/features/riskMap/components/SpreadDistanceSlider'
import { addGrowthLayer } from '@/features/riskMap/slices/fireGrowthSlice'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHotSpots } from '@/features/riskMap/slices/hotSpotsSlice'
import { fetchRepresentativeStations } from '@/features/riskMap/slices/representativeStationSlice'
import { theme } from '@/app/theme'
import { Geometry } from 'ol/geom'
import { ComputeRiskButton } from '@/features/riskMap/components/ComputeRisk'
import { convertFeaturesToGeoJSON, getFeaturesFromLayer } from '@/features/riskMap/mapFunctions'
import RiskTable from '@/features/riskMap/components/sidePanel/RiskTable'
import RiskPanel from '@/features/riskMap/components/sidePanel/RiskPanel'

export const RiskMapPage = () => {
  const dispatch: AppDispatch = useDispatch()
  const { hotSpotPoints } = useSelector(selectHotSpots)
  const { day, dayGrowthLayers } = useSelector(selectFireGrowthDay)

  const [mapInstance, setMapInstance] = useState<Map | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  const [dateOfInterest, setDateOfInterest] = useState<DateTime>(DateTime.now().setZone('America/Vancouver'))
  const [growthDay, setGrowthDay] = useState<number>(0)
  const [spreadDistance, setSpreadDistance] = useState(500)
  const [riskDetails, setRiskDetails] = useState([])

  const [file, setFile] = useState<File | null>(null)
  const [values, setValues] = useState<Feature<Geometry>[]>([])

  const getGrowthColor = () => {
    const a = 0.6 // Fixed alpha for transparency (60% opacity)
    let currentGrowthDay = growthDay
    setGrowthDay(currentGrowthDay++)
    switch (currentGrowthDay) {
      case 0:
        return `rgba(187, 125, 81, ${a})`
      case 1:
        return `rgba(205, 145, 88, ${a})`
      case 2:
        return `rgba(221, 166, 95, ${a})`
      case 3:
        return `rgba(237, 188, 103, ${a})`
      default:
        return `rgba(253, 183, 119, ${a})`
    }
  }

  const removeLayerByName = () => {
    if (mapInstance) {
      const layers = mapInstance
        .getLayers()
        .getArray()
        .filter(l => {
          const name = l.get('name')
          return name?.startsWith('firePerimDay')
        })
      if (layers) {
        layers.forEach(layer => mapInstance.removeLayer(layer))
      }
    }
  }

  useEffect(() => {
    if (mapInstance) {
      if (day === 0) {
        removeLayerByName()
      } else {
        const layerToAdd = dayGrowthLayers[day]
        if (layerToAdd) {
          mapInstance.addLayer(dayGrowthLayers[day])
        }
      }
    }
  }, [day])

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
          features: hotSpotPoints.features
        },
        time_of_interest: dateOfInterest.toISO()
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
          }),
          properties: { name: `firePerimDay${index + 1}` }
        })
        firePerimeterLayer.setZIndex((initialZIndex -= 1))
        dispatch(addGrowthLayer(firePerimeterLayer))

        // Add the layer to the map
        // mapInstance?.addLayer(firePerimeterLayer)
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  const computeRisk = async () => {
    try {
      setLoading(true)
      const valueFeatures = getFeaturesFromLayer(mapInstance, 'uploadedValues')
      const valueJsonFeatures = convertFeaturesToGeoJSON(valueFeatures)
      const url = 'risk-map/compute'
      const { data } = await axios.post(url, {
        values: {
          features: valueJsonFeatures.features
        },
        hotspots: {
          features: hotSpotPoints.features
        }
      })
      setLoading(false)
      setRiskDetails(data.risk_outputs)
      console.log(data)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    dispatch(fetchWxStations(getDetailedStations, StationSource.unspecified))
    dispatch(fetchRepresentativeStations())
    dispatch(fetchHotSpots(dateOfInterest))
  }, [dateOfInterest])

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Modal open={loading}>
        <Box>
          <Grid
            container
            direction={'column'}
            sx={{
              display: 'flex',
              alignItems: 'center',
              height: '100vh'
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

      <GeneralHeader isBeta={true} spacing={1} title={'Risk Map'} productName={'Risk Map'} />

      <Box sx={{ padding: '0.5em' }}>
        <Grid container spacing={1} alignItems="center">
          <Grid item>
            <LocalizationProvider dateAdapter={AdapterLuxon}>
              <DatePicker
                label="Date of Interest"
                value={dateOfInterest}
                onChange={newValue => {
                  if (newValue) {
                    setDateOfInterest(newValue.setZone('America/Vancouver'))
                  }
                }}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item>
            <ValuesImportButton setFile={setFile} setValues={setValues} />
          </Grid>
          <Grid item>
            <GrowFireButton growFire={growFire} />
          </Grid>
          <Grid item>
            <ComputeRiskButton computeRisk={computeRisk} />
          </Grid>
          <Grid item>
            <DayControl />
          </Grid>
          <Grid item>
            <DistanceSlider spreadDistance={spreadDistance} setSpreadDistance={setSpreadDistance} />
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ display: 'flex', flexGrow: 1, width: '100%' }}>
        {riskDetails.length > 0 && (
          <RiskPanel>
            <RiskTable open={true} valueDetails={riskDetails}></RiskTable>
          </RiskPanel>
        )}
        <FireMap
          valuesFile={file}
          setMapInstance={setMapInstance}
          dateOfInterest={dateOfInterest}
          spreadDistance={spreadDistance}
        />
      </Box>
    </Box>
  )
}
