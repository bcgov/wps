import Box from "@mui/material/Box";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";

interface SwipeableBottomDrawerProps {
  children: React.ReactNode;
  open: boolean;
  onClose: () => void;
}

export function SwipeableBottomDrawer({
  children,
  open,
  onClose,
}: SwipeableBottomDrawerProps) {
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
        root: {
          sx: {
            pointerEvents: "none",
          },
        },
        paper: {
          sx: {
            borderRadius: "12px 12px 0 0",
            paddingBottom: "env(safe-area-inset-bottom)",
            pointerEvents: "auto",
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
}
