import React, { useState } from 'react'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import { Button } from '@mui/material'
import AddStationModal from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

export interface AddStationButtonProps {
  planningAreas?: PlanningArea[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
}

const AddStationButton = ({ planningAreas, planningAreaStationInfo }: AddStationButtonProps) => {
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const openAddStationModal = () => {
    setModalOpen(true)
  }

  return (
    <React.Fragment>
      <Button variant="text" color="primary" onClick={openAddStationModal} data-testid={'manage-stations-button'}>
        <SettingsOutlinedIcon />
        Manage Stations
      </Button>
      <AddStationModal
        modalOpen={modalOpen}
        setModalOpen={setModalOpen}
        planningAreas={planningAreas}
        planningAreaStationInfo={planningAreaStationInfo}
      />
    </React.Fragment>
  )
}

export default React.memo(AddStationButton)
