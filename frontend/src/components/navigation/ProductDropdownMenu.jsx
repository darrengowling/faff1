/**
 * Product Dropdown Menu Component
 * Navigation dropdown for product features
 */

import React from 'react';
import { ChevronDown } from 'lucide-react';
import { Button } from '../ui/button';
import { TESTIDS } from '../../testids.ts';

export const ProductDropdownMenu = ({ isOpen, onToggle, onClose }) => {
  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggle}
        className="flex items-center space-x-1"
        data-testid={TESTIDS.navDropdownProduct}
      >
        <span>Product</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>
      
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50">
          <div className="py-1">
            <a
              href="#auction"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              data-testid={TESTIDS.navDdAuction}
              onClick={onClose}
            >
              Auction Room
            </a>
            <a
              href="#roster"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              data-testid={TESTIDS.navDdRoster}
              onClick={onClose}
            >
              My Roster
            </a>
            <a
              href="#fixtures"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              data-testid={TESTIDS.navDdFixtures}
              onClick={onClose}
            >
              Fixtures
            </a>
            <a
              href="#leaderboard"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              data-testid={TESTIDS.navDdLeaderboard}
              onClick={onClose}
            >
              Leaderboard
            </a>
            <a
              href="#settings"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              data-testid={TESTIDS.navDdSettings}
              onClick={onClose}
            >
              Settings
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDropdownMenu;