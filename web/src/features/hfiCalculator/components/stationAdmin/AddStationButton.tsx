import React, { useState } from 'react'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { Button } from '@mui/material'
import AddStationModal from 'features/hfiCalculator/components/stationAdmin/AddStationModal'

export interface AddStationButtonProps {
  testId?: string
  fireCentreId: number
}

const AddStationButton = ({ fireCentreId }: AddStationButtonProps) => {
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const openAddStationModal = () => {
    setModalOpen(true)
  }

  return (
    <React.Fragment>
      <Button
        variant="text"
        color="primary"
        onClick={openAddStationModal}
        data-testid={'manage-stations-button'}
      >
        <AddCircleOutlineIcon />
        Add weather station
      </Button>
      <AddStationModal
        fireCentreId={fireCentreId}
        modalOpen={modalOpen}
        setModalOpen={setModalOpen}
      />
    </React.Fragment>
  )
}

export default React.memo(AddStationButton)
