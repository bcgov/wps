import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import { Button } from '@mui/material'
import type { PlanningArea, StationInfo } from '@wps/api/hfiCalculatorAPI'
import ManageStationsModal from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import React, { useState } from 'react'

export interface ManageStationsButtonProps {
  planningAreas?: PlanningArea[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
}

const ManageStationsButton = ({ planningAreas, planningAreaStationInfo }: ManageStationsButtonProps) => {
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
      <ManageStationsModal
        modalOpen={modalOpen}
        setModalOpen={setModalOpen}
        planningAreas={planningAreas}
        planningAreaStationInfo={planningAreaStationInfo}
      />
    </React.Fragment>
  )
}

export default React.memo(ManageStationsButton)
