import { Box, Button, styled } from "@mui/material";
import { useEffect, useState } from "react";
import { DateTime } from "luxon";
import { MAP_BUTTON_GREY } from "@/theme";
import { BORDER_RADIUS, BUTTON_HEIGHT } from "@/components/MapIconButton";
import { today } from "@/utils/dataSliceUtils";

interface TodayTomorrowSwitchProps {
  border?: boolean;
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
}

const BUTTON_WIDTH = 48;
const TEXT_BOX_WIDTH = BUTTON_WIDTH - 4;
const TEXT_BOX_HEIGHT = BUTTON_HEIGHT - 4;

const StyledButton = styled(Button)({
  alignItems: "center",
  borderBottomLeftRadius: `${BORDER_RADIUS}px`,
  borderTopLeftRadius: `${BORDER_RADIUS}px`,
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
  borderRadius: `${BORDER_RADIUS}px`,
  display: "flex",
  height: `${TEXT_BOX_HEIGHT}px`,
  justifyContent: "center",
  minWidth: `${TEXT_BOX_WIDTH}px`,
});

const TodayTomorrowSwitch = ({
  border = false,
  date,
  setDate,
}: TodayTomorrowSwitchProps) => {
  const borderStyle = border ? `1px solid ${MAP_BUTTON_GREY}` : "none";
  const [value, setValue] = useState<number>(date.day === today.day ? 0 : 1);

  useEffect(() => {
    setValue(date.day === today.day ? 0 : 1);
  }, [date]);

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
        border: borderStyle,
        background: "white",
        borderRadius: `${BORDER_RADIUS}px`,
        display: "flex",
      }}
    >
      <StyledButton disabled={value === 0} onClick={() => handleDayChange(0)}>
        <StyledTextContainer
          sx={{
            backgroundColor: value === 0 ? MAP_BUTTON_GREY : "white",
            color: value === 0 ? "white" : "black",
          }}
        >
          NOW
        </StyledTextContainer>
      </StyledButton>
      <StyledButton disabled={value === 1} onClick={() => handleDayChange(1)}>
        <StyledTextContainer
          sx={{
            backgroundColor: value === 1 ? MAP_BUTTON_GREY : "white",
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
