import { Box, Fade } from "@mui/material";
import React, { forwardRef, useEffect } from "react";

interface ScalebarContainerProps {
  visible: boolean;
  setVisible: React.Dispatch<React.SetStateAction<boolean>>;
}

const ScalebarContainer = forwardRef(
  ({ visible, setVisible }: ScalebarContainerProps, ref) => {
    useEffect(() => {
      if (visible) {
        const timer = setTimeout(() => setVisible(false), 3000);
        return () => clearTimeout(timer);
      }
    }, [visible]);

    return (
      <Fade in={visible} timeout={visible ? 0 : 2000}>
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
      </Fade>
    );
  }
);
ScalebarContainer.displayName = "ScalebarContainer";

export default React.memo(ScalebarContainer);
