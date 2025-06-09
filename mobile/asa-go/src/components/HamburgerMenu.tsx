import {
  Drawer,
  IconButton,
  List,
  Typography,
  ListItemButton,
} from "@mui/material";
import { EmailComposer } from "capacitor-email-composer";
import Grid from "@mui/material/Grid2";

import { Menu as MenuIcon, Close as CloseIcon } from "@mui/icons-material";

import { useState } from "react";
import { RunType, FireCenter, FireShape } from "@/api/fbaAPI";
import { DateTime } from "luxon";

export interface HamburgerMenuProps {
  runType: RunType;
  setRunType: React.Dispatch<React.SetStateAction<RunType>>;
  date: DateTime;
  updateDate: (d: DateTime) => void;
  selectedFireCenter?: FireCenter;
  fireCenterOptions: FireCenter[];
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  setZoomSource: React.Dispatch<
    React.SetStateAction<"fireCenter" | "fireShape" | undefined>
  >;
  drawerTop: number;
  drawerHeight: number;
}

export const HamburgerMenu = ({
  drawerTop,
  drawerHeight,
}: HamburgerMenuProps) => {
  const [open, setOpen] = useState(false);

  const handleListButtonClick = (url: string) => {
    if (url.startsWith("mail:to")) {
      EmailComposer.open({
        to: ["bcws.predictiveservices@gov.bc.ca"],
        subject: "ASA App Contact",
        body: "",
        isHtml: false,
      });
    } else {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <>
      <IconButton onClick={() => setOpen(true)}>
        <MenuIcon fontSize="large" sx={{ color: "white" }} />
      </IconButton>
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{
          sx: {
            top: `${drawerTop}px`,
            height: `${drawerHeight}px`,
            backgroundColor: "lightGrey",
            borderTopLeftRadius: 16,
            borderBottomLeftRadius: 16,
          },
        }}
      >
        <Grid
          container
          spacing={1}
          direction={"column"}
          sx={{ width: 250, padding: "16px" }}
        >
          <Grid container alignItems="center" justifyContent="space-between">
            <IconButton
              onClick={() => setOpen(false)}
              sx={{
                cursor: "pointer",
                backgroundColor: "transparent",
                transition: "background-color 0.2s",
                alignSelf: "flex-end",
                marginLeft: "auto",
                "&:hover": {
                  backgroundColor: "#f0f0f0",
                },
              }}
              aria-label="close settings"
            >
              <CloseIcon />
            </IconButton>
          </Grid>
          <List
            sx={{
              width: "100%",
              "& .MuiListItemButton-root": {
                width: "100%",
                justifyContent: "flex-end",
              },
            }}
          >
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick("https://psu.nrs.gov.bc.ca/")
              }
            >
              <Typography variant="subtitle1">Home</Typography>
            </ListItemButton>
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick(
                  "https://www2.gov.bc.ca/gov/content/home/disclaimer"
                )
              }
            >
              Disclaimer
            </ListItemButton>
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick(
                  "https://www2.gov.bc.ca/gov/content/home/privacy"
                )
              }
            >
              Privacy
            </ListItemButton>
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick(
                  "https://www2.gov.bc.ca/gov/content/home/accessible-government"
                )
              }
            >
              Accessibility
            </ListItemButton>
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick(
                  "https://www2.gov.bc.ca/gov/content/home/copyright"
                )
              }
            >
              Copyright
            </ListItemButton>
            <ListItemButton
              divider
              onClick={() =>
                handleListButtonClick(
                  "mailto:bcws.predictiveservices@gov.bc.ca"
                )
              }
            >
              Contact Us
            </ListItemButton>
          </List>
        </Grid>
      </Drawer>
    </>
  );
};
