/**
 * Simple Landing Page for Testing
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Trophy, Users, Shield, Clock, Target, Star, 
  Menu, X, Check, ArrowRight, Zap, Award, Eye, Heart, MessageCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BrandBadge } from './ui/brand-badge';

const SimpleLandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <BrandBadge variant="full" size="md" />
            
            {/* Desktop CTAs */}
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => navigate('/login')} className="text-sm">
                Sign In
              </Button>
              <Button onClick={() => navigate('/login')} className="text-sm">
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section id="home" className="pt-16 bg-gradient-to-br from-blue-50 via-white to-indigo-50 min-h-screen flex items-center">
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
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how" className="py-20 bg-white">
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
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Users className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">Step 1</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Create League</h3>
              <p className="text-gray-600">
                Invite 2-8 friends to your private league. Set your budget, club slots, and competition format.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Trophy className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">Step 2</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Live Auction</h3>
              <p className="text-gray-600">
                Bid on your favorite football clubs in real-time. Anti-snipe protection ensures fair competition.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Trophy className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">Step 3</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Score from Results</h3>
              <p className="text-gray-600">
                Earn points from real match results. Goals, wins, and draws translate to leaderboard success.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
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
          </div>
        </div>
      </section>
    </div>
  );
};

export default SimpleLandingPage;