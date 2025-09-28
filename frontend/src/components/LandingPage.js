/**
 * Friends of PIFA Landing Page
 * Responsive marketing page with hero, features, and CTAs
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getBrandName, getBrandTagline } from '../brand';
import useScrollSpy from '../hooks/useScrollSpy';
import { 
  Trophy, Users, Shield, Clock, Target, Star, 
  ChevronRight, Menu, X, Check, ArrowRight,
  Play, Zap, Award, Eye, Heart, MessageCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BrandBadge, HeaderBrand } from './ui/brand-badge';

const LandingPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Use scroll spy hook for deterministic section tracking
  const { activeSection } = useScrollSpy({ threshold: 0.5 });

  // Navigation sections
  const navSections = [
    { id: 'home', label: 'Home' },
    { id: 'how', label: 'How it Works' },
    { id: 'why', label: 'Why PIFA' },
    { id: 'features', label: 'Features' },
    { id: 'safety', label: 'Fair Play' },
    { id: 'faq', label: 'FAQ' },
  ];

  // Smooth scroll to section
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    setMobileMenuOpen(false);
  };

  // Navigation Header
  const NavigationHeader = () => (
    <header className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <HeaderBrand onClick={() => scrollToSection('home')} className="cursor-pointer" data-testid="landing-nav-brand" />
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navSections.slice(1).map((section) => (
              <button
                key={section.id}
                onClick={() => scrollToSection(section.id)}
                className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                  activeSection === section.id ? 'text-blue-600' : 'text-gray-700'
                }`}
              >
                {section.label}
              </button>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center space-x-4">
            <Button variant="ghost" onClick={() => navigate('/login')} className="text-sm">
              Sign In
            </Button>
            <Button onClick={() => navigate('/login')} className="text-sm">
              Get Started
            </Button>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t bg-white">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navSections.slice(1).map((section) => (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className={`block px-3 py-2 text-base font-medium rounded-md w-full text-left transition-colors ${
                    activeSection === section.id
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  {section.label}
                </button>
              ))}
              <div className="pt-4 space-y-2">
                <Button variant="ghost" onClick={() => navigate('/login')} className="w-full">
                  Sign In
                </Button>
                <Button onClick={() => navigate('/login')} className="w-full">
                  Get Started
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );

  // Hero Section
  const HeroSection = () => (
    <section id="home" className="anchor-section pt-16 bg-gradient-to-br from-blue-50 via-white to-indigo-50 min-h-screen flex items-center" data-testid="section-home">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
        <div className="text-center">
          {/* Brand Logo */}
          <div className="flex justify-center mb-8">
            <BrandBadge variant="full" size="lg" className="scale-125" />
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Football Auctions
            <span className="text-blue-600 block">with Friends</span>
          </h1>

          {/* Caption */}
          <p className="text-xl sm:text-2xl text-gray-600 mb-4 max-w-3xl mx-auto font-light">
            No bets. No chance. Just you, the game, and bragging rights.
          </p>

          {/* Subheadline */}
          <p className="text-lg text-gray-700 mb-10 max-w-2xl mx-auto">
            Create private football leagues, auction your dream teams, and compete for glory. 
            Strategy meets friendship in the ultimate fantasy experience.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              size="lg" 
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto text-lg px-8 py-4 shadow-lg hover:shadow-xl transition-all"
            >
              <Trophy className="w-5 h-5 mr-2" />
              Create a League
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto text-lg px-8 py-4"
            >
              <Users className="w-5 h-5 mr-2" />
              Join with an Invite
            </Button>
          </div>

          {/* Social proof placeholder */}
          <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
            <div className="flex items-center">
              <Star className="w-4 h-4 text-yellow-500 mr-1" />
              <span>Trusted by thousands</span>
            </div>
            <div className="flex items-center">
              <Shield className="w-4 h-4 text-green-500 mr-1" />
              <span>100% Fair Play</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );

  // How It Works Section
  const HowItWorksSection = () => {
    const steps = [
      {
        icon: Users,
        title: 'Create League',
        description: 'Invite 2-8 friends to your private league. Set your budget, club slots, and competition format.',
        color: 'bg-blue-100 text-blue-600'
      },
      {
        icon: Trophy,
        title: 'Live Auction',
        description: 'Bid on your favorite football clubs in real-time. Anti-snipe protection ensures fair competition.',
        color: 'bg-purple-100 text-purple-600'
      },
      {
        icon: Target,
        title: 'Score from Results',
        description: 'Earn points from real match results. Goals, wins, and draws translate to leaderboard success.',
        color: 'bg-green-100 text-green-600'
      }
    ];

    return (
      <section id="how" className="anchor-section py-20 bg-white" data-testid="section-how">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Three simple steps to start your football auction adventure
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="text-center">
                <div className={`w-16 h-16 ${step.color} rounded-full flex items-center justify-center mx-auto mb-6`}>
                  <step.icon className="w-8 h-8" />
                </div>
                <div className="text-sm font-semibold text-blue-600 mb-2">
                  Step {index + 1}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {step.title}
                </h3>
                <p className="text-gray-600">
                  {step.description}
                </p>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute right-0 top-8 transform translate-x-1/2">
                    <ArrowRight className="w-6 h-6 text-gray-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  };

  // Why Friends of PIFA Section
  const WhySection = () => {
    const benefits = [
      {
        icon: Shield,
        title: 'No Gambling, All Strategy',
        description: 'Pure skill-based competition with zero wagering. Your football knowledge and tactical decisions determine success.',
        color: 'text-green-600'
      },
      {
        icon: Users,
        title: 'The Social Arena',
        description: 'Where skill beats luck. Compete with friends in a fair environment built for strategy and friendly rivalry.',
        color: 'text-blue-600'
      },
      {
        icon: Heart,
        title: 'Built for Friends',
        description: 'Private leagues create the perfect space for banter, competition, and shared football passion.',
        color: 'text-red-600'
      }
    ];

    return (
      <section id="why" className="anchor-section py-20 bg-gray-50" data-testid="section-why">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Why Friends of PIFA
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Fair, social, and skill-based. The way football competition should be.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {benefits.map((benefit, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-8 text-center">
                  <benefit.icon className={`w-12 h-12 ${benefit.color} mx-auto mb-6`} />
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">
                    {benefit.title}
                  </h3>
                  <p className="text-gray-600">
                    {benefit.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    );
  };

  // Features Section
  const FeaturesSection = () => {
    const features = [
      {
        icon: Users,
        title: 'Private Leagues (2–8 Players)',
        description: 'Perfect size for friend groups with customizable league settings'
      },
      {
        icon: Target,
        title: 'Configurable Slots & Budgets',
        description: 'Tailor your league with flexible team sizes and spending limits'
      },
      {
        icon: Clock,
        title: 'Anti-Snipe Auction',
        description: 'Fair bidding with automatic timer extensions for last-second bids'
      },
      {
        icon: Zap,
        title: 'Real-Time Scoring',
        description: 'Live updates from actual match results and instant point calculations'
      },
      {
        icon: Award,
        title: 'Dynamic Leaderboards',
        description: 'Track performance across matchdays with detailed statistics'
      },
      {
        icon: MessageCircle,
        title: 'League Chat & Banter',
        description: 'Built-in communication for trash talk and strategy discussions'
      }
    ];

    return (
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need for the perfect football auction experience
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="flex items-start space-x-4 p-6 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <feature.icon className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  };

  // Safety & Fair Play Section
  const SafetySection = () => (
    <section id="safety" className="py-20 bg-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Fair Play & Transparency
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Built on principles of fairness and transparency. No hidden mechanics, just pure football strategy.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">No Wagering</h3>
                <p className="text-gray-600">Zero gambling. Play for pride, bragging rights, and the love of the game.</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Points from Performance</h3>
                <p className="text-gray-600">Your clubs earn points based on real match results. Goals, wins, and draws count.</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Clear Rules</h3>
                <p className="text-gray-600">Transparent scoring system and auction mechanics. Everyone knows how it works.</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Private & Secure</h3>
                <p className="text-gray-600">Your leagues are private to your group. No public rankings or external pressure.</p>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className="w-32 h-32 bg-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
              <Eye className="w-16 h-16 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Complete Transparency
            </h3>
            <p className="text-gray-600">
              Every bid, every point, every result is visible to all league members. 
              Fairness through complete openness.
            </p>
          </div>
        </div>
      </div>
    </section>
  );

  // FAQ Section
  const FAQSection = () => {
    const faqs = [
      {
        question: 'How does scoring work?',
        answer: 'Your clubs earn points based on real match results: +1 for each goal scored, +3 for wins, +1 for draws.'
      },
      {
        question: 'What happens if I miss the auction?',
        answer: 'Auctions are scheduled by your league commissioner. If you miss it, you can still join future auctions or trade with other managers.'
      },
      {
        question: 'Can I create multiple leagues?',
        answer: 'Yes! You can create and participate in multiple leagues with different friend groups.'
      },
      {
        question: 'Is there any cost to play?',
        answer: 'Friends of PIFA is free to play. No hidden fees, no premium features - just pure football fun.'
      },
      {
        question: 'How do invites work?',
        answer: 'League commissioners can send email invites to friends. Recipients just click the link to join the league.'
      },
      {
        question: 'What competitions are supported?',
        answer: 'We support major European competitions with plans to expand to more leagues and tournaments.'
      }
    ];

    return (
      <section id="faq" className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need to know about Friends of PIFA
            </p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <Card key={index} className="border border-gray-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg font-medium text-gray-900">
                    {faq.question}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-gray-600">
                    {faq.answer}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    );
  };

  // Final CTA Section
  const FinalCTASection = () => (
    <section id="cta" className="py-20 bg-gradient-to-r from-blue-600 to-blue-800 text-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold mb-4">
          Ready to Start Your League?
        </h2>
        <p className="text-xl mb-8 text-blue-100">
          Join thousands of football fans competing in the fairest, most fun auction platform.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button 
            size="lg" 
            variant="secondary"
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto text-lg px-8 py-4 bg-white text-blue-600 hover:bg-gray-100"
          >
            <Trophy className="w-5 h-5 mr-2" />
            Create Your League Now
          </Button>
          <Button 
            size="lg" 
            variant="ghost"
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto text-lg px-8 py-4 text-white border-white hover:bg-white hover:text-blue-600"
          >
            Sign Up Free
          </Button>
        </div>

        <p className="text-sm text-blue-200 mt-6">
          No credit card required • Free forever • Start in minutes
        </p>
      </div>
    </section>
  );

  // Sticky CTA (mobile)
  const StickyCTA = () => (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 md:hidden z-40">
      <Button 
        onClick={() => navigate('/login')} 
        className="w-full"
        size="lg"
      >
        <Trophy className="w-5 h-5 mr-2" />
        Get Started Free
      </Button>
    </div>
  );

  return (
    <div className="min-h-screen bg-white">
      <NavigationHeader />
      <HeroSection />
      <HowItWorksSection />
      <WhySection />
      <FeaturesSection />
      <SafetySection />
      <FAQSection />
      <FinalCTASection />
      <StickyCTA />
      
      {/* Bottom padding for sticky CTA on mobile */}
      <div className="h-20 md:hidden" />
    </div>
  );
};

export default LandingPage;