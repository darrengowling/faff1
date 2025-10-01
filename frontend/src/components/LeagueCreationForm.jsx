/**
 * League Creation Form Component
 * 
 * Reusable form for both dialog and dedicated page implementation
 * Maintains identical testids across both contexts
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { TESTIDS } from '../testids.ts';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Separator } from './ui/separator';
import { TestableInput, TestableButton } from './testable/TestableComponents.tsx';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LeagueCreationForm = ({ 
  onCancel, 
  onSuccess, 
  isDialog = false,
  className = ''
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  // Form state
  const [submitting, setSubmitting] = useState(false);
  const [createSuccess, setCreateSuccess] = useState(false);
  const [justCreatedId, setJustCreatedId] = useState(null);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [competitionProfiles, setCompetitionProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    season: '2025-26',
    settings: {
      budget_per_manager: 100,
      min_increment: 1,
      club_slots_per_manager: 5,
      anti_snipe_seconds: 30,
      bid_timer_seconds: 60,
      league_size: { min: 2, max: 8 },
      scoring_rules: {
        club_goal: 1,
        club_win: 3,
        club_draw: 1
      }
    }
  });

  // Load competition profiles
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const response = await axios.get(`${API}/competition-profiles`);
        setCompetitionProfiles(response.data.profiles || []);
        if (response.data.profiles && response.data.profiles.length > 0) {
          setSelectedProfile(response.data.profiles[0]._id);
        }
      } catch (error) {
        console.error('Failed to fetch competition profiles:', error);
        setCompetitionProfiles([]);
      }
    };
    
    fetchProfiles();
  }, []);

  // Helper functions
  const updateSettings = (key, value) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        [key]: value
      }
    }));
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

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'League name is required';
    }
    
    if (formData.settings.budget_per_manager < 50 || formData.settings.budget_per_manager > 500) {
      newErrors.budget = 'Budget must be between £50 and £500';
    }
    
    if (formData.settings.club_slots_per_manager < 1 || formData.settings.club_slots_per_manager > 10) {
      newErrors.slots = 'Club slots must be between 1 and 10';
    }
    
    if (formData.settings.league_size.min < 2 || formData.settings.league_size.min > 8) {
      newErrors.min = 'Minimum managers must be between 2 and 8';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError('');
    
    try {
      const response = await axios.post(`${API}/leagues`, formData);
      
      if (response.status === 201) {
        // Atomic success handling for both contexts:
        
        // 1. Set success markers
        setCreateSuccess(true);
        setJustCreatedId(response.data.leagueId);
        
        // 2. Close dialog if in dialog context
        if (isDialog && onCancel) {
          onCancel(); // This sets data-state="closed"
        }
        
        // 3. Notify parent component
        if (onSuccess) {
          onSuccess(response.data);
        }
        
        // 4. Navigate to lobby in microtask
        queueMicrotask(() => {
          navigate(`/app/leagues/${response.data.leagueId}/lobby`);
        });
        
        toast.success(t('leagueCreation.leagueCreatedSuccess'));
        
      } else {
        const errorMessage = response.data?.message || 'Could not create league';
        setSubmitError(errorMessage);
      }
    } catch (error) {
      console.error('League creation error:', error);
      
      if (error.response?.status === 400 && error.response?.data?.detail) {
        setSubmitError(error.response.data.detail);
      } else {
        setSubmitError('Failed to create league. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={className}>
      {/* Success indicator - Always present for testing (Stable DOM Pattern) */}
      <div 
        data-testid={TESTIDS.createSuccess} 
        className={createSuccess ? 'sr-only' : 'sr-only'}
        aria-hidden={!createSuccess}
        style={{
          visibility: createSuccess ? 'visible' : 'hidden',
          height: '0px',
          overflow: 'hidden'
        }}
      >
        {createSuccess ? 'League creation successful' : 'No success yet'}
      </div>

      {!isDialog && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-theme-text">Create New League</h1>
          <p className="text-theme-text-secondary mt-2">Set up your auction league with friends</p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6" aria-busy={submitting}>
        {/* Loading indicator for tests */}
        {submitting && (
          <div 
            data-testid={TESTIDS.createLoading} 
            aria-hidden="true"
            className="sr-only"
          >
            Creating league...
          </div>
        )}

        {/* Submit Error */}
        {submitError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{submitError}</p>
          </div>
        )}

        {/* Basic Info */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">{t('leagueCreation.leagueName')}</Label>
            <TestableInput
              id="name"
              value={formData.name}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, name: e.target.value }));
                clearError('name');
              }}
              required
              loading={submitting}
              aria-describedby={errors.name ? "name-error" : undefined}
              className={errors.name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
              data-testid={TESTIDS.createNameInput}
            />
            {errors.name && (
              <p id="name-error" className="text-sm text-red-600" data-testid="create-error-name">
                {errors.name}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="season">{t('dashboard.season')}</Label>
            <Input
              id="season"
              placeholder="2025-26"
              value={formData.season}
              onChange={(e) => setFormData(prev => ({ ...prev, season: e.target.value }))}
              required
            />
          </div>
          
          {/* Competition Profile Selection */}
          <div className="space-y-2">
            <Label htmlFor="profile">Competition Template</Label>
            <select
              id="profile"
              className="w-full p-2 border border-gray-300 rounded-md"
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
            >
              {Array.isArray(competitionProfiles) && competitionProfiles.map(profile => (
                <option key={profile._id} value={profile._id}>
                  {profile.competition} ({profile.short_name}) - {profile.defaults.club_slots} slots
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-600">
              Choose a template to set default values. You can customize them below.
            </p>
          </div>
        </div>

        <Separator />

        {/* League Settings */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">League Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="budget">Budget per Manager (£)</Label>
              <TestableInput
                id="budget"
                type="number"
                min="50"
                max="500"
                value={formData.settings.budget_per_manager}
                onChange={(e) => {
                  updateSettings('budget_per_manager', e.target.value);
                  clearError('budget');
                }}
                loading={submitting}
                aria-describedby={errors.budget ? "budget-error" : undefined}
                className={errors.budget ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                data-testid={TESTIDS.createBudgetInput}
              />
              {errors.budget && (
                <p id="budget-error" className="text-sm text-red-600" data-testid="create-error-budget">
                  {errors.budget}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="slots">Club Slots per Manager</Label>
              <TestableInput
                id="slots"
                type="number"
                min="1"
                max="10"
                value={formData.settings.club_slots_per_manager}
                onChange={(e) => {
                  updateSettings('club_slots_per_manager', e.target.value);
                  clearError('slots');
                }}
                loading={submitting}
                aria-describedby={errors.slots ? "slots-error" : undefined}
                className={errors.slots ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                data-testid={TESTIDS.createSlotsInput}
              />
              {errors.slots && (
                <p id="slots-error" className="text-sm text-red-600" data-testid="create-error-slots">
                  {errors.slots}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="minIncrement">Min Bid Increment</Label>
              <Input
                id="minIncrement"
                type="number"
                min="1"
                max="10"
                value={formData.settings.min_increment}
                onChange={(e) => updateSettings('min_increment', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bidTimer">Bid Timer (seconds)</Label>
              <Input
                id="bidTimer"
                type="number"
                min="30"
                max="300"
                value={formData.settings.bid_timer_seconds}
                onChange={(e) => updateSettings('bid_timer_seconds', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="minManagers">Min Managers</Label>
              <Input
                id="minManagers"
                type="number"
                min="2"
                max="8"
                value={formData.settings.league_size?.min || 2}
                onChange={(e) => {
                  updateSettings('league_size', { 
                    ...formData.settings.league_size, 
                    min: parseInt(e.target.value) || 2 
                  });
                  clearError('min');
                }}
                aria-describedby={errors.min ? "min-error" : undefined}
                className={errors.min ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                data-testid={TESTIDS.createMinInput}
              />
              {errors.min && (
                <p id="min-error" className="text-sm text-red-600" data-testid="create-error-min">
                  {errors.min}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxManagers">Max Managers</Label>
              <Input
                id="maxManagers"
                type="number"
                min="2"
                max="8"
                value={formData.settings.league_size?.max || 8}
                onChange={(e) => updateSettings('league_size', { 
                  ...formData.settings.league_size, 
                  max: parseInt(e.target.value) || 8 
                })}
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          {onCancel && (
            <Button 
              type="button" 
              variant="outline" 
              className="flex-1"
              onClick={onCancel}
              disabled={submitting}
            >
              Cancel
            </Button>
          )}
          <TestableButton 
            type="submit" 
            className="flex-1" 
            disabled={submitting || Object.keys(errors).length > 0}
            loading={submitting}
            data-testid={TESTIDS.createSubmit}
          >
            {submitting ? 'Creating...' : 'Create League'}
          </TestableButton>
        </div>
      </form>
    </div>
  );
};

export default LeagueCreationForm;