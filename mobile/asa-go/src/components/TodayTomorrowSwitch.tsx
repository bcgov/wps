import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useEffect, useState } from "react";
import { DateTime } from "luxon"

interface TodayTomorrowSwitchProps {
  date: DateTime
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
}

const TodayTomorrowSwitch = ({date, setDate}: TodayTomorrowSwitchProps) => {
  const [value, setValue] = useState<number>(0)

const handleDayChange = (_: React.MouseEvent<HTMLElement>, newValue: number) => {
  if (newValue !== null) {
    setValue(newValue)
    const duration = newValue === 0 ? -1 : 1
    setDate(date.plus({day: duration}))
  }
}

useEffect(() => {
  const newValue = date.toISODate() === DateTime.now().toISODate() ? 0 : 1
  setValue(newValue)
}, [date])

  return (
    <ToggleButtonGroup exclusive onChange={handleDayChange} sx={{background: "white", height: "36px"}} value={value}>
      <ToggleButton sx={{width: "56px", maxWidth: "56px" }} value={0}>NOW</ToggleButton>
      <ToggleButton sx={{width: "56px", maxWidth: "56px" }} value={1}>TMR</ToggleButton>
    </ToggleButtonGroup>
  )
}

export default TodayTomorrowSwitch;
