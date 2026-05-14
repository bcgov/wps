import Box from "@mui/material/Box";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import { useMediaQuery, useTheme } from "@mui/material";
import { useIsPortrait } from "@/hooks/useIsPortrait";

interface SwipeableBottomDrawerProps {
  children: React.ReactNode;
  open: boolean;
  onClose: () => void;
}

export const SwipeableBottomDrawer = ({
  children,
  open,
  onClose,
}: SwipeableBottomDrawerProps) => {
  const theme = useTheme();
  const isPortrait = useIsPortrait();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down("lg"));
  const useSideSheet = !isPortrait && isSmallScreen;

  return (
    <SwipeableDrawer
      anchor="bottom"
      allowSwipeInChildren
      disableDiscovery
      disableSwipeToOpen
      hideBackdrop
      ModalProps={{
        disableScrollLock: true,
        keepMounted: true,
      }}
      open={open}
      onClose={onClose}
      onOpen={() => {}}
      slotProps={{
        // let map gestures pass through outside the sheet while keeping the sheet itself interactive.
        root: {
          sx: {
            pointerEvents: "none",
          },
        },
        paper: {
          sx: {
            borderRadius: "12px 12px 0 0",
            display: "flex",
            flexDirection: "column",
            // in landscape on small screens constrain the sheet into a tall panel on the left.
            left: useSideSheet ? theme.spacing(1) : 0,
            right: useSideSheet ? "auto" : 0,
            paddingBottom: useSideSheet
              ? theme.spacing(1)
              : "env(safe-area-inset-bottom)",
            pointerEvents: "auto",
            bottom: 0,
            height: useSideSheet
              ? `calc(100% - ${theme.spacing(2)})`
              : undefined,
            width: useSideSheet ? "min(320px, 50vw)" : undefined,
            willChange: "transform",
          },
        },
      }}
    >
      <Box
        sx={{
          alignItems: "center",
          cursor: "grab",
          display: "flex",
          justifyContent: "center",
          py: 1.5,
          touchAction: "none",
        }}
      >
        <Box
          sx={{
            bgcolor: "grey.300",
            borderRadius: 2,
            height: 4,
            width: 134,
          }}
        />
      </Box>
      {children}
    </SwipeableDrawer>
  );
};
