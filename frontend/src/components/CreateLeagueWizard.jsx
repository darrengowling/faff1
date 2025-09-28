/**
 * Create League Wizard Component
 * 
 * Multi-step wizard for creating a new league with all required configuration
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { EnhancedBreadcrumb } from './ui/enhanced-breadcrumb';
import { ArrowLeft, ArrowRight, Trophy, Users, DollarSign, Settings } from 'lucide-react';
import { TESTIDS } from '../testids.ts';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateLeagueWizard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    slots: 3, // Default club slots
    budget: 100, // Default budget
    minBid: 1 // Default minimum bid
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(false);

  // Update form field
  const updateField = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (!formData.name || formData.name.trim().length < 3) {
      newErrors.name = 'League name must be at least 3 characters';
    }

    if (formData.slots < 2 || formData.slots > 8) {
      newErrors.slots = 'Club slots must be between 2 and 8';
    }

    if (formData.budget < 50 || formData.budget > 1000) {
      newErrors.budget = 'Budget must be between 50 and 1000';
    }

    if (formData.minBid < 1 || formData.minBid > 10) {
      newErrors.minBid = 'Minimum bid must be between 1 and 10';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors below');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API}/leagues`, {
        name: formData.name.trim(),
        club_slots: parseInt(formData.slots),
        budget: parseInt(formData.budget),
        min_bid: parseInt(formData.minBid)
      });

      toast.success('League created successfully!');
      
      // Navigate to the new league
      navigate(`/app`);
      
    } catch (error) {
      console.error('League creation failed:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create league. Please try again.';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb Navigation */}
      <EnhancedBreadcrumb />
      
      {/* Main Content */}
      <div className="max-w-2xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Trophy className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New League</h1>
          <p className="text-lg text-gray-600">
            Set up your Champions League fantasy competition
          </p>
        </div>

        {/* Wizard Form */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">League Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-8">
              
              {/* League Name */}
              <div>
                <label htmlFor="league-name" className="block text-sm font-medium text-gray-700 mb-2">
                  <Trophy className="w-4 h-4 inline mr-1" />
                  League Name
                </label>
                <input
                  type="text"
                  id="league-name"
                  value={formData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Champions League Friends 2024"
                  data-testid={TESTIDS.createLeagueWizardName}
                  required
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                )}
              </div>

              {/* Club Slots */}
              <div>
                <label htmlFor="club-slots" className="block text-sm font-medium text-gray-700 mb-2">
                  <Users className="w-4 h-4 inline mr-1" />
                  Club Slots per Manager
                </label>
                <select
                  id="club-slots"
                  value={formData.slots}
                  onChange={(e) => updateField('slots', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.slots ? 'border-red-500' : 'border-gray-300'
                  }`}
                  data-testid={TESTIDS.createLeagueWizardSlots}
                >
                  <option value={2}>2 clubs</option>
                  <option value={3}>3 clubs (recommended)</option>
                  <option value={4}>4 clubs</option>
                  <option value={5}>5 clubs</option>
                  <option value={6}>6 clubs</option>
                  <option value={7}>7 clubs</option>
                  <option value={8}>8 clubs</option>
                </select>
                {errors.slots && (
                  <p className="mt-1 text-sm text-red-600">{errors.slots}</p>
                )}
                <p className="mt-1 text-sm text-gray-500">
                  How many Champions League clubs each manager can own
                </p>
              </div>

              {/* Budget */}
              <div>
                <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
                  <DollarSign className="w-4 h-4 inline mr-1" />
                  Starting Budget
                </label>
                <select
                  id="budget"
                  value={formData.budget}
                  onChange={(e) => updateField('budget', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.budget ? 'border-red-500' : 'border-gray-300'
                  }`}
                  data-testid={TESTIDS.createLeagueWizardBudget}
                >
                  <option value={75}>75 coins</option>
                  <option value={100}>100 coins (recommended)</option>
                  <option value={150}>150 coins</option>
                  <option value={200}>200 coins</option>
                </select>
                {errors.budget && (
                  <p className="mt-1 text-sm text-red-600">{errors.budget}</p>
                )}
                <p className="mt-1 text-sm text-gray-500">
                  Virtual currency for the auction
                </p>
              </div>

              {/* Minimum Bid */}
              <div>
                <label htmlFor="min-bid" className="block text-sm font-medium text-gray-700 mb-2">
                  <Settings className="w-4 h-4 inline mr-1" />
                  Minimum Bid
                </label>
                <select
                  id="min-bid"
                  value={formData.minBid}
                  onChange={(e) => updateField('minBid', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.minBid ? 'border-red-500' : 'border-gray-300'
                  }`}
                  data-testid={TESTIDS.createLeagueWizardMin}
                >
                  <option value={1}>1 coin (recommended)</option>
                  <option value={2}>2 coins</option>
                  <option value={3}>3 coins</option>
                  <option value={5}>5 coins</option>
                </select>
                {errors.minBid && (
                  <p className="mt-1 text-sm text-red-600">{errors.minBid}</p>
                )}
                <p className="mt-1 text-sm text-gray-500">
                  Minimum amount for each bid
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/app')}
                  className="flex items-center"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
                
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex items-center"
                  data-testid={TESTIDS.createLeagueWizardSubmit}
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating League...
                    </>
                  ) : (
                    <>
                      Create League
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
              
            </form>
          </CardContent>
        </Card>

        {/* Help Text */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            Need help? Check out our{' '}
            <button 
              type="button"
              onClick={() => window.open('/help/league-setup', '_blank')}
              className="text-blue-600 hover:underline focus:outline-none"
            >
              league setup guide
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default CreateLeagueWizard;