import { InputLabel, MenuItem, Select } from '@material-ui/core'
import React from 'react'

export const MIN_PREP_DAYS = 2
export const MAX_PREP_DAYS = 5

export interface PrepDaySelectProps {
  days: number
  setDays: React.Dispatch<React.SetStateAction<number>>
}

const PrepDaysSelect = ({ days, setDays }: PrepDaySelectProps) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const changeHandler = (event: React.ChangeEvent<{ value: any }>) => {
    setDays(Number(event.target.value))
  }

  return (
    <React.Fragment>
      <InputLabel id="prep-days-label"># Prep Days</InputLabel>

      <Select variant="outlined" value={days} onChange={changeHandler}>
        <MenuItem value={2}>2</MenuItem>
        <MenuItem value={3}>3</MenuItem>
        <MenuItem value={4}>4</MenuItem>
        <MenuItem value={5}>5</MenuItem>
      </Select>
    </React.Fragment>
  )
}

export default React.memo(PrepDaysSelect)
