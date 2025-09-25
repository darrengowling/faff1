
import React from 'react';

const TestComponent = () => {
  const clubSlots = 3; // This should trigger ESLint error
  const anotherNumber = 5; // This should also trigger ESLint error
  return <div>Club slots: {clubSlots}, Other: {anotherNumber}</div>;
};

export default TestComponent;

