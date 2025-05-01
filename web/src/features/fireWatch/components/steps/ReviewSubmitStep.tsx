import { FORM_MAX_WIDTH } from "@/features/fireWatch/components/CreateFireWatch"
import SummaryTextLine from "@/features/fireWatch/components/steps/SummaryTextLine"
import { FireWatch, FuelTypeEnum } from "@/features/fireWatch/fireWatchApi"
import { Box, Button, Step, Typography, useTheme } from "@mui/material"
import { isUndefined } from "lodash"
import { SetStateAction } from "react"

interface ReviewSubmitStepProps {
  fireWatch: FireWatch
  setActiveStep: React.Dispatch<SetStateAction<number>>
}

const ReviewSubmitStep = ({fireWatch, setActiveStep}: ReviewSubmitStepProps) => {
  const theme = useTheme()

  const formatNumber = (value: number | undefined) => {
    if (isUndefined(value)) {
      return '-'
    }
    return `${!isNaN(value) ? value : '-'}`
  }

  const formatFuelType = () => {
    let postfix = ''
    switch (fireWatch.fuelType) {
      case FuelTypeEnum.M1 || FuelTypeEnum.M2:
        postfix = `(Percent Conifer: ${formatNumber(fireWatch.percentConifer)})`
        break
      case FuelTypeEnum.M3 || FuelTypeEnum.M4:
        postfix = `(Percent Dead Fir: ${formatNumber(fireWatch.percentDeadFir)})`
        break
      case FuelTypeEnum.C7:
        postfix = `(Percent Grass Curing: ${formatNumber(fireWatch.percentGrassCuring)})`
        break
    }
    return `${fireWatch.fuelType} ${postfix}`
  }

  return (
    <Step>
      <Box sx={{display: 'flex', flexDirection: 'column', maxWidth: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4)}}>
        <Typography sx={{fontWeight: "bold"}} variant='h6'>
          Step 5: Review and Submit
        </Typography>
        <Typography sx={{fontWeight: "bold", py: theme.spacing(2)}} variant='body1'>
          Submission Summary
        </Typography>
        <Box sx={{display: 'flex', flexGrow: 1}}>
          <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: 1}}>
            <Box sx={{display: 'flex'}}>
              <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: "1"}}>
                <Typography sx={{fontWeight: "bold"}} variant="body1">
                  1. Location & Basics
                </Typography>
                <SummaryTextLine indentLevel={1} left="Burn Name" right={fireWatch.title} />
                <SummaryTextLine indentLevel={1} left="Latitude" right={formatNumber(fireWatch.latitude)} />
                <SummaryTextLine indentLevel={1} left="Longitude" right={formatNumber(fireWatch.longitude)} />
                <SummaryTextLine indentLevel={1} left="Burn Window" right={`${fireWatch.burnWindowStart.toISODate() ?? ""} - ${fireWatch.burnWindowEnd.toISODate() ?? ""}`} />
                <SummaryTextLine indentLevel={1} left="Contact Email" right={fireWatch.contactEmail.length > 0 ? fireWatch.contactEmail[0].toString() : ""} />
              </Box>
              <Box>
                <Button onClick={()=> setActiveStep(0)}>Edit</Button>
              </Box>
            </Box>
            <Box sx={{display: 'flex', pt: theme.spacing(2)}}>
              <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: "1"}}>
                <Typography sx={{fontWeight: "bold"}} variant="body1">
                  2. Weather (Min/Preferred/Max)
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
                <Button onClick={()=> setActiveStep(1)}>Edit</Button>
              </Box>
            </Box>
            <Box sx={{display: 'flex', pt: theme.spacing(2)}}>
              <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: "1"}}>
                <Typography sx={{fontWeight: "bold"}} variant="body1">
                  3. Fuel Type and Fuel Moisture Codes
                </Typography>
                <SummaryTextLine
                  indentLevel={1}
                  left="Fuel Type"
                  right={`${formatFuelType()}`}
                />
                <SummaryTextLine
                  indentLevel={1}
                  left="Fuel Moisture Codes (Min/Preferred/Max)"
                  right={""}
                />
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
                <Button onClick={()=> setActiveStep(2)}>Edit</Button>
              </Box>
            </Box>
            <Box sx={{display: 'flex', pt: theme.spacing(2)}}>
              <Box sx={{display: 'flex', flexDirection: 'column', flexGrow: "1"}}>
                <Typography sx={{fontWeight: "bold"}} variant="body1">
                  4. Fire Behavior Indices (Min/Preferred/Max
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
                <Button onClick={()=> setActiveStep(3)}>Edit</Button>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default ReviewSubmitStep