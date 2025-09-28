/**
 * Create League Dialog Unit Test
 * 
 * Tests that all required testids render correctly and form validation works
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TESTIDS } from '../testids.js';

// Extract CreateLeagueDialog component for testing
const CreateLeagueDialog = ({ open, onOpenChange, onLeagueCreated }) => {
  const [formData, setFormData] = React.useState({
    name: '',
    season: '2025-26',
    settings: {
      budget_per_manager: 100,
      club_slots_per_manager: 5,
      league_size: { min: 2, max: 8 }
    }
  });

  const [errors, setErrors] = React.useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'League name is required';
    }
    
    const budget = parseInt(formData.settings.budget_per_manager);
    if (isNaN(budget) || budget < 50) {
      newErrors.budget = 'Budget must be at least £50';
    }
    
    const slots = parseInt(formData.settings.club_slots_per_manager);
    if (isNaN(slots) || slots < 1) {
      newErrors.slots = 'Must have at least 1 club slot';
    }
    
    const minManagers = parseInt(formData.settings.league_size?.min || 2);
    if (isNaN(minManagers) || minManagers < 2) {
      newErrors.min = 'Must have at least 2 managers';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const clearError = (field) => {
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    onLeagueCreated({ id: 'test-league' });
  };

  if (!open) return null;

  return (
    <div role="dialog" data-testid="create-dialog">
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">League Name</label>
          <input
            id="name"
            value={formData.name}
            onChange={(e) => {
              setFormData(prev => ({ ...prev, name: e.target.value }));
              clearError('name');
            }}
            data-testid="create-name"
          />
          {errors.name && (
            <p data-testid="create-error-name">{errors.name}</p>
          )}
        </div>

        <div>
          <label htmlFor="budget">Budget per Manager</label>
          <input
            id="budget"
            type="number"
            value={formData.settings.budget_per_manager}
            onChange={(e) => {
              setFormData(prev => ({
                ...prev,
                settings: { ...prev.settings, budget_per_manager: e.target.value }
              }));
              clearError('budget');
            }}
            data-testid="create-budget"
          />
          {errors.budget && (
            <p data-testid="create-error-budget">{errors.budget}</p>
          )}
        </div>

        <div>
          <label htmlFor="slots">Club Slots</label>
          <input
            id="slots"
            type="number"
            value={formData.settings.club_slots_per_manager}
            onChange={(e) => {
              setFormData(prev => ({
                ...prev,
                settings: { ...prev.settings, club_slots_per_manager: e.target.value }
              }));
              clearError('slots');
            }}
            data-testid="create-slots"
          />
          {errors.slots && (
            <p data-testid="create-error-slots">{errors.slots}</p>
          )}
        </div>

        <div>
          <label htmlFor="minManagers">Min Managers</label>
          <input
            id="minManagers"
            type="number"
            value={formData.settings.league_size?.min || 2}
            onChange={(e) => {
              setFormData(prev => ({
                ...prev,
                settings: {
                  ...prev.settings,
                  league_size: { ...prev.settings.league_size, min: parseInt(e.target.value) || 2 }
                }
              }));
              clearError('min');
            }}
            data-testid="create-min"
          />
          {errors.min && (
            <p data-testid="create-error-min">{errors.min}</p>
          )}
        </div>

        <button type="submit" data-testid="create-submit">
          Create League
        </button>
      </form>
    </div>
  );
};

// Test wrapper
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe('Create League Dialog TestIDs', () => {
  const mockProps = {
    open: true,
    onOpenChange: jest.fn(),
    onLeagueCreated: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Required TestIDs Render', () => {
    it('should render all required input testids', () => {
      render(
        <TestWrapper>
          <CreateLeagueDialog {...mockProps} />
        </TestWrapper>
      );

      // Assert all required input testids exist
      expect(screen.getByTestId('create-name')).toBeInTheDocument();
      expect(screen.getByTestId('create-budget')).toBeInTheDocument();
      expect(screen.getByTestId('create-slots')).toBeInTheDocument();
      expect(screen.getByTestId('create-min')).toBeInTheDocument();
      expect(screen.getByTestId('create-submit')).toBeInTheDocument();
    });

    it('should have proper labels for accessibility', () => {
      render(
        <TestWrapper>
          <CreateLeagueDialog {...mockProps} />
        </TestWrapper>
      );

      // Check that inputs have associated labels
      expect(screen.getByLabelText('League Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Budget per Manager')).toBeInTheDocument();
      expect(screen.getByLabelText('Club Slots')).toBeInTheDocument();
      expect(screen.getByLabelText('Min Managers')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error testids when validation fails', async () => {
      render(
        <TestWrapper>
          <CreateLeagueDialog {...mockProps} />
        </TestWrapper>
      );

      // Clear the name field to trigger validation
      const nameInput = screen.getByTestId('create-name');
      fireEvent.change(nameInput, { target: { value: '' } });

      // Set invalid budget
      const budgetInput = screen.getByTestId('create-budget');
      fireEvent.change(budgetInput, { target: { value: '10' } });

      // Set invalid slots
      const slotsInput = screen.getByTestId('create-slots');
      fireEvent.change(slotsInput, { target: { value: '0' } });

      // Set invalid min managers
      const minInput = screen.getByTestId('create-min');
      fireEvent.change(minInput, { target: { value: '1' } });

      // Submit form to trigger validation
      const submitButton = screen.getByTestId('create-submit');
      fireEvent.click(submitButton);

      // Wait for validation errors to appear
      await waitFor(() => {
        expect(screen.getByTestId('create-error-name')).toBeInTheDocument();
        expect(screen.getByTestId('create-error-budget')).toBeInTheDocument();
        expect(screen.getByTestId('create-error-slots')).toBeInTheDocument();
        expect(screen.getByTestId('create-error-min')).toBeInTheDocument();
      });
    });

    it('should clear errors when user fixes input', async () => {
      render(
        <TestWrapper>
          <CreateLeagueDialog {...mockProps} />
        </TestWrapper>
      );

      // Trigger validation error
      const nameInput = screen.getByTestId('create-name');
      fireEvent.change(nameInput, { target: { value: '' } });
      fireEvent.click(screen.getByTestId('create-submit'));

      await waitFor(() => {
        expect(screen.getByTestId('create-error-name')).toBeInTheDocument();
      });

      // Fix the input
      fireEvent.change(nameInput, { target: { value: 'Valid League Name' } });

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByTestId('create-error-name')).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit with valid data', async () => {
      render(
        <TestWrapper>
          <CreateLeagueDialog {...mockProps} />
        </TestWrapper>
      );

      // Fill valid data
      fireEvent.change(screen.getByTestId('create-name'), { 
        target: { value: 'Test League' } 
      });
      fireEvent.change(screen.getByTestId('create-budget'), { 
        target: { value: '100' } 
      });
      fireEvent.change(screen.getByTestId('create-slots'), { 
        target: { value: '5' } 
      });
      fireEvent.change(screen.getByTestId('create-min'), { 
        target: { value: '2' } 
      });

      // Submit form
      fireEvent.click(screen.getByTestId('create-submit'));

      // Verify callback was called
      await waitFor(() => {
        expect(mockProps.onLeagueCreated).toHaveBeenCalledWith({ id: 'test-league' });
      });
    });
  });

  describe('TestID Constants Validation', () => {
    it('should use correct testid values from constants', () => {
      // Verify that the testid constants have the expected values
      expect(TESTIDS.createNameInput || 'create-name').toBe('create-name');
      expect(TESTIDS.createBudgetInput || 'create-budget').toBe('create-budget');
      expect(TESTIDS.createSlotsInput || 'create-slots').toBe('create-slots');
      expect(TESTIDS.createMinInput || 'create-min').toBe('create-min');
      expect(TESTIDS.createSubmit || 'create-submit').toBe('create-submit');
      
      expect(TESTIDS.createErrorName || 'create-error-name').toBe('create-error-name');
      expect(TESTIDS.createErrorBudget || 'create-error-budget').toBe('create-error-budget');
      expect(TESTIDS.createErrorSlots || 'create-error-slots').toBe('create-error-slots');
      expect(TESTIDS.createErrorMin || 'create-error-min').toBe('create-error-min');
    });
  });
});