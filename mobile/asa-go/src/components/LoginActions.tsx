import LoginButton from "@/components/LoginButton";
import { selectAuthentication } from "@/store";
import { Box, CircularProgress, Typography, useTheme } from "@mui/material";
import { isNull } from "lodash";
import { useSelector } from "react-redux";

interface LoginActionsProps {
  direction?: "row" | "column";
}

const LoginActions = ({ direction = "column" }: LoginActionsProps) => {
  const theme = useTheme();
  const { authenticating, error } = useSelector(selectAuthentication);

  if (authenticating) {
    return <CircularProgress color="secondary" />;
  }

  return (
    <Box
      sx={{
        alignItems: "center",
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing(2),
      }}
    >
      <Box
        sx={{
          alignItems: "center",
          display: "flex",
          flexDirection: direction,
          gap: theme.spacing(2),
          justifyContent: "center",
        }}
      >
        <LoginButton />
      </Box>
      {!isNull(error) && (
        <Typography sx={{ color: "white" }} variant="body1">
          Unable to login, please try again.
        </Typography>
      )}
    </Box>
  );
};

export default LoginActions;
