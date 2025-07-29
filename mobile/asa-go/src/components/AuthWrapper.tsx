import AsaIcon from "@/assets/asa-go-transparent.png";
import LoginButton from "@/components/LoginButton";
import { selectAuthentication } from "@/store";
import { Capacitor } from "@capacitor/core";
import { Box, CircularProgress, Typography, useTheme } from "@mui/material";
import { isNull } from "lodash";
import React from "react";
import { useSelector } from "react-redux";

interface Props {
  children: React.ReactElement;
}

const AuthWrapper = ({ children }: Props) => {
  const theme = useTheme();
  const { isAuthenticated, authenticating, error } =
    useSelector(selectAuthentication);

  // TODO implement for Android
  if (Capacitor.getPlatform() === "android") {
    return <React.StrictMode>{children}</React.StrictMode>;
  }

  if (isAuthenticated) {
    return <React.StrictMode>{children}</React.StrictMode>;
  }

  return (
    <Box
      sx={{
        bgcolor: theme.palette.primary.dark,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
      }}
    >
      <Box
        sx={{
          alignItems: "flex-end",
          display: "flex",
          flexGrow: 1,
          justifyContent: "center",
        }}
      >
        <Box sx={{ display: "flex", flexGrow: 1, justifyContent: "Center" }}>
          <Box
            component="img"
            sx={{ height: "300px", width: "300px" }}
            src={AsaIcon}
          />
        </Box>
      </Box>
      <Box
        sx={{
          alignItems: "center",
          justifyContent: "center",
          display: "flex",
        }}
      >
        <Typography
          sx={{
            color: "white",
            fontWeight: "bold",
          }}
          variant="h2"
        >
          ASA Go
        </Typography>
      </Box>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          flexGrow: 1,
          alignItems: "center",
        }}
      >
        {!authenticating && (
          <>
            <LoginButton label="Login" />
          </>
        )}
        {authenticating && (
          <Box sx={{ pt: theme.spacing(4) }}>
            <CircularProgress color="secondary" />
          </Box>
        )}
        {!isNull(error) && (
          <Typography
            sx={{ color: "white", mt: theme.spacing(5) }}
            variant="h5"
          >
            Unable to login, please try again.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default React.memo(AuthWrapper);
