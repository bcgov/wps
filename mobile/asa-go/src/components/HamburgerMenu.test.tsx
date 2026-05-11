import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { HamburgerMenu } from "@/components/HamburgerMenu";

vi.mock("@sentry/react", () => ({
  getFeedback: vi.fn(),
}))

vi.mock("@sentry/capacitor", () => ({}))

import { getFeedback } from "@sentry/react";
const mockGetFeedback = getFeedback as ReturnType<typeof vi.fn>;

describe("HamburgerMenu", () => {
  const defaultProps = { drawerTop: 60, drawerHeight: 740 };

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the menu button", () => {
    mockGetFeedback.mockReturnValue(undefined);
    render(<HamburgerMenu {...defaultProps} />);
    expect(screen.getByRole("button", { name: /open menu/i })).toBeInTheDocument();
  });

  it('opens the Sentry feedback dialog when Contact Us is clicked', async () => {
    const mockOpenDialog = vi.fn();
    mockGetFeedback.mockReturnValue({ openDialog: mockOpenDialog });

    render(<HamburgerMenu {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    const contactUs = await screen.findByText("Contact Us");
    fireEvent.click(contactUs);

    expect(mockOpenDialog).toHaveBeenCalled();
  });

  it('does not throw when getFeedback returns undefined and Contact Us is clicked', async () => {
    mockGetFeedback.mockReturnValue(undefined);

    render(<HamburgerMenu {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    const contactUs = await screen.findByText("Contact Us");
    expect(() => fireEvent.click(contactUs)).not.toThrow();
  });
});
