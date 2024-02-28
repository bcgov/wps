import React from 'react'

import { Button } from '@mui/material'
import { MORECAST_WEATHER_PARAMS, MoreCastParams, theme } from 'app/theme'
import styled from '@emotion/styled'

const StyledButton = styled(Button)(() => ({
  marginLeft: theme.spacing(1),
  '&:hover': {
    color: 'black',
    backgroundColor: 'white'
  }
}))

const SelectedButton = styled(StyledButton, { shouldForwardProp: prop => prop !== 'weatherParam' })(
  ({ weatherParam }: { weatherParam: keyof MoreCastParams }) => ({
    backgroundColor: MORECAST_WEATHER_PARAMS[weatherParam].active,
    color: MORECAST_WEATHER_PARAMS[weatherParam].text
  })
)

const UnSelectedButton = styled(StyledButton, { shouldForwardProp: prop => prop !== 'weatherParam' })(
  ({ weatherParam }: { weatherParam: keyof MoreCastParams }) => ({
    backgroundColor: MORECAST_WEATHER_PARAMS[weatherParam].inactive,
    color: MORECAST_WEATHER_PARAMS[weatherParam].text
  })
)

interface SelectableButtonProps {
  children?: React.ReactNode
  dataTestId?: string
  onClick: () => void
  selected: boolean
  weatherParam: keyof MoreCastParams
}

const SelectableButton = ({ children, dataTestId, onClick, selected, weatherParam }: SelectableButtonProps) => {
  return selected ? (
    <SelectedButton
      data-testid={`${dataTestId}-selected`}
      onClick={onClick}
      variant={selected ? 'contained' : 'outlined'}
      weatherParam={weatherParam}
    >
      {children}
    </SelectedButton>
  ) : (
    <UnSelectedButton
      data-testid={`${dataTestId}-unselected`}
      onClick={onClick}
      variant={selected ? 'contained' : 'outlined'}
      weatherParam={weatherParam}
    >
      {children}
    </UnSelectedButton>
  )
}

export default React.memo(SelectableButton)
