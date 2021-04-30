import React from 'react'
import { useSelector } from 'react-redux'

import { Button } from 'components'
import { RootState } from 'app/rootReducer'

interface Props {
  onBtnClick: () => void
  selector: (root: RootState) => boolean
}

const GetWxDataButton = ({ onBtnClick, selector }: Props) => {
  const wxDataLoading = useSelector(selector)

  return (
    <Button
      data-testid="get-wx-data-button"
      onClick={onBtnClick}
      loading={wxDataLoading}
      variant="contained"
      color="primary"
      spinnerColor="white"
    >
      Get Weather Data
    </Button>
  )
}

export default React.memo(GetWxDataButton)
