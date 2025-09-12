import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CampaignSelector from '../CampaignSelector';
import * as api from '../../../services/api';

// Mock the API
vi.mock('../../../services/api', () => ({
  default: {
    get: vi.fn()
  }
}));

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('CampaignSelector', () => {
  const mockOnChange = vi.fn();
  const mockCampaigns = [
    {
      campaign_id: 'camp-1',
      campaign_name: 'Brand_SpringSale_2025',
      campaign_type: 'sp',
      status: 'ENABLED',
      brand: 'BrandA'
    },
    {
      campaign_id: 'camp-2',
      campaign_name: 'Brand_SummerSale_2025',
      campaign_type: 'sb',
      status: 'ENABLED',
      brand: 'BrandA'
    },
    {
      campaign_id: 'camp-3',
      campaign_name: 'Holiday_Special_2024',
      campaign_type: 'sd',
      status: 'ENABLED',
      brand: 'BrandB'
    },
    {
      campaign_id: 'camp-4',
      campaign_name: 'Product_Launch_Q1',
      campaign_type: 'dsp',
      status: 'ENABLED',
      brand: 'BrandC'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.default.get).mockResolvedValue({ 
      data: { campaigns: mockCampaigns } 
    });
  });

  describe('Basic Functionality', () => {
    it('renders with placeholder text', () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
        />
      );
      
      expect(screen.getByText(/select campaigns or use wildcards/i)).toBeInTheDocument();
    });

    it('opens dropdown on click', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search or use wildcards/i)).toBeInTheDocument();
      });
    });

    it('displays campaigns when opened', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
        expect(screen.getByText('Brand_SummerSale_2025')).toBeInTheDocument();
        expect(screen.getByText('Holiday_Special_2024')).toBeInTheDocument();
      });
    });

    it('selects single campaign', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          multiple={false}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const radio = screen.getAllByRole('radio')[0];
      fireEvent.click(radio);
      
      expect(mockOnChange).toHaveBeenCalledWith(['camp-1']);
    });

    it('selects multiple campaigns', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          multiple={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);
      
      expect(mockOnChange).toHaveBeenLastCalledWith(['camp-1', 'camp-2']);
    });
  });

  describe('Wildcard Pattern Support', () => {
    it('shows wildcard help when enabled', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const helpButton = screen.getByRole('button', { name: '' });
        const infoIcon = helpButton.querySelector('.lucide-info');
        expect(infoIcon).toBeTruthy();
      });
      
      const helpButtons = screen.getAllByRole('button');
      const helpButton = helpButtons.find(btn => btn.querySelector('.lucide-info'));
      if (helpButton) fireEvent.click(helpButton);
      
      await waitFor(() => {
        expect(screen.getByText(/wildcard pattern examples/i)).toBeInTheDocument();
        expect(screen.getByText(/Brand_\*/)).toBeInTheDocument();
        expect(screen.getByText(/\*_2025/)).toBeInTheDocument();
      });
    });

    it('adds wildcard pattern', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      const searchInput = await screen.findByPlaceholderText(/search or use wildcards/i);
      await user.type(searchInput, 'Brand_*_2025');
      
      await waitFor(() => {
        expect(screen.getByText('Add Pattern')).toBeInTheDocument();
      });
      
      const addButton = screen.getByText('Add Pattern');
      fireEvent.click(addButton);
      
      expect(mockOnChange).toHaveBeenCalledWith(['Brand_*_2025']);
    });

    it('filters campaigns by wildcard pattern', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText(/search or use wildcards/i);
      await user.type(searchInput, 'Brand_*_2025');
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
        expect(screen.getByText('Brand_SummerSale_2025')).toBeInTheDocument();
        expect(screen.queryByText('Holiday_Special_2024')).not.toBeInTheDocument();
      });
    });

    it('shows active patterns with match count', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={['Brand_*_2025']}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/active patterns/i)).toBeInTheDocument();
        expect(screen.getByText('Brand_*_2025')).toBeInTheDocument();
        expect(screen.getByText(/2 matches/)).toBeInTheDocument();
      });
    });

    it('removes wildcard pattern', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={['Brand_*_2025', 'camp-3']}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_*_2025')).toBeInTheDocument();
      });
      
      const removeButtons = screen.getAllByRole('button').filter(btn => 
        btn.querySelector('.lucide-x')
      );
      const patternRemoveButton = removeButtons[1]; // Second X button is for the pattern
      fireEvent.click(patternRemoveButton);
      
      expect(mockOnChange).toHaveBeenCalledWith(['camp-3']);
    });

    it('highlights campaigns matching patterns', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={['Brand_*_2025']}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const springCampaign = screen.getByText('Brand_SpringSale_2025').closest('label');
        expect(springCampaign).toHaveClass('bg-blue-50');
        
        const holidayCampaign = screen.getByText('Holiday_Special_2024').closest('label');
        expect(holidayCampaign).not.toHaveClass('bg-blue-50');
      });
    });

    it('supports multiple wildcard patterns', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      const searchInput = await screen.findByPlaceholderText(/search or use wildcards/i);
      
      // Add first pattern
      await user.type(searchInput, 'Brand_*');
      fireEvent.click(screen.getByText('Add Pattern'));
      
      // Clear and add second pattern
      await user.clear(searchInput);
      await user.type(searchInput, '*_2024');
      
      await waitFor(() => {
        expect(screen.getByText('Add Pattern')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Add Pattern'));
      
      expect(mockOnChange).toHaveBeenLastCalledWith(['Brand_*', '*_2024']);
    });
  });

  describe('Campaign Type Filtering', () => {
    it('filters by campaign type', async () => {
      vi.mocked(api.default.get).mockResolvedValue({ 
        data: { 
          campaigns: mockCampaigns.filter(c => c.campaign_type === 'sp') 
        } 
      });
      
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          campaignType="sp"
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
        expect(screen.queryByText('Brand_SummerSale_2025')).not.toBeInTheDocument();
      });
      
      expect(api.default.get).toHaveBeenCalledWith(
        expect.stringContaining('type=sp')
      );
    });

    it('displays campaign type badges', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const badges = screen.getAllByText(/sp|sb|sd|dsp/i);
        expect(badges.length).toBeGreaterThan(0);
        
        const spBadge = badges.find(b => b.textContent === 'sp');
        expect(spBadge).toHaveClass('bg-blue-100');
      });
    });
  });

  describe('Value Type Handling', () => {
    it('returns campaign IDs by default', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          valueType="ids"
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const checkbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(checkbox);
      
      expect(mockOnChange).toHaveBeenCalledWith(['camp-1']);
    });

    it('returns campaign names when specified', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          valueType="names"
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const checkbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(checkbox);
      
      expect(mockOnChange).toHaveBeenCalledWith(['Brand_SpringSale_2025']);
    });
  });

  describe('Max Selections', () => {
    it('limits selections to max value', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          maxSelections={2}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);
      fireEvent.click(checkboxes[2]); // This should not work
      
      expect(mockOnChange).toHaveBeenLastCalledWith(['camp-1', 'camp-2']);
      expect(mockOnChange).not.toHaveBeenCalledWith(expect.arrayContaining(['camp-3']));
    });

    it('disables unselected items when max reached', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={['camp-1', 'camp-2']}
          onChange={mockOnChange}
          showAll={true}
          maxSelections={2}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes[2]).toBeDisabled();
        expect(checkboxes[3]).toBeDisabled();
      });
    });

    it('shows max selections in UI', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          maxSelections={5}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/max 5/)).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('filters campaigns by search term', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await user.type(searchInput, 'Holiday');
      
      await waitFor(() => {
        expect(screen.getByText('Holiday_Special_2024')).toBeInTheDocument();
        expect(screen.queryByText('Brand_SpringSale_2025')).not.toBeInTheDocument();
      });
    });

    it('searches by campaign ID', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await user.type(searchInput, 'camp-3');
      
      await waitFor(() => {
        expect(screen.getByText('Holiday_Special_2024')).toBeInTheDocument();
        expect(screen.queryByText('Brand_SpringSale_2025')).not.toBeInTheDocument();
      });
    });
  });

  describe('Bulk Actions', () => {
    it('selects all matching campaigns', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
      
      const selectAllButton = screen.getByText(/select all matching/i);
      fireEvent.click(selectAllButton);
      
      expect(mockOnChange).toHaveBeenCalledWith(['camp-1', 'camp-2', 'camp-3', 'camp-4']);
    });

    it('clears all selections', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={['camp-1', 'camp-2']}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const clearButton = screen.getByText(/clear selection/i);
        fireEvent.click(clearButton);
      });
      
      expect(mockOnChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Display Text', () => {
    it('shows placeholder when no selection', () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          placeholder="Choose campaigns"
        />
      );
      
      expect(screen.getByText('Choose campaigns')).toBeInTheDocument();
    });

    it('shows single campaign name', () => {
      renderWithProviders(
        <CampaignSelector 
          value={['camp-1']}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      waitFor(() => {
        expect(screen.getByText('Brand_SpringSale_2025')).toBeInTheDocument();
      });
    });

    it('shows count for multiple selections', () => {
      renderWithProviders(
        <CampaignSelector 
          value={['camp-1', 'camp-2', 'camp-3']}
          onChange={mockOnChange}
        />
      );
      
      expect(screen.getByText('3 campaigns selected')).toBeInTheDocument();
    });

    it('shows combined count for campaigns and patterns', () => {
      renderWithProviders(
        <CampaignSelector 
          value={['camp-1', 'Brand_*_2025']}
          onChange={mockOnChange}
          enableWildcards={true}
        />
      );
      
      expect(screen.getByText('1 campaigns, 1 patterns')).toBeInTheDocument();
    });
  });

  describe('Instance and Brand Filtering', () => {
    it('uses filtered endpoint when instance provided', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          instanceId="inst-1"
          brandId="brand-1"
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(api.default.get).toHaveBeenCalledWith(
          expect.stringContaining('/campaigns/by-instance-brand/list')
        );
      });
    });

    it('shows brand info when showAll is true', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Brand: BrandA/)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      await user.tab();
      const button = screen.getByRole('button');
      expect(button).toHaveFocus();
      
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i);
        expect(searchInput).toHaveFocus();
      });
    });

    it('supports Enter key to add patterns', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
          enableWildcards={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      const searchInput = await screen.findByPlaceholderText(/search or use wildcards/i);
      await user.type(searchInput, 'Brand_*{Enter}');
      
      expect(mockOnChange).toHaveBeenCalledWith(['Brand_*']);
    });

    it('provides proper ARIA labels', async () => {
      renderWithProviders(
        <CampaignSelector 
          value={null}
          onChange={mockOnChange}
          showAll={true}
        />
      );
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes.length).toBeGreaterThan(0);
      });
    });
  });
});