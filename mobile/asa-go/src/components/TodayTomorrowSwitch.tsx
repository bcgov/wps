import { Box, Button, styled } from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { selectDateOfInterest, setDateOfInterest } from '@/slices/dateOfInterestSlice'
import type { AppDispatch } from '@/store'
import { MAP_BUTTON_GREY } from '@/theme'
import { BORDER_RADIUS, BUTTON_HEIGHT } from '@/utils/constants'
import { getToday } from '@/utils/dataSliceUtils'

interface TodayTomorrowSwitchProps {
  border?: boolean
}

const BUTTON_WIDTH = 60

const StyledButton = styled(Button)({
  alignItems: 'center',
  display: 'flex',
  justifyContent: 'center',
  fontWeight: 'bold',
  fontSize: '1rem',
  minWidth: `${BUTTON_WIDTH}px`,
  maxWidth: `${BUTTON_WIDTH}px`,
  padding: '2px'
})

// A container for the text displayed on a button.
const StyledTextContainer = styled(Box)({
  alignItems: 'center',
  borderRadius: `${BORDER_RADIUS}px`,
  display: 'flex',
  height: '100%',
  width: '100%',
  justifyContent: 'center'
})

const TodayTomorrowSwitch = ({ border = false }: TodayTomorrowSwitchProps) => {
  const dispatch: AppDispatch = useDispatch()
  const date = useSelector(selectDateOfInterest)
  const borderStyle = border ? `1px solid ${MAP_BUTTON_GREY}` : 'none'

  const today = getToday()
  const isToday = date.toISODate() === today.toISODate()
  const isTomorrow = date.toISODate() === today.plus({ days: 1 }).toISODate()

  const handleDayChange = (newValue: number) => {
    // newValue: 0 = today, 1 = tomorrow
    const dateKey = today.plus({ days: newValue }).toISODate()
    if (dateKey) dispatch(setDateOfInterest(dateKey))
  }

  return (
    <Box
      id="tdy-tmr-switch-d"
      sx={{
        border: borderStyle,
        background: 'white',
        borderRadius: `${BORDER_RADIUS}px`,
        display: 'flex',
        height: `${BUTTON_HEIGHT}px`
      }}
    >
      <StyledButton disabled={isToday} onClick={() => handleDayChange(0)}>
        <StyledTextContainer
          sx={{
            backgroundColor: isToday ? MAP_BUTTON_GREY : 'white',
            color: isToday ? 'white' : MAP_BUTTON_GREY
          }}
        >
          NOW
        </StyledTextContainer>
      </StyledButton>
      <StyledButton disabled={isTomorrow} onClick={() => handleDayChange(1)}>
        <StyledTextContainer
          sx={{
            backgroundColor: isTomorrow ? MAP_BUTTON_GREY : 'white',
            color: isTomorrow ? 'white' : MAP_BUTTON_GREY
          }}
        >
          TMR
        </StyledTextContainer>
      </StyledButton>
    </Box>
  )
}

export default TodayTomorrowSwitch
