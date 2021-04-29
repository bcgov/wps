import React from 'react'
import { useSelector } from 'react-redux'

import { Button } from 'components'
import { selectWxDataLoading } from 'app/rootReducer'

interface Props {
  onBtnClick: () => void
  disabled: boolean
}

const GetWxDataButton = ({ onBtnClick, disabled }: Props) => {
  const wxDataLoading = useSelector(selectWxDataLoading)

  return (
    <Button
      data-testid="get-wx-data-button"
      onClick={onBtnClick}
      disabled={disabled}
      loading={wxDataLoading}
      variant="contained"
      color="primary"
      spinnercolor="white"
    >
      Get Weather Data
    </Button>
  )
}

export default React.memo(GetWxDataButton)
