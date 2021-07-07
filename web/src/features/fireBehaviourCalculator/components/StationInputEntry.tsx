import React, { useEffect } from 'react'

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Checkbox,
  FormControlLabel
} from '@material-ui/core'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'
import { useDispatch } from 'react-redux'
import { getStations } from 'api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import FBCInputForm from './FBCInputForm'

interface StationInputEntryProps {
  testId?: string
  stationsOfInterest: number
  setStationsOfInterest: (stations: number) => void
  fuelType: string
  setFuelType: (fuelType: string) => void
  grassCurePercentage: number | null
  setGrassCurePercentage: (percentage: number | null) => void
  stationMenuItems: JSX.Element[]
  fuelTypeMenuItems: JSX.Element[]
}

const StationInputEntry = (props: StationInputEntryProps) => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(fetchWxStations(getStations))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Accordion>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-label="Expand"
        aria-controls="additional-actions1-content"
        id="additional-actions1-header"
      >
        <FormControlLabel
          aria-label="Acknowledge"
          onClick={event => event.stopPropagation()}
          onFocus={event => event.stopPropagation()}
          control={<Checkbox />}
          label={`Enable station ${props.stationsOfInterest} for calculation`}
        />
      </AccordionSummary>
      <AccordionDetails>
        <FBCInputForm
          stationsOfInterest={props.stationsOfInterest}
          setStationsOfInterest={props.setStationsOfInterest}
          fuelType={props.fuelType}
          setFuelType={props.setFuelType}
          grassCurePercentage={props.grassCurePercentage}
          setGrassCurePercentage={props.setGrassCurePercentage}
          stationMenuItems={props.stationMenuItems}
          fuelTypeMenuItems={props.fuelTypeMenuItems}
        />
      </AccordionDetails>
    </Accordion>
  )
}

export default React.memo(StationInputEntry)
