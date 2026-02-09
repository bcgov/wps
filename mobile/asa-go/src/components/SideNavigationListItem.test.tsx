import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SideNavigationListItem from "@/components/SideNavigationListItem";
import { NavPanel } from "@/utils/constants";
import { theme } from "@/theme";

describe("SideNavigationListItem", () => {
  // Test constants
  const mockIcon = <div data-testid="test-icon">Test Icon</div>;
  const mockNavItem = NavPanel.ADVISORY;
  const mockTab = NavPanel.MAP;
  const mockSetTab = vi.fn();

  it("renders the component with icon and text", () => {
    render(
      <SideNavigationListItem
        icon={mockIcon}
        navItem={mockNavItem}
        tab={mockTab}
        setTab={mockSetTab}
      />,
    );

    // Check if icon is rendered
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
    // Check if text is rendered
    expect(screen.getByText(mockNavItem)).toBeInTheDocument();
  });

  it("renders with selected styles when tab matches navItem", () => {
    render(
      <SideNavigationListItem
        icon={mockIcon}
        navItem={mockNavItem}
        tab={mockNavItem}
        setTab={mockSetTab}
      />,
    );

    // Check if selected styles are applied
    const button = screen.getByRole("button");
    expect(button).toHaveClass("Mui-selected");
    expect(button).toHaveStyle({ backgroundColor: theme.palette.primary.dark });
    expect(button).toHaveStyle({ color: theme.palette.secondary.main });
  });

  it("renders with default styles when tab does not match navItem", () => {
    render(
      <SideNavigationListItem
        icon={mockIcon}
        navItem={mockNavItem}
        tab={NavPanel.MAP}
        setTab={mockSetTab}
      />,
    );

    // Check if selected styles are not applied
    const button = screen.getByRole("button");
    expect(button).not.toHaveClass("Mui-selected");
    expect(button).toHaveStyle({ color: theme.palette.primary.contrastText });
  });

  it("calls setTab with correct navItem when clicked", () => {
    render(
      <SideNavigationListItem
        icon={mockIcon}
        navItem={mockNavItem}
        tab={mockTab}
        setTab={mockSetTab}
      />,
    );

    // Click the button
    fireEvent.click(screen.getByRole("button"));

    // Check if setTab is called with correct navItem
    expect(mockSetTab).toHaveBeenCalledTimes(1);
    expect(mockSetTab).toHaveBeenCalledWith(mockNavItem);
  });

  it("renders different nav items correctly", () => {
    const navItems = Object.values(NavPanel);

    navItems.forEach((navItem) => {
      render(
        <SideNavigationListItem
          icon={mockIcon}
          navItem={navItem}
          tab={mockTab}
          setTab={mockSetTab}
        />,
      );

      expect(screen.getByText(navItem)).toBeInTheDocument();
    });
  });
});
