import OptionalHeading from '@/features/fireWatch/components/OptionalHeading'
import { FORM_MAX_WIDTH } from '@/features/fireWatch/constants'
import { FireWatch, FuelTypeEnum, fuelTypes } from '@/features/fireWatch/interfaces'
import { Autocomplete, Box, Step, TextField, Typography, useTheme } from '@mui/material'
import { isNull, isUndefined } from 'lodash'
import { SetStateAction } from 'react'

interface FuelStepProps {
  fireWatch: FireWatch
  setFireWatch: React.Dispatch<SetStateAction<FireWatch>>
}

const FuelStep = ({ fireWatch, setFireWatch }: FuelStepProps) => {
  const theme = useTheme()

  const handleFormUpdate = (partialFireWatch: Partial<FireWatch>) => {
    const newFireWatch = { ...fireWatch, ...partialFireWatch }
    setFireWatch(newFireWatch)
  }

  const renderConditionalPercentInputField = () => {
    switch (fireWatch.fuelType) {
      case FuelTypeEnum.M1:
      case FuelTypeEnum.M2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Percent Conifer
            </Typography>
            <TextField
              type="number"
              required
              size="small"
              value={
                !isUndefined(fireWatch.percentConifer) && isNaN(fireWatch.percentConifer)
                  ? ''
                  : fireWatch.percentConifer
              }
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                handleFormUpdate({ percentConifer: parseFloat(event.target.value) })
              }
            />
          </Box>
        )
      case FuelTypeEnum.M3:
      case FuelTypeEnum.M4:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Percent Dead Fir
            </Typography>
            <TextField
              type="number"
              required
              size="small"
              value={
                !isUndefined(fireWatch.percentDeadFir) && isNaN(fireWatch.percentDeadFir)
                  ? ''
                  : fireWatch.percentDeadFir
              }
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                handleFormUpdate({ percentDeadFir: parseFloat(event.target.value) })
              }
            />
          </Box>
        )
      case FuelTypeEnum.C7:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Percent Grass Curing
            </Typography>
            <TextField
              type="number"
              required
              size="small"
              value={
                !isUndefined(fireWatch.percentGrassCuring) && isNaN(fireWatch.percentGrassCuring)
                  ? ''
                  : fireWatch.percentGrassCuring
              }
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                handleFormUpdate({ percentGrassCuring: parseFloat(event.target.value) })
              }
            />
          </Box>
        )
    }
  }

  return (
    <Step>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4) }}>
        <Typography variant="h6">Step 4: Fuel Type & Fuel Moisture Codes</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', pt: theme.spacing(2) }}>
            <Typography sx={{ pb: theme.spacing(0.5) }} variant="body1">
              Fuel Type
            </Typography>
            <Autocomplete
              blurOnSelect
              disableClearable
              options={fuelTypes}
              size="small"
              value={fireWatch.fuelType}
              renderInput={params => <TextField {...params} />}
              onChange={(_: React.SyntheticEvent<Element, Event>, newValue: FuelTypeEnum) => {
                handleFormUpdate({ fuelType: newValue })
              }}
            />
          </Box>
          {renderConditionalPercentInputField()}
          <Box sx={{ display: 'flex', flexDirection: 'row', pt: theme.spacing(2) }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
              <OptionalHeading>Fine Fuel Moisture Code (FFMC)</OptionalHeading>
              <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
                <TextField
                  required={!isNull(fireWatch.ffmcMax) && !isNaN(fireWatch.ffmcMax)}
                  label="Minimum"
                  size="small"
                  type="number"
                  value={isNull(fireWatch.ffmcMin) || isNaN(fireWatch.ffmcMin) ? null : fireWatch.ffmcMin}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ ffmcMin: parseFloat(event.target.value) })
                  }
                  sx={{ pr: theme.spacing(2) }}
                />
                <TextField
                  required={!isNull(fireWatch.ffmcMin) && !isNaN(fireWatch.ffmcMin)}
                  label="Maximum"
                  size="small"
                  type="number"
                  value={isNull(fireWatch.ffmcMax) || isNaN(fireWatch.ffmcMax) ? '' : fireWatch.ffmcMax}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleFormUpdate({ ffmcMax: parseFloat(event.target.value) })
                  }
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
            <OptionalHeading>Duff Moisture Code (DMC)</OptionalHeading>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                required={!isNull(fireWatch.dmcMax) && !isNaN(fireWatch.dmcMax)}
                label="Minimum"
                size="small"
                type="number"
                value={isNull(fireWatch.dmcMin) || isNaN(fireWatch.dmcMin) ? '' : fireWatch.dmcMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ dmcMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                required={!isNull(fireWatch.dmcMin) && !isNaN(fireWatch.dmcMin)}
                label="Maximum"
                size="small"
                type="number"
                value={isNull(fireWatch.dmcMax) || isNaN(fireWatch.dmcMax) ? '' : fireWatch.dmcMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ dmcMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(2) }}>
            <OptionalHeading>Drought Code (DC)</OptionalHeading>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                required={!isNull(fireWatch.dcMax) && !isNaN(fireWatch.dcMax)}
                label="Minimum"
                size="small"
                type="number"
                value={isNull(fireWatch.dcMin) || isNaN(fireWatch.dcMin) ? '' : fireWatch.dcMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ dcMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                required={!isNull(fireWatch.dcMin) && !isNaN(fireWatch.dcMin)}
                label="Maximum"
                size="small"
                type="number"
                value={isNull(fireWatch.dcMax) || isNaN(fireWatch.dcMax) ? '' : fireWatch.dcMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ dcMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, pb: theme.spacing(4) }}>
            <OptionalHeading>Buildup Index (BUI)</OptionalHeading>
            <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1 }}>
              <TextField
                required={!isNull(fireWatch.buiMax) && !isNaN(fireWatch.buiMax)}
                label="Minimum"
                size="small"
                type="number"
                value={isNull(fireWatch.buiMin) || isNaN(fireWatch.buiMin) ? '' : fireWatch.buiMin}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ buiMin: parseFloat(event.target.value) })
                }
                sx={{ pr: theme.spacing(2) }}
              />
              <TextField
                required={!isNull(fireWatch.buiMin) && !isNaN(fireWatch.buiMin)}
                label="Maximum"
                size="small"
                type="number"
                value={isNull(fireWatch.buiMax) || isNaN(fireWatch.buiMax) ? '' : fireWatch.buiMax}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  handleFormUpdate({ buiMax: parseFloat(event.target.value) })
                }
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Step>
  )
}

export default FuelStep
