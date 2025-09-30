/**
 * League Creation Page Component
 * 
 * Dedicated page for /app/leagues/new route
 * Provides same functionality as dialog but as a full page
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import LeagueCreationForm from './LeagueCreationForm';

const LeagueCreationPage = () => {
  const navigate = useNavigate();

  const handleCancel = () => {
    navigate('/app');
  };

  const handleSuccess = (data) => {
    // Success handling is managed by the form component
    console.log('League created:', data.leagueId);
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <LeagueCreationForm
        onCancel={handleCancel}
        onSuccess={handleSuccess}
        isDialog={false}
        className="space-y-6"
      />
    </div>
  );
};

export default LeagueCreationPage;