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

export interface HamburgerMenuProps {
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
            {[
              { url: "https://psu.nrs.gov.bc.ca/", title: "Home" },
              {
                url: "https://www2.gov.bc.ca/gov/content/home/disclaimer",
                title: "Disclaimer",
              },
              {
                url: "https://www2.gov.bc.ca/gov/content/home/privacy",
                title: "Privacy",
              },
              {
                url: "https://www2.gov.bc.ca/gov/content/home/accessible-government",
                title: "Accessibility",
              },
              {
                url: "https://www2.gov.bc.ca/gov/content/home/copyright",
                title: "Copyright",
              },
              {
                url: "mailto:bcws.predictiveservices@gov.bc.ca",
                title: "Contact Us",
              },
            ].map((item, index) => (
              <ListItemButton
                divider
                key={`hamburger-menu-${index}`}
                onClick={() => handleListButtonClick(item.url)}
              >
                <Typography variant="subtitle1">{item.title}</Typography>
              </ListItemButton>
            ))}
          </List>
        </Grid>
      </Drawer>
    </>
  );
};
