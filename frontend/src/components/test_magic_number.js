
import React from 'react';

const TestComponent = () => {
  const clubSlots = 3; // This should trigger ESLint error
  return <div>Club slots: {clubSlots}</div>;
};

export default TestComponent;

