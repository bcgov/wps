import React from 'react'

import { Button } from '@mui/material'
import { MORECAST_WEATHER_PARAM_COLORS, MoreCastParamColors, theme } from 'app/theme'
import styled from '@emotion/styled'

const StyledButton = styled(Button)(
  ({ weatherParam, selected }: { weatherParam: keyof MoreCastParamColors; selected: boolean }) => ({
    marginLeft: theme.spacing(1),
    backgroundColor: selected
      ? MORECAST_WEATHER_PARAM_COLORS[weatherParam].active
      : MORECAST_WEATHER_PARAM_COLORS[weatherParam].inactive,
    color: MORECAST_WEATHER_PARAM_COLORS[weatherParam].text,
    '&:hover': {
      color: 'black',
      backgroundColor: 'white'
    }
  })
)

interface SelectableButtonProps {
  children?: React.ReactNode
  dataTestId?: string
  onClick: () => void
  selected: boolean
  weatherParam: keyof MoreCastParamColors
}

const SelectableButton = ({ children, dataTestId, onClick, selected, weatherParam }: SelectableButtonProps) => {
  return (
    <StyledButton
      data-testid={dataTestId}
      onClick={onClick}
      variant={selected ? 'contained' : 'outlined'}
      selected={selected}
      weatherParam={weatherParam}
    >
      {children}
    </StyledButton>
  )
}

export default React.memo(SelectableButton)
