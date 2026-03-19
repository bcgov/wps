import { useRef, useState, useCallback } from "react";
import Drawer, { DrawerProps } from "@mui/material/Drawer";
import Box from "@mui/material/Box";

interface SwipeableDrawerProps
  extends Omit<DrawerProps, "anchor" | "slotProps" | "PaperProps"> {
  // How far the user must drag (px) before dismissing on release
  dismissThreshold?: number;
  onClose: () => void;
}

export function SwipeableBottomDrawer({
  children,
  dismissThreshold = 120,
  onClose,
  ...drawerProps
}: SwipeableDrawerProps) {
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startYRef = useRef(0);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // Record where the finger started so we can compute delta
    startYRef.current = e.touches[0].clientY;
    setIsDragging(true);
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const delta = e.touches[0].clientY - startYRef.current;
    // Only allow downward drag — ignore upward pulls
    if (delta > 0) setDragY(delta);
  }, []);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    if (dragY >= dismissThreshold) {
      onClose();
    }
    // Reset position regardless — CSS transition handles the snap-back
    setDragY(0);
  }, [dragY, dismissThreshold, onClose]);

  return (
    <Drawer
      anchor="bottom"
      hideBackdrop
      ModalProps={{
        disableScrollLock: true,
      }}
      onClose={onClose}
      slotProps={{
        root: {
          sx: {
            pointerEvents: "none",
          },
        },
        paper: {
          sx: {
            borderRadius: "12px 12px 0 0",
            // Disable transition during drag so position tracks the finger
            // Re-enable on release so snap-back animates smoothly
            transition: isDragging
              ? "none"
              : "transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            transform: dragY > 0 ? `translateY(${dragY}px)` : undefined,
            // Respect iOS home indicator
            paddingBottom: "env(safe-area-inset-bottom)",
            pointerEvents: "auto",
          },
        },
      }}
      {...drawerProps}
    >
      {/* Handle — the primary drag target */}
      <Box
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          py: 1.5,
          cursor: "grab",
          // Prevent browser scroll interfering with drag
          touchAction: "none",
        }}
      >
        <Box
          sx={{
            width: 36,
            height: 4,
            borderRadius: 2,
            bgcolor: "grey.300",
          }}
        />
      </Box>

      {children}
    </Drawer>
  );
}
