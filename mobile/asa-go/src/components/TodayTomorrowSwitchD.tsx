import { Box, Button } from "@mui/material";
import { useEffect, useState } from "react";
import { DateTime } from "luxon"

interface TodayTomorrowSwitchProps {
  date: DateTime
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
}

const DEFAULT_BORDER_RADIUS = 16

const TodayTomorrowSwitchD = ({date, setDate}: TodayTomorrowSwitchProps) => {
  const [value, setValue] = useState<number>(0)

  const handleDayChange = (newValue: number) => {
    if (value !== newValue) {
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

    <Box
      id="tdy-tmr-switch-d"
      sx={{
        background: "white",
        border: "1px solid black",
        borderRadius: `${DEFAULT_BORDER_RADIUS}px`,
        display: "flex"
      }}
    >
      <Button
        onClick={() => handleDayChange(0)}
        sx={{
          alignItems: "center",
          borderBottomLeftRadius: `${DEFAULT_BORDER_RADIUS}px`,
          borderTopLeftRadius: `${DEFAULT_BORDER_RADIUS}px`,
          borderTopRightRadius: 0,
          borderBottomRightRadius: 0,
          display: "flex",
          flexGrow: 1,
          color: value === 0 ? "white" : "black",
          fontSize: "0.8rem",
          fontWeight: "bold",
          height: "32px",
          justifyContent: "center",
          minWidth: "56px",
          maxWidth: "56px"
        }}
      >
        <Box sx={{
          alignItems: "center",
          backgroundColor: value === 0 ? "#7F7F7F" : "white",
          borderRadius: `${DEFAULT_BORDER_RADIUS}px`,
          display: "flex",
          height: "28px",
          justifyContent: "center",
          minWidth: "52px"
        }}>
          NOW
        </Box>
      </Button>
      <Button
        onClick={() => handleDayChange(1)}
        sx={{
          alignItems: "center",
          borderBottomLeftRadius: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: `${DEFAULT_BORDER_RADIUS}px`,
          borderBottomRightRadius: `${DEFAULT_BORDER_RADIUS}px`,
          color: value === 1 ? "white" : "black",
          display: "flex",
          flexGrow: 1,
          fontSize: "0.8rem",
          fontWeight: "bold",
          height: "32px",
          justifyContent: "center",
          minWidth: "56px",
          maxWidth: "56px"
        }}
      >
        <Box sx={{
          alignItems: "center",
          backgroundColor: value === 1 ? "#7F7F7F" : "white",
          borderRadius: `${DEFAULT_BORDER_RADIUS}px`,
          display: "flex",
          height: "28px",
          justifyContent: "center",
          minWidth: "52px"
        }}>
        TMR
        </Box>
      </Button>
    </Box>
  )
}

export default TodayTomorrowSwitchD
