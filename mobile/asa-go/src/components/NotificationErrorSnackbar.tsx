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
}: NotificationErrorSnackbarProps) => (
  <Snackbar
    open={open}
    autoHideDuration={6000}
    onClose={onClose}
    anchorOrigin={anchorOrigin}
  >
    <Alert onClose={onClose} severity="error" variant="filled">
      {message}
    </Alert>
  </Snackbar>
);

export default NotificationErrorSnackbar;
