import React, { useState } from 'react'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { Button } from '@mui/material'
import AddStationModal from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { PlanningArea } from 'api/hfiCalculatorAPI'

export interface AddStationButtonProps {
  planningAreas?: PlanningArea[]
}

const AddStationButton = ({ planningAreas }: AddStationButtonProps) => {
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const openAddStationModal = () => {
    setModalOpen(true)
  }

  return (
    <React.Fragment>
      <Button variant="text" color="primary" onClick={openAddStationModal} data-testid={'manage-stations-button'}>
        <AddCircleOutlineIcon />
        Add weather station
      </Button>
      <AddStationModal modalOpen={modalOpen} setModalOpen={setModalOpen} planningAreas={planningAreas} />
    </React.Fragment>
  )
}

export default React.memo(AddStationButton)
