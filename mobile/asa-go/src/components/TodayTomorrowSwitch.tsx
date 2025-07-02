import { Box, Button, styled } from "@mui/material";
import { useState } from "react";
import { DateTime } from "luxon";

interface TodayTomorrowSwitchProps {
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
}

const DEFAULT_BORDER_RADIUS = 8;
const BUTTON_WIDTH = 48;
const TEXT_BOX_WIDTH = BUTTON_WIDTH - 4;
const MAX_SWITCH_WIDTH = 2 * BUTTON_WIDTH;
const BUTTON_HEIGHT = 32;
const TEXT_BOX_HEIGHT = BUTTON_HEIGHT - 4;

const StyledButton = styled(Button)({
  alignItems: "center",
  borderBottomLeftRadius: `${DEFAULT_BORDER_RADIUS}px`,
  borderTopLeftRadius: `${DEFAULT_BORDER_RADIUS}px`,
  borderTopRightRadius: 0,
  borderBottomRightRadius: 0,
  display: "flex",
  flexGrow: 1,
  fontSize: "0.8rem",
  fontWeight: "bold",
  height: `${BUTTON_HEIGHT}px`,
  justifyContent: "center",
  minWidth: `${BUTTON_WIDTH}px`,
  maxWidth: `${BUTTON_WIDTH}px`,
});

// A container for the text displayed on a button.
const StyledTextContainer = styled(Box)({
  alignItems: "center",
  borderRadius: `${DEFAULT_BORDER_RADIUS}px`,
  display: "flex",
  height: `${TEXT_BOX_HEIGHT}px`,
  justifyContent: "center",
  minWidth: `${TEXT_BOX_WIDTH}px`,
});

const TodayTomorrowSwitch = ({ date, setDate }: TodayTomorrowSwitchProps) => {
  const [value, setValue] = useState<number>(
    date.day === DateTime.now().day ? 0 : 1
  );

  const handleDayChange = (newValue: number) => {
    if (value !== newValue) {
      setValue(newValue);
      const duration = newValue === 0 ? -1 : 1;
      setDate(date.plus({ day: duration }));
    }
  };

  return (
    <Box
      id="tdy-tmr-switch-d"
      sx={{
        background: "white",
        borderRadius: `${DEFAULT_BORDER_RADIUS}px`,
        display: "flex",
        maxWidth: `${MAX_SWITCH_WIDTH}px`,
      }}
    >
      <StyledButton disabled={value === 0} onClick={() => handleDayChange(0)}>
        <StyledTextContainer
          sx={{
            backgroundColor: value === 0 ? "#7F7F7F" : "white",
            color: value === 0 ? "white" : "black",
          }}
        >
          NOW
        </StyledTextContainer>
      </StyledButton>
      <StyledButton disabled={value === 1} onClick={() => handleDayChange(1)}>
        <StyledTextContainer
          sx={{
            backgroundColor: value === 1 ? "#7F7F7F" : "white",
            color: value === 1 ? "white" : "black",
          }}
        >
          TMR
        </StyledTextContainer>
      </StyledButton>
    </Box>
  );
};

export default TodayTomorrowSwitch;
