import { Box, Fade } from "@mui/material";
import React, { forwardRef, useEffect } from "react";

interface ScaleContainerProps {
  visible: boolean;
  setVisible: React.Dispatch<React.SetStateAction<boolean>>;
}

const ScaleContainer = forwardRef(
  ({ visible, setVisible }: ScaleContainerProps, ref) => {
    useEffect(() => {
      if (visible) {
        const timer = setTimeout(() => setVisible(false), 2000);
        return () => clearTimeout(timer);
      }
    }, [visible]);

    return (
      <Fade in={visible} timeout={visible ? 0 : 2000}>
        <Box
          data-testid="scale-container"
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
      </Fade>
    );
  }
);
ScaleContainer.displayName = "ScaleContainer";

export default React.memo(ScaleContainer);
