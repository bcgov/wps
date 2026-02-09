import { theme } from "@/theme";
import { NavPanel } from "@/utils/constants";
import {
  Box,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  styled,
} from "@mui/material";

const StyledListItemButton = styled(ListItemButton)({
  color: theme.palette.primary.contrastText,
  padding: theme.spacing(1),
  "&.Mui-selected": {
    backgroundColor: theme.palette.primary.dark,
    color: theme.palette.secondary.main,
    "&:hover": {
      backgroundColor: theme.palette.primary.dark,
    },
  },
  "&:hover": {
    backgroundColor: theme.palette.primary.dark,
  },
  height: "auto",
  display: "flex",
  flexDirection: "column",
});

const StyledListItemIcon = styled(ListItemIcon)({
  color: "inherit",
  justifyContent: "center",
});

const StyledListItemText = styled(ListItemText)({
  color: "inherit",
  "& .MuiListItemText-primary": {
    fontSize: "14px",
    fontWeight: 500,
  },
});

interface SideNavigationListItemProps {
  icon: React.ReactNode;
  navItem: NavPanel;
  tab: NavPanel;
  setTab: (newValue: NavPanel) => void;
}

const SideNavigationListItem = ({
  icon,
  navItem,
  tab,
  setTab,
}: SideNavigationListItemProps) => {
  return (
    <ListItem key={navItem} sx={{ px: 0 }}>
      <StyledListItemButton
        selected={tab === navItem}
        onClick={() => setTab(navItem)}
      >
        <Box
          sx={{
            display: "flex",
            flexGrow: 1,
            alignItems: "self-end",
          }}
        >
          <StyledListItemIcon>{icon}</StyledListItemIcon>
        </Box>
        <Box sx={{ display: "flex", flexGrow: 1, alignItems: "self-start" }}>
          <StyledListItemText primary={navItem} />
        </Box>
      </StyledListItemButton>
    </ListItem>
  );
};

export default SideNavigationListItem;
