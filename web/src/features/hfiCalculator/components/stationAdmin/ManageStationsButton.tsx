import React, { useState } from 'react'
import SettingsIcon from '@mui/icons-material/Settings'
import { Button } from '@mui/material'
import ManageStationsModal from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'

const ManageStationsButton = () => {
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const openAboutModal = () => {
    setModalOpen(true)
  }

  return (
    <React.Fragment>
      <Button
        variant="text"
        color="primary"
        onClick={openAboutModal}
        data-testid={'manage-stations-button'}
      >
        <SettingsIcon />
        Manage Stations
      </Button>
      <ManageStationsModal modalOpen={modalOpen} setModalOpen={setModalOpen} />
    </React.Fragment>
  )
}

export default React.memo(ManageStationsButton)
