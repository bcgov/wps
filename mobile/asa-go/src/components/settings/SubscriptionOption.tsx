import { FireZoneUnit } from "@/api/fbaAPI";
import LoadingSwitch from "@/components/LoadingSwitch";
import { selectSettings } from "@/store";
import { fireZoneUnitNameFormatter } from "@/utils/stringUtils";
import {
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
} from "@mui/material";
import { useSelector } from "react-redux";

interface SubscriptionOptionProps {
  fireZoneUnit: FireZoneUnit;
  onToggle: (fireZoneUnitId: number) => void;
  disabled: boolean;
  loading?: boolean;
  error?: string;
}

const SubscriptionOption = ({
  fireZoneUnit,
  onToggle,
  disabled,
  loading,
  error,
}: SubscriptionOptionProps) => {
  const { subscriptions } = useSelector(selectSettings);
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onToggle(fireZoneUnit.id);
  };

  const handleSubscriptionUpdate = () => {
    onToggle(fireZoneUnit.id);
  };

  return (
    <ListItem disableGutters disablePadding>
      <ListItemButton disableRipple onClick={handleSubscriptionUpdate}>
        <ListItemText>
          <Typography
            variant="body2"
            fontWeight="bold"
            sx={{ whiteSpace: "pre-line" }}
          >
            {fireZoneUnitNameFormatter(fireZoneUnit.name)}
          </Typography>
        </ListItemText>
        <span onClick={(e) => e.stopPropagation()}>
          <LoadingSwitch
            edge="end"
            disabled={disabled}
            loading={loading}
            error={error}
            checked={subscriptions.includes(fireZoneUnit.id)}
            onChange={handleSwitchChange}
            aria-label={`Toggle subscription for ${fireZoneUnit.name}`}
          />
        </span>
      </ListItemButton>
    </ListItem>
  );
};

export default SubscriptionOption;
