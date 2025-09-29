// This file should fail TypeScript compilation if uncommented
// because TestableButton requires a data-testid prop

import React from 'react';
import { TestableButton } from './TestableComponents';

export function BrokenTestComponent() {
  return (
    <div>
      {/* This should cause TypeScript error - missing data-testid */}
      {/* 
      <TestableButton onClick={() => console.log('clicked')}>
        Missing TestID Button
      </TestableButton>
      */}
      
      {/* This should work fine - has required data-testid */}
      <TestableButton data-testid="working-button" onClick={() => console.log('clicked')}>
        Working Button
      </TestableButton>
    </div>
  );
}