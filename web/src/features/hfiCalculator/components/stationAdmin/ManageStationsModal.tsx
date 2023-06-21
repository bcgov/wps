import React, { useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { Dialog, DialogContent, IconButton, Paper, Typography } from '@mui/material'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations, selectHFICalculatorState } from 'app/rootReducer'
import { setStationsUpdatedFailed, StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { groupBy, isNull, isUndefined, sortBy } from 'lodash'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import StationListAdmin from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { getSelectedFuelType } from 'features/hfiCalculator/util'

const PREFIX = 'ManageStationsModal'

const classes = {
  modalWindow: `${PREFIX}-modalWindow`,
  closeIcon: `${PREFIX}-closeIcon`,
  title: `${PREFIX}-title`,
  actionButton: `${PREFIX}-actionButton`
}

// TODO jss-to-styled codemod: The Fragment root was replaced by div. Change the tag if needed.
const Root = styled('div')(() => ({
  [`& .${classes.modalWindow}`]: {
    maxWidth: 'xl'
  },

  [`& .${classes.closeIcon}`]: {
    padding: 5,
    position: 'absolute',
    right: '0px'
  },

  [`& .${classes.title}`]: {
    textAlign: 'center'
  },

  [`& .${classes.actionButton}`]: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

export interface BasicPlanningArea {
  id: number
  name: string
}
export interface BasicWFWXStation {
  code: number
  name: string
}

export interface AddStationOptions {
  planningAreaOptions: BasicPlanningArea[]
  stationOptions: BasicWFWXStation[]
  fuelTypeOptions: FuelType[]
}

export interface StationAdminRow {
  planningAreaId: number
  rowId: number
  station?: BasicWFWXStation
  fuelType?: Pick<FuelType, 'id' | 'abbrev'>
}

export interface AddStationModalProps {
  testId?: string
  planningAreas?: PlanningArea[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

export const ManageStationsModal = ({
  modalOpen,
  setModalOpen,
  planningAreas,
  planningAreaStationInfo
}: AddStationModalProps): JSX.Element => {
  const dispatch: AppDispatch = useDispatch()

  const { fuelTypes, selectedFireCentre, stationsUpdatedError } = useSelector(selectHFICalculatorState)
  const { stations: wfwxStations } = useSelector(selectFireWeatherStations)
  const planning_areas: BasicPlanningArea[] = selectedFireCentre
    ? selectedFireCentre.planning_areas.map(planningArea => ({
        id: planningArea.id,
        name: planningArea.name
      }))
    : []
  const stations: BasicWFWXStation[] = wfwxStations.map(station => ({
    code: station.properties.code,
    name: station.properties.name
  }))

  const existingStations: { [key: string]: StationAdminRow[] } = groupBy(
    planningAreas
      ? sortBy(planningAreas, 'order_of_appearance_in_list')
          .map(planningArea =>
            sortBy(planningArea.stations, 'order_of_appearance_in_planning_area_list').map((station, i) => ({
              planningAreaId: planningArea.id,
              rowId: i,
              station: { code: station.code, name: station.station_props.name },
              fuelType: getSelectedFuelType(planningAreaStationInfo, planningArea.id, station.code, fuelTypes)
            }))
          )
          .flat()
      : [],
    'planningAreaId'
  )

  useEffect(() => {
    if (!isUndefined(selectedFireCentre)) {
      dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleClose = () => {
    setModalOpen(false)
    if (!isNull(stationsUpdatedError)) {
      dispatch(setStationsUpdatedFailed(null))
    }
  }

  return (
    <Root>
      <Dialog fullWidth maxWidth="md" open={modalOpen} onClose={handleClose} data-testid="manage-stations-modal">
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>
          <DialogContent>
            <Typography variant="h5" align="center">
              Manage Default Weather Stations
            </Typography>
            <Typography variant="body1" align="center">
              Add and remove stations in planning areas for all future prep
            </Typography>
          </DialogContent>
          {!isUndefined(planningAreas) && !isUndefined(wfwxStations) && !isUndefined(selectedFireCentre) && (
            <StationListAdmin
              fireCentreId={selectedFireCentre.id}
              planningAreas={planningAreas}
              fuelTypes={fuelTypes}
              existingPlanningAreaStations={existingStations}
              addStationOptions={{
                planningAreaOptions: planning_areas,
                stationOptions: stations,
                fuelTypeOptions: fuelTypes
              }}
              handleClose={handleClose}
            />
          )}
        </Paper>
      </Dialog>
    </Root>
  )
}

export default React.memo(ManageStationsModal)
