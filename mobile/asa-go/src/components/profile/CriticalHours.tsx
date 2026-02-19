import { Typography } from "@mui/material";
import React from "react";
import { isNil } from "lodash";
import { formatCriticalHoursTimeText } from "@/utils/criticalHoursStartEndTime";

interface CriticalHoursProps {
  start?: number;
  end?: number;
}

const CriticalHours = ({ start, end }: CriticalHoursProps) => {
  let formattedCriticalHours = "-";

  if (!isNil(start) && !isNil(end)) {
    const [formattedStartTime, formattedEndTime] = formatCriticalHoursTimeText(
      start,
      end,
    );
    formattedCriticalHours = `${formattedStartTime} - ${formattedEndTime}`;
  }
  return (
    <Typography
      sx={{
        fontSize: "0.75rem",
        display: "flex",
        height: "100%",
        alignItems: "center",
        fontWeight: "bold",
      }}
      data-testid="critical-hours"
    >
      {formattedCriticalHours}
    </Typography>
  );
};

export default React.memo(CriticalHours);
