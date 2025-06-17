import { FORM_MAX_WIDTH } from '@/features/fireWatch/components/CreateFireWatch'
import SummaryTextLine from '@/features/fireWatch/components/steps/SummaryTextLine'
import { FireWatch, FuelTypeEnum } from '@/features/fireWatch/interfaces'
import { Box, Button, Step, Typography, useTheme } from '@mui/material'
import { isUndefined } from 'lodash'
import React, { SetStateAction, useEffect, useRef, useState } from 'react'
import { fromLonLat, toLonLat } from 'ol/proj'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import { source as baseMapSource } from 'features/fireWeather/components/maps/constants'
import VectorSource from 'ol/source/Vector.js'
import VectorLayer from 'ol/layer/Vector.js'
import { Icon, Style } from 'ol/style'
import Feature from 'ol/Feature.js'
import { Point } from 'ol/geom'
import { CENTER_OF_BC } from '@/utils/constants'

interface ReviewSubmitStepProps {
  fireWatch: FireWatch
  setActiveStep: React.Dispatch<SetStateAction<number>>
}

export const MapContext = React.createContext<Map | null>(null)

const ReviewSubmitStep = ({ fireWatch, setActiveStep }: ReviewSubmitStepProps) => {
  const theme = useTheme()
  const [map, setMap] = useState<Map | null>(null)
  const mapRef = useRef<HTMLDivElement | null>(null) as React.MutableRefObject<HTMLElement>

  const formatNumber = (value: number | undefined) => {
    if (isUndefined(value)) {
      return '-'
    }
    return `${!isNaN(value) ? value : '-'}`
  }

  const formatFuelType = () => {
    let postfix = ''
    switch (fireWatch.fuelType) {
      case FuelTypeEnum.M1:
      case FuelTypeEnum.M2:
        postfix = `(Percent Conifer: ${formatNumber(fireWatch.percentConifer)})`
        break
      case FuelTypeEnum.M3:
      case FuelTypeEnum.M4:
        postfix = `(Percent Dead Fir: ${formatNumber(fireWatch.percentDeadFir)})`
        break
      case FuelTypeEnum.C7:
        postfix = `(Percent Grass Curing: ${formatNumber(fireWatch.percentGrassCuring)})`
        break
    }
    return `${fireWatch.fuelType} ${postfix}`
  }

  useEffect(() => {
    if (!mapRef.current) {
      return
    }
    const feature =
      fireWatch.geometry.length === 2 ? new Feature({ geometry: new Point(fireWatch.geometry) }) : new Feature()
    const featureSource = new VectorSource({ features: [feature] })
    const featureLayer = new VectorLayer({
      source: featureSource,
      style: new Style({
        image: new Icon({
          anchor: [0.5, 1],
          height: 32,
          src: '/images/redMarker.png'
        })
      }),
      zIndex: 50
    })
    const mapObject = new Map({
      view: new View({
        zoom: fireWatch.geometry.length === 2 ? 9 : 5,
        center: fireWatch.geometry.length === 2 ? fireWatch.geometry : fromLonLat(CENTER_OF_BC)
      }),
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        featureLayer
      ]
    })
    mapObject.setTarget(mapRef.current)
    setMap(mapObject)
    return () => {
      mapObject.setTarget('')
    }
  }, [])

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            maxWidth: `${FORM_MAX_WIDTH}px`,
            width: `${FORM_MAX_WIDTH}px`,
            padding: theme.spacing(4)
          }}
        >
          <Typography sx={{ fontWeight: 'bold' }} variant="h6">
            Step 6: Review and Submit
          </Typography>
          <Typography sx={{ fontWeight: 'bold', py: theme.spacing(2) }} variant="body1">
            Submission Summary
          </Typography>
          <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
              <Box sx={{ display: 'flex' }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: '1' }}>
                  <Typography sx={{ fontWeight: 'bold' }} variant="body1">
                    1. Burn Information
                  </Typography>
                  <SummaryTextLine
                    indentLevel={1}
                    left="Name"
                    right={fireWatch.contactEmail.length > 0 ? fireWatch.title : ''}
                  />
                  {(fireWatch.burnWindowStart || fireWatch.burnWindowEnd) && (
                    <SummaryTextLine
                      indentLevel={1}
                      left="Burn Window"
                      right={`${fireWatch.burnWindowStart?.toISODate() ?? '-'} - ${fireWatch.burnWindowEnd?.toISODate() ?? '-'}`}
                    />
                  )}
                  <SummaryTextLine indentLevel={1} left="Fire Centre" right={fireWatch.fireCentre?.name ?? ''} />
                  <SummaryTextLine indentLevel={1} left="Weather Station" right={fireWatch.station?.name ?? ''} />
                  <SummaryTextLine
                    indentLevel={1}
                    left="Contact Email"
                    right={fireWatch.contactEmail.length > 0 ? fireWatch.contactEmail[0].toString() : ''}
                  />
                </Box>
                <Box>
                  <Button onClick={() => setActiveStep(0)}>Edit</Button>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', pt: theme.spacing(2) }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: '1' }}>
                  <Typography sx={{ fontWeight: 'bold' }} variant="body1">
                    2. Location
                  </Typography>
                  <SummaryTextLine
                    indentLevel={1}
                    left="Latitude"
                    right={fireWatch.geometry.length === 2 ? toLonLat(fireWatch.geometry)[1].toFixed(3) : ''}
                  />
                  <SummaryTextLine
                    indentLevel={1}
                    left="Longitude"
                    right={fireWatch.geometry.length === 2 ? toLonLat(fireWatch.geometry)[0].toFixed(3) : ''}
                  />
                </Box>
                <Box>
                  <Button onClick={() => setActiveStep(1)}>Edit</Button>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', pt: theme.spacing(2) }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: '1' }}>
                  <Typography sx={{ fontWeight: 'bold' }} variant="body1">
                    3. Weather (Min/Preferred/Max)
                  </Typography>
                  <SummaryTextLine
                    indentLevel={1}
                    left="Temperature (°C)"
                    right={`${formatNumber(fireWatch.tempMin)}/${formatNumber(fireWatch.tempPreferred)}/${formatNumber(fireWatch.tempMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={1}
                    left="Relative Humidity (%)"
                    right={`${formatNumber(fireWatch.rhMin)}/${formatNumber(fireWatch.rhPreferred)}/${formatNumber(fireWatch.rhMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={1}
                    left="Wind Speed (km/h)"
                    right={`${formatNumber(fireWatch.windSpeedMin)}/${formatNumber(fireWatch.windSpeedPreferred)}/${formatNumber(fireWatch.windSpeedMax)}`}
                  />
                </Box>
                <Box>
                  <Button onClick={() => setActiveStep(2)}>Edit</Button>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', pt: theme.spacing(2) }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: '1' }}>
                  <Typography sx={{ fontWeight: 'bold' }} variant="body1">
                    4. Fuel Type and Fuel Moisture Codes
                  </Typography>
                  <SummaryTextLine indentLevel={1} left="Fuel Type" right={`${formatFuelType()}`} />
                  <SummaryTextLine indentLevel={1} left="Fuel Moisture Codes (Min/Preferred/Max)" right={''} />
                  <SummaryTextLine
                    indentLevel={2}
                    left="FFMC"
                    right={`${formatNumber(fireWatch.ffmcMin)}/${formatNumber(fireWatch.ffmcPreferred)}/${formatNumber(fireWatch.ffmcMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={2}
                    left="DMC"
                    right={`${formatNumber(fireWatch.dmcMin)}/${formatNumber(fireWatch.dmcPreferred)}/${formatNumber(fireWatch.dmcMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={2}
                    left="DC"
                    right={`${formatNumber(fireWatch.dcMin)}/${formatNumber(fireWatch.dcPreferred)}/${formatNumber(fireWatch.dcMax)}`}
                  />
                </Box>
                <Box>
                  <Button onClick={() => setActiveStep(3)}>Edit</Button>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', pt: theme.spacing(2) }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: '1' }}>
                  <Typography sx={{ fontWeight: 'bold' }} variant="body1">
                    5. Fire Behavior Indices (Min/Preferred/Max)
                  </Typography>
                  <SummaryTextLine
                    indentLevel={1}
                    left="BUI"
                    right={`${formatNumber(fireWatch.buiMin)}/${formatNumber(fireWatch.buiPreferred)}/${formatNumber(fireWatch.buiMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={1}
                    left="ISI"
                    right={`${formatNumber(fireWatch.isiMin)}/${formatNumber(fireWatch.isiPreferred)}/${formatNumber(fireWatch.isiMax)}`}
                  />
                  <SummaryTextLine
                    indentLevel={1}
                    left="HFI (kw/M)"
                    right={`${formatNumber(fireWatch.hfiMin)}/${formatNumber(fireWatch.hfiPreferred)}/${formatNumber(fireWatch.hfiMax)}`}
                  />
                </Box>
                <Box>
                  <Button onClick={() => setActiveStep(4)}>Edit</Button>
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', flexGrow: 1, padding: theme.spacing(2), justifyContent: 'center' }}>
          <MapContext.Provider value={map}>
            <Box ref={mapRef} data-testid="summary-map" sx={{ height: '80%', width: '80%' }}></Box>
          </MapContext.Provider>
        </Box>
      </Box>
    </Step>
  )
}

export default ReviewSubmitStep
