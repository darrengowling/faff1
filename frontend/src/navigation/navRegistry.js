/**
 * Navigation Registry
 * 
 * Single source of truth for all navigation items across the application
 * Generates menus dynamically with conditional visibility and enablement
 */

import { 
  Trophy, Users, Calendar, BarChart3, Settings, 
  Home, HelpCircle, Info, MessageSquare, ExternalLink,
  Plus, UserPlus, Mail, Shield
} from 'lucide-react';

// Type definitions (in JSDoc format for JavaScript)
/**
 * @typedef {Object} User
 * @property {string} id
 * @property {string} [display_name]
 * @property {string} [email]
 */

/**
 * @typedef {Object} League
 * @property {string} id
 * @property {string} name
 * @property {string} status
 * @property {string} [commissioner_id]
 * @property {number} [member_count]
 */

/**
 * @typedef {Object} AppState
 * @property {League|null} [selectedLeague]
 * @property {League[]} [leagues]
 * @property {boolean} isAuthenticated
 * @property {User|null} [user]
 */

/**
 * @typedef {Object} NavigationItem
 * @property {string} id
 * @property {string} label
 * @property {string} href
 * @property {any} [icon]
 * @property {string} [description]
 * @property {boolean} [external]
 * @property {function(User|null, AppState): boolean} enabled
 * @property {function(User|null, AppState): boolean} visible
 */

// Primary Navigation (main navbar items)
export const primaryNavigation = [
  {
    id: 'how-it-works',
    label: 'How it Works',
    href: '/#how',
    icon: HelpCircle,
    enabled: () => true,
    visible: () => true
  },
  {
    id: 'why-fop',
    label: 'Why FoP',
    href: '/#why', 
    icon: Info,
    enabled: () => true,
    visible: () => true
  },
  {
    id: 'faq',
    label: 'FAQ',
    href: '/#faq',
    icon: MessageSquare,
    enabled: () => true,
    visible: () => true
  }
];

// Product Dropdown Navigation (authenticated user features)
export const productDropdownNavigation = [
  {
    id: 'auction-room',
    label: 'Auction Room',
    href: '/auction',
    icon: Trophy,
    description: 'Join live bidding session',
    enabled: (user, appState) => {
      return !!(appState?.selectedLeague && appState?.isAuthenticated);
    },
    visible: (user, appState) => {
      return !!(appState?.isAuthenticated);
    }
  },
  {
    id: 'my-roster',
    label: 'My Roster', 
    href: '/clubs',
    icon: Users,
    description: 'View your clubs and budget',
    enabled: (user, appState) => {
      return !!(appState?.selectedLeague && appState?.isAuthenticated);
    },
    visible: (user, appState) => {
      return !!(appState?.isAuthenticated);
    }
  },
  {
    id: 'fixtures',
    label: 'Fixtures',
    href: '/fixtures',
    icon: Calendar,
    description: 'Match schedules and results',
    enabled: (user, appState) => {
      return !!(appState?.selectedLeague && appState?.isAuthenticated);
    },
    visible: (user, appState) => {
      return !!(appState?.isAuthenticated);
    }
  },
  {
    id: 'leaderboard',
    label: 'Leaderboard',
    href: '/leaderboard',
    icon: BarChart3,
    description: 'Rankings and statistics',
    enabled: (user, appState) => {
      return !!(appState?.selectedLeague && appState?.isAuthenticated);
    },
    visible: (user, appState) => {
      return !!(appState?.isAuthenticated);
    }
  },
  {
    id: 'league-admin',
    label: 'League Settings',
    href: '/admin',
    icon: Settings,
    description: 'Manage league configuration',
    enabled: (user, appState) => {
      const league = appState?.selectedLeague;
      return !!(
        league && 
        appState?.isAuthenticated && 
        user?.id === league.commissioner_id
      );
    },
    visible: (user, appState) => {
      return !!(appState?.isAuthenticated);
    }
  }
];

// Dashboard Quick Actions
export const dashboardActions = [
  {
    id: 'create-league',
    label: 'Create League',
    href: '/app',
    icon: Plus,
    description: 'Start a new football auction',
    enabled: (user, appState) => appState?.isAuthenticated || false,
    visible: (user, appState) => appState?.isAuthenticated || false
  },
  {
    id: 'join-league',
    label: 'Join League',
    href: '/app',
    icon: UserPlus,
    description: 'Enter with invitation code',
    enabled: (user, appState) => appState?.isAuthenticated || false,
    visible: (user, appState) => appState?.isAuthenticated || false
  }
];

// Footer Navigation
export const footerNavigation = [
  {
    id: 'terms',
    label: 'Terms of Service',
    href: '/terms',
    enabled: () => true,
    visible: () => true,
    external: true
  },
  {
    id: 'privacy',
    label: 'Privacy Policy', 
    href: '/privacy',
    enabled: () => true,
    visible: () => true,
    external: true
  },
  {
    id: 'contact',
    label: 'Contact Us',
    href: '/contact',
    enabled: () => true,
    visible: () => true,
    external: true
  },
  {
    id: 'about',
    label: 'About Us',
    href: '/about', 
    enabled: () => true,
    visible: () => true,
    external: true
  }
];

// Authentication Navigation (login/logout actions)
export const authNavigation = [
  {
    id: 'sign-in',
    label: 'Sign In',
    href: '/login',
    enabled: (user, appState) => !appState?.isAuthenticated,
    visible: (user, appState) => !appState?.isAuthenticated
  },
  {
    id: 'get-started',
    label: 'Get Started',
    href: '/login',
    enabled: (user, appState) => !appState?.isAuthenticated,
    visible: (user, appState) => !appState?.isAuthenticated
  },
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/app',
    icon: Home,
    enabled: (user, appState) => appState?.isAuthenticated || false,
    visible: (user, appState) => appState?.isAuthenticated || false
  }
];

// Utility functions for menu generation
export const getVisibleItems = (
  items: NavigationItem[],
  user?: User | null,
  appState?: AppState
): NavigationItem[] => {
  return items.filter(item => item.visible(user, appState));
};

export const getEnabledItems = (
  items: NavigationItem[],
  user?: User | null, 
  appState?: AppState
): NavigationItem[] => {
  return items.filter(item => 
    item.visible(user, appState) && item.enabled(user, appState)
  );
};

export const buildHref = (
  item: NavigationItem,
  appState?: AppState
): string => {
  const { href } = item;
  
  // Handle dynamic league-based URLs
  if (appState?.selectedLeague) {
    switch (item.id) {
      case 'auction-room':
        return `/auction/${appState.selectedLeague.id}`;
      case 'my-roster':
        return `/clubs/${appState.selectedLeague.id}`;
      case 'fixtures':
        return `/fixtures/${appState.selectedLeague.id}`;
      case 'leaderboard':
        return `/leaderboard/${appState.selectedLeague.id}`;
      case 'league-admin':
        return `/admin/${appState.selectedLeague.id}`;
      default:
        return href;
    }
  }
  
  return href;
};

// Menu configuration for different contexts
export const menuConfigs = {
  globalNavbar: {
    primary: primaryNavigation,
    productDropdown: productDropdownNavigation,
    auth: authNavigation
  },
  footer: {
    legal: footerNavigation
  },
  dashboard: {
    quickActions: dashboardActions
  }
} as const;

export default {
  primaryNavigation,
  productDropdownNavigation,
  dashboardActions,
  footerNavigation,
  authNavigation,
  getVisibleItems,
  getEnabledItems,
  buildHref,
  menuConfigs
};