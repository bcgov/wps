import React from 'react'
import { useSelector } from 'react-redux'

import { Button } from 'components'
import { RootState } from 'app/rootReducer'

interface Props {
  onBtnClick: () => void
  selector: (root: RootState) => boolean
  disabled?: boolean
  buttonLabel?: string
}

const GetWxDataButton = ({ onBtnClick, selector, disabled, buttonLabel }: Props) => {
  const wxDataLoading = useSelector(selector)
  const label = buttonLabel ? buttonLabel : 'Get Weather Data'

  return (
    <Button
      disabled={disabled}
      data-testid="get-wx-data-button"
      onClick={onBtnClick}
      loading={wxDataLoading}
      variant="contained"
      color="primary"
      spinnercolor="white"
    >
      {label}
    </Button>
  )
}

export default React.memo(GetWxDataButton)
