import { Alert, Snackbar } from "@mui/material";
import { SnackbarOrigin } from "@mui/material/Snackbar";

interface NotificationErrorSnackbarProps {
  open: boolean;
  onClose: () => void;
  message: string;
  anchorOrigin?: SnackbarOrigin;
}

const NotificationErrorSnackbar = ({
  open,
  onClose,
  message,
  anchorOrigin = { vertical: "top", horizontal: "center" },
}: NotificationErrorSnackbarProps) => {
  const snackbarSx = {
    ...(anchorOrigin.vertical === "top"
      ? {
          top: {
            xs: "calc(env(safe-area-inset-top) + 8px)",
            sm: "calc(env(safe-area-inset-top) + 24px)",
          },
        }
      : {}),
    width: {
      xs: "calc(100% - 16px)",
      sm: "min(420px, calc(100% - 48px))",
    },
    maxWidth: "100%",
  };

  return (
    <Snackbar
      open={open}
      autoHideDuration={6000}
      onClose={onClose}
      anchorOrigin={anchorOrigin}
      sx={snackbarSx}
    >
      <Alert onClose={onClose} severity="error" variant="filled">
        {message}
      </Alert>
    </Snackbar>
  );
};

export default NotificationErrorSnackbar;
