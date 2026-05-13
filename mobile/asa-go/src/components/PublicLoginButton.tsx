import { continueAsGuest } from "@/slices/authenticationSlice";
import { AppDispatch } from "@/store";
import { Button } from "@mui/material";
import { useDispatch } from "react-redux";

const PublicLoginButton = () => {
  const dispatch: AppDispatch = useDispatch();
  const handleClick = () => {
    dispatch(continueAsGuest());
  };
  return (
    <Button
      onClick={handleClick}
      sx={{ color: "white", textDecoration: "underline" }}
    >
      Continue as guest
    </Button>
  );
};

export default PublicLoginButton;
