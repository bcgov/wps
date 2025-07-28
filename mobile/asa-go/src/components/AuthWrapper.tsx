import React from "react";
import { useSelector } from "react-redux";
import { Capacitor } from "@capacitor/core";
import { selectAuthentication } from "@/store";
import { Box, CircularProgress, Typography, useTheme } from "@mui/material";
import { isNull } from "lodash";
import LoginButton from "@/components/LoginButton";
import AsaIcon from "@/assets/asa-go-transparent.png";

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
          height: "40%",
          display: "flex",
          alignItems: "end",
          justifyContent: "center",
        }}
      >
        <Box sx={{ alignItems: "center", display: "flex", height: "200px" }}>
          <Box
            component="img"
            sx={{ height: "150px", width: "150px" }}
            src={AsaIcon}
          />
          <Typography sx={{ color: "white", fontWeight: "bold" }} variant="h2">
            ASA Go
          </Typography>
        </Box>
      </Box>
      <Box
        sx={{
          height: "60%",
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
