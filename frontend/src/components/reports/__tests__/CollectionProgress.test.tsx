import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CollectionProgress from '../CollectionProgress';
import type { CollectionProgress as CollectionProgressType, CollectionWeek } from '../../../types/dataCollection';
import { dataCollectionService } from '../../../services/dataCollectionService';

// Mock the dataCollectionService
vi.mock('../../../services/dataCollectionService', () => ({
  dataCollectionService: {
    getCollectionProgress: vi.fn(),
  },
}));

// Mock the AMCExecutionDetail component
vi.mock('../../executions/AMCExecutionDetail', () => ({
  default: vi.fn(({ isOpen, onClose, instanceId, executionId }) => 
    isOpen ? (
      <div data-testid="amc-execution-detail-modal">
        <div>Instance ID: {instanceId}</div>
        <div>Execution ID: {executionId}</div>
        <button onClick={onClose}>Close Modal</button>
      </div>
    ) : null
  ),
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  ArrowLeft: () => <div>ArrowLeft</div>,
  Calendar: () => <div>Calendar</div>,
  CheckCircle: () => <div>CheckCircle</div>,
  AlertCircle: () => <div>AlertCircle</div>,
  Clock: () => <div>Clock</div>,
  RefreshCw: () => <div>RefreshCw</div>,
  ExternalLink: () => <div>ExternalLink</div>,
  Eye: () => <div>Eye</div>,
  BarChart3: () => <div>BarChart3</div>,
}));

const createMockProgress = (overrides?: Partial<CollectionProgressType>): CollectionProgressType => ({
  collection_id: 'test-collection-123',
  status: 'running',
  progress_percentage: 50,
  statistics: {
    total_weeks: 10,
    completed: 5,
    pending: 3,
    running: 1,
    failed: 1,
  },
  weeks: [
    {
      id: 'week-1',
      week_start_date: '2025-01-01',
      week_end_date: '2025-01-07',
      status: 'completed',
      execution_id: 'exec-123',
      record_count: 1000,
      execution_time_seconds: 120,
    },
    {
      id: 'week-2',
      week_start_date: '2025-01-08',
      week_end_date: '2025-01-14',
      status: 'running',
      execution_id: 'exec-456',
      started_at: '2025-01-08T10:00:00Z',
    },
    {
      id: 'week-3',
      week_start_date: '2025-01-15',
      week_end_date: '2025-01-21',
      status: 'pending',
      execution_id: null,
    },
    {
      id: 'week-4',
      week_start_date: '2025-01-22',
      week_end_date: '2025-01-28',
      status: 'failed',
      execution_id: 'exec-789',
      error_message: 'Query timeout',
    },
  ] as CollectionWeek[],
  started_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-15T12:00:00Z',
  ...overrides,
});

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('CollectionProgress - Week Execution Click Handler', () => {
  const mockOnBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should trigger modal when clicking on a completed week with execution_id', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Find the completed week row - look for the status element instead
    const completedWeeks = screen.getAllByText('CheckCircle');
    expect(completedWeeks.length).toBeGreaterThan(0);
    const completedWeekElement = completedWeeks[0].closest('.px-6.py-4') || completedWeeks[0];
    
    // Click on the completed week
    fireEvent.click(completedWeekElement);

    // Check that the AMCExecutionDetail modal is opened
    await waitFor(() => {
      expect(screen.getByTestId('amc-execution-detail-modal')).toBeInTheDocument();
      expect(screen.getByText('Instance ID: instance-123')).toBeInTheDocument();
      expect(screen.getByText('Execution ID: exec-123')).toBeInTheDocument();
    });
  });

  it('should not trigger modal when clicking on a pending week without execution_id', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Find all week rows and filter for pending ones (those without execution_id)
    const weekRows = screen.getAllByTestId('week-row');
    const pendingWeekRow = weekRows.find(row => row.getAttribute('data-clickable') === 'false');
    
    // Click on the pending week
    if (pendingWeekRow) {
      fireEvent.click(pendingWeekRow);
    }

    // Check that the modal is NOT opened
    expect(screen.queryByTestId('amc-execution-detail-modal')).not.toBeInTheDocument();
  });

  it('should pass correct instance_id and execution_id to the modal', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-456"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Find a week with execution_id and click the View button
    const viewButtons = screen.getAllByTestId('view-execution-button');
    // Click on the last one (failed week with exec-789)
    fireEvent.click(viewButtons[viewButtons.length - 1]);

    // Check correct props are passed
    await waitFor(() => {
      expect(screen.getByTestId('amc-execution-detail-modal')).toBeInTheDocument();
      expect(screen.getByText('Instance ID: instance-456')).toBeInTheDocument();
      expect(screen.getByText('Execution ID: exec-789')).toBeInTheDocument();
    });
  });

  it('should close modal when close button is clicked', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Open modal by clicking a View button
    const viewButtons = screen.getAllByTestId('view-execution-button');
    fireEvent.click(viewButtons[0]);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByTestId('amc-execution-detail-modal')).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByText('Close Modal');
    fireEvent.click(closeButton);

    // Check modal is closed
    await waitFor(() => {
      expect(screen.queryByTestId('amc-execution-detail-modal')).not.toBeInTheDocument();
    });
  });

  it('should show visual feedback for clickable weeks', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Get all week rows
    const weekRows = screen.getAllByTestId('week-row');
    
    // Check that weeks with execution_id have clickable indicator
    const clickableWeeks = weekRows.filter(row => row.getAttribute('data-clickable') === 'true');
    expect(clickableWeeks.length).toBeGreaterThan(0);
    
    // Check that weeks without execution_id don't have clickable indicator
    const nonClickableWeeks = weekRows.filter(row => row.getAttribute('data-clickable') === 'false');
    expect(nonClickableWeeks.length).toBeGreaterThan(0);
  });

  it('should handle running weeks with execution_id correctly', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Find the view buttons and click the one for running week (exec-456)
    const viewButtons = screen.getAllByTestId('view-execution-button');
    // The running week is the second one with execution_id
    fireEvent.click(viewButtons[1]);

    // Check that the modal is opened (running weeks with execution_id are viewable)
    await waitFor(() => {
      expect(screen.getByTestId('amc-execution-detail-modal')).toBeInTheDocument();
      expect(screen.getByText('Execution ID: exec-456')).toBeInTheDocument();
    });
  });

  it('should handle missing instanceId prop gracefully', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue({
      ...mockProgress,
      instance_id: 'progress-instance-123', // Instance ID from progress data
    });

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        // No instanceId prop provided
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Click on a View button
    const viewButtons = screen.getAllByTestId('view-execution-button');
    fireEvent.click(viewButtons[0]);

    // Should use instance_id from progress data
    await waitFor(() => {
      expect(screen.getByTestId('amc-execution-detail-modal')).toBeInTheDocument();
      expect(screen.getByText('Instance ID: progress-instance-123')).toBeInTheDocument();
    });
  });

  it('should display visual indicators for execution links', async () => {
    const mockProgress = createMockProgress();
    vi.mocked(dataCollectionService.getCollectionProgress).mockResolvedValue(mockProgress);

    renderWithQueryClient(
      <CollectionProgress 
        collectionId="test-collection-123" 
        onBack={mockOnBack}
        instanceId="instance-123"
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Collection Progress/i)).toBeInTheDocument();
    });

    // Check for view execution buttons/links on completed weeks
    const viewButtons = screen.getAllByTestId('view-execution-button');
    expect(viewButtons.length).toBeGreaterThan(0);
    
    // Verify the button contains appropriate icon or text
    expect(viewButtons[0]).toHaveTextContent(/View|Eye/);
  });
});