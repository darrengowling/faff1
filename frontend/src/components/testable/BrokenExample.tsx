// This should demonstrate the TypeScript error when testid is missing
import React from 'react';
import { TestableButton } from './TestableComponents';

export function WillFailTypeScript() {
  return (
    <TestableButton onClick={() => console.log('clicked')}>
      This will fail TypeScript compilation - missing required data-testid
    </TestableButton>
  );
}