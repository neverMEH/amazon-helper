import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import QueryLibrary from '../QueryLibrary';
import * as queryTemplateService from '../../services/queryTemplateService';

// Mock the service
vi.mock('../../services/queryTemplateService', () => ({
  queryTemplateService: {
    listTemplates: vi.fn(),
    getCategories: vi.fn(),
    getTemplate: vi.fn(),
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
    useTemplate: vi.fn(),
    buildQueryFromTemplate: vi.fn(),
  }
}));

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: () => <div>Monaco Editor</div>
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
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('QueryLibrary', () => {
  const mockTemplates = [
    {
      id: '1',
      templateId: 'template-1',
      name: 'Top Products by Revenue',
      description: 'Analyze top performing products',
      category: 'Product Performance',
      sqlTemplate: 'SELECT * FROM products',
      parametersSchema: {
        startDate: { type: 'date', required: true },
        endDate: { type: 'date', required: true },
        limit: { type: 'number', default: 10 }
      },
      defaultParameters: { limit: 10 },
      isPublic: true,
      tags: ['revenue', 'products'],
      usageCount: 45,
      isOwner: false,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z'
    },
    {
      id: '2',
      templateId: 'template-2',
      name: 'Campaign Performance',
      description: 'Track campaign metrics',
      category: 'Advertising',
      sqlTemplate: 'SELECT * FROM campaigns',
      parametersSchema: {
        campaigns: { type: 'array', required: true },
        dateRange: { type: 'date', required: true }
      },
      defaultParameters: {},
      isPublic: true,
      tags: ['campaigns', 'performance'],
      usageCount: 32,
      isOwner: true,
      createdAt: '2025-01-02T00:00:00Z',
      updatedAt: '2025-01-02T00:00:00Z'
    },
    {
      id: '3',
      templateId: 'template-3',
      name: 'ASIN Analysis',
      description: 'Analyze ASIN performance',
      category: 'Product Performance',
      sqlTemplate: 'SELECT * FROM asins',
      parametersSchema: {
        asins: { type: 'array', required: true },
        metrics: { type: 'array', required: true }
      },
      defaultParameters: { metrics: ['impressions', 'clicks'] },
      isPublic: false,
      tags: ['asins', 'analysis'],
      usageCount: 18,
      isOwner: true,
      createdAt: '2025-01-03T00:00:00Z',
      updatedAt: '2025-01-03T00:00:00Z'
    }
  ];

  const mockCategories = ['Product Performance', 'Advertising', 'Attribution', 'Custom'];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(queryTemplateService.queryTemplateService.listTemplates).mockResolvedValue(mockTemplates);
    vi.mocked(queryTemplateService.queryTemplateService.getCategories).mockResolvedValue(mockCategories);
  });

  describe('Template Gallery', () => {
    it('renders the query library page with templates', async () => {
      renderWithProviders(<QueryLibrary />);

      expect(screen.getByText('Query Library')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search templates/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Top Products by Revenue')).toBeInTheDocument();
        expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
        expect(screen.getByText('ASIN Analysis')).toBeInTheDocument();
      });
    });

    it('displays template metadata correctly', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        const firstTemplate = screen.getByText('Top Products by Revenue').closest('div');
        expect(firstTemplate).toHaveTextContent('Product Performance');
        expect(firstTemplate).toHaveTextContent('45 uses');
        expect(firstTemplate).toHaveTextContent('revenue');
        expect(firstTemplate).toHaveTextContent('products');
      });
    });

    it('shows ownership badges correctly', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        const ownedTemplate = screen.getByText('Campaign Performance').closest('div');
        expect(ownedTemplate).toHaveTextContent('Your Template');
        
        const publicTemplate = screen.getByText('Top Products by Revenue').closest('div');
        expect(publicTemplate).toHaveTextContent('Public');
      });
    });
  });

  describe('Search and Filtering', () => {
    it('filters templates by search term', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('Top Products by Revenue')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      fireEvent.change(searchInput, { target: { value: 'campaign' } });

      await waitFor(() => {
        expect(screen.queryByText('Top Products by Revenue')).not.toBeInTheDocument();
        expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
      });
    });

    it('filters templates by category', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('All Categories')).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'Advertising' } });

      await waitFor(() => {
        expect(screen.queryByText('Top Products by Revenue')).not.toBeInTheDocument();
        expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
      });
    });

    it('filters templates by ownership', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('All Templates')).toBeInTheDocument();
      });

      const ownershipFilter = screen.getByRole('combobox', { name: /ownership/i });
      fireEvent.change(ownershipFilter, { target: { value: 'my-templates' } });

      await waitFor(() => {
        expect(screen.queryByText('Top Products by Revenue')).not.toBeInTheDocument();
        expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
        expect(screen.getByText('ASIN Analysis')).toBeInTheDocument();
      });
    });

    it('combines multiple filters correctly', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getAllByTestId('template-card')).toHaveLength(3);
      });

      // Apply category filter
      const categoryFilter = screen.getByRole('combobox', { name: /category/i });
      fireEvent.change(categoryFilter, { target: { value: 'Product Performance' } });

      // Apply search filter
      const searchInput = screen.getByPlaceholderText(/search templates/i);
      fireEvent.change(searchInput, { target: { value: 'asin' } });

      await waitFor(() => {
        expect(screen.queryByText('Top Products by Revenue')).not.toBeInTheDocument();
        expect(screen.queryByText('Campaign Performance')).not.toBeInTheDocument();
        expect(screen.getByText('ASIN Analysis')).toBeInTheDocument();
      });
    });
  });

  describe('Template Actions', () => {
    it('opens template detail modal on click', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('Top Products by Revenue')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Top Products by Revenue'));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText('Template Details')).toBeInTheDocument();
      });
    });

    it('navigates to query builder with template', async () => {
      const mockNavigate = vi.fn();
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom');
        return {
          ...actual,
          useNavigate: () => mockNavigate
        };
      });

      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('Top Products by Revenue')).toBeInTheDocument();
      });

      const useButton = screen.getAllByText('Use Template')[0];
      fireEvent.click(useButton);

      expect(mockNavigate).toHaveBeenCalledWith('/query-builder/new', {
        state: { templateId: 'template-1' }
      });
    });

    it('allows editing owned templates', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        const ownedTemplate = screen.getByText('Campaign Performance').closest('div');
        expect(ownedTemplate?.querySelector('[aria-label="Edit template"]')).toBeInTheDocument();
      });
    });

    it('prevents editing public templates not owned', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        const publicTemplate = screen.getByText('Top Products by Revenue').closest('div');
        expect(publicTemplate?.querySelector('[aria-label="Edit template"]')).not.toBeInTheDocument();
      });
    });

    it('allows deleting owned templates', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        const ownedTemplate = screen.getByText('Campaign Performance').closest('div');
        const deleteButton = ownedTemplate?.querySelector('[aria-label="Delete template"]');
        expect(deleteButton).toBeInTheDocument();
      });

      // Click delete and confirm
      const deleteButton = screen.getAllByLabelText('Delete template')[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Delete Template')).toBeInTheDocument();
        expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(queryTemplateService.queryTemplateService.deleteTemplate).toHaveBeenCalledWith('template-2');
      });
    });
  });

  describe('Create New Template', () => {
    it('opens create template modal', async () => {
      renderWithProviders(<QueryLibrary />);

      const createButton = screen.getByRole('button', { name: /create template/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText('Create New Template')).toBeInTheDocument();
      });
    });

    it('validates required fields in create form', async () => {
      renderWithProviders(<QueryLibrary />);

      const createButton = screen.getByRole('button', { name: /create template/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /save template/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/category is required/i)).toBeInTheDocument();
        expect(screen.getByText(/sql template is required/i)).toBeInTheDocument();
      });
    });
  });

  describe('Template Sorting', () => {
    it('sorts templates by usage count', async () => {
      renderWithProviders(<QueryLibrary />);

      await waitFor(() => {
        expect(screen.getByText('Sort by')).toBeInTheDocument();
      });

      const sortSelect = screen.getByRole('combobox', { name: /sort/i });
      fireEvent.change(sortSelect, { target: { value: 'usage' } });

      await waitFor(() => {
        const templateCards = screen.getAllByTestId('template-card');
        expect(templateCards[0]).toHaveTextContent('Top Products by Revenue');
        expect(templateCards[1]).toHaveTextContent('Campaign Performance');
        expect(templateCards[2]).toHaveTextContent('ASIN Analysis');
      });
    });

    it('sorts templates by date', async () => {
      renderWithProviders(<QueryLibrary />);

      const sortSelect = screen.getByRole('combobox', { name: /sort/i });
      fireEvent.change(sortSelect, { target: { value: 'newest' } });

      await waitFor(() => {
        const templateCards = screen.getAllByTestId('template-card');
        expect(templateCards[0]).toHaveTextContent('ASIN Analysis');
        expect(templateCards[1]).toHaveTextContent('Campaign Performance');
        expect(templateCards[2]).toHaveTextContent('Top Products by Revenue');
      });
    });

    it('sorts templates alphabetically', async () => {
      renderWithProviders(<QueryLibrary />);

      const sortSelect = screen.getByRole('combobox', { name: /sort/i });
      fireEvent.change(sortSelect, { target: { value: 'alphabetical' } });

      await waitFor(() => {
        const templateCards = screen.getAllByTestId('template-card');
        expect(templateCards[0]).toHaveTextContent('ASIN Analysis');
        expect(templateCards[1]).toHaveTextContent('Campaign Performance');
        expect(templateCards[2]).toHaveTextContent('Top Products by Revenue');
      });
    });
  });
});