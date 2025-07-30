import axios from "@/api/axios";
import { authenticate } from "@/slices/authenticationSlice";
import { AppDispatch, AppThunk, selectToken } from "@/store";
import { Button, Typography, useTheme } from "@mui/material";

import { isNil } from "lodash";
import { useDispatch } from "react-redux";

const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use((config) => {
    const token = selectToken(getState());
    if (!isNil(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });
};

interface LoginButonProps {
  label: string;
}

const LoginButton = ({ label }: LoginButonProps) => {
  const dispatch: AppDispatch = useDispatch();
  const theme = useTheme();

  const handleLogin = () => {
    dispatch(authenticate());
    dispatch(setAxiosRequestInterceptors());
  };
  return (
    <Button
      onClick={handleLogin}
      size="large"
      sx={{
        border: "1px solid white",
        color: "white",
        display: "block",
        mt: theme.spacing(5),
      }}
      variant="outlined"
    >
      <Typography
        sx={{
          justifyContent: "center",
          display: "flex",
          fontWeight: "bold",
        }}
      >
        {label}
      </Typography>
    </Button>
  );
};

export default LoginButton;
