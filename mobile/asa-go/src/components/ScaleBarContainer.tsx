import { Box } from "@mui/material";
import React, { forwardRef } from "react";

const ScalebarContainer = forwardRef((_, ref) => {
  return (
    <Box
      ref={ref}
      sx={{
        position: "absolute",
        bottom: "0.5rem",
        right: "0.5rem",
        zIndex: 1,
        ["& div.ol-scale-line"]: {
          background: "none",
          bottom: 0,
          left: "auto",
          right: 0,
        },
      }}
    ></Box>
  );
});
ScalebarContainer.displayName = "ScalebarContainer";

export default React.memo(ScalebarContainer);
