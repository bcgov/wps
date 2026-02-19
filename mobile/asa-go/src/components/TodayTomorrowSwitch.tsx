import { Box, Button, styled } from "@mui/material";
import { DateTime } from "luxon";
import { MAP_BUTTON_GREY } from "@/theme";
import { BORDER_RADIUS, BUTTON_HEIGHT } from "@/components/MapIconButton";
import { today } from "@/utils/dataSliceUtils";

interface TodayTomorrowSwitchProps {
  border?: boolean;
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
}

const BUTTON_WIDTH = 60;

const StyledButton = styled(Button)({
  alignItems: "center",
  display: "flex",
  justifyContent: "center",
  fontWeight: "bold",
  fontSize: "1rem",
  minWidth: `${BUTTON_WIDTH}px`,
  maxWidth: `${BUTTON_WIDTH}px`,
  padding: "2px",
});

// A container for the text displayed on a button.
const StyledTextContainer = styled(Box)({
  alignItems: "center",
  borderRadius: `${BORDER_RADIUS}px`,
  display: "flex",
  height: "100%",
  width: "100%",
  justifyContent: "center",
});

const TodayTomorrowSwitch = ({
  border = false,
  date,
  setDate,
}: TodayTomorrowSwitchProps) => {
  const borderStyle = border ? `1px solid ${MAP_BUTTON_GREY}` : "none";

  const isToday = date.day === today.day;

  const handleDayChange = (newValue: number) => {
    // newValue: 0 = today, 1 = tomorrow
    const shouldBeToday = newValue === 0;

    if (isToday !== shouldBeToday) {
      // If we need to go to today but we're on tomorrow, subtract a day
      // If we need to go to tomorrow but we're on today, add a day
      const duration = shouldBeToday ? -1 : 1;
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
        height: `${BUTTON_HEIGHT - 2}px`,
      }}
    >
      <StyledButton disabled={isToday} onClick={() => handleDayChange(0)}>
        <StyledTextContainer
          sx={{
            backgroundColor: isToday ? MAP_BUTTON_GREY : "white",
            color: isToday ? "white" : MAP_BUTTON_GREY,
          }}
        >
          NOW
        </StyledTextContainer>
      </StyledButton>
      <StyledButton disabled={!isToday} onClick={() => handleDayChange(1)}>
        <StyledTextContainer
          sx={{
            backgroundColor: !isToday ? MAP_BUTTON_GREY : "white",
            color: !isToday ? "white" : MAP_BUTTON_GREY,
          }}
        >
          TMR
        </StyledTextContainer>
      </StyledButton>
    </Box>
  );
};

export default TodayTomorrowSwitch;
