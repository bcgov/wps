import { Alert, AlertColor, Snackbar } from "@mui/material";
import { SnackbarOrigin } from "@mui/material/Snackbar";

interface NotificationErrorSnackbarProps {
  open: boolean;
  onClose: () => void;
  message: string;
  anchorOrigin?: SnackbarOrigin;
  severity?: AlertColor;
  autoHideDuration?: number | null;
}

const NotificationErrorSnackbar = ({
  open,
  onClose,
  message,
  anchorOrigin = { vertical: "top", horizontal: "center" },
  severity = "error",
  autoHideDuration = 6000,
}: NotificationErrorSnackbarProps) => (
  <Snackbar
    open={open}
    autoHideDuration={autoHideDuration}
    onClose={onClose}
    anchorOrigin={anchorOrigin}
  >
    <Alert onClose={onClose} severity={severity} variant="filled">
      {message}
    </Alert>
  </Snackbar>
);

export default NotificationErrorSnackbar;
