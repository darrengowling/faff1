import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Trophy, 
  Users, 
  Crown, 
  Mail, 
  User, 
  Settings, 
  LogOut,
  Plus,
  Timer,
  DollarSign,
  Gavel,
  Target,
  Send,
  UserPlus,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw,
  Eye,
  Shield,
  Calendar,
  MapPin,
  Play,
  Copy,
  ArrowRight,
  Star,
  Zap,
  Heart,
  Globe,
  Lock,
  HelpCircle
} from 'lucide-react';
import { TESTIDS } from '../testids';
import { getBrandName } from '../brand';
import MarketingShell from './layouts/MarketingShell';
import { TestableSection, TestableButton } from './testable/TestableComponents.tsx';

const SimpleLandingPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <MarketingShell>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Hero Section */}
        <TestableSection 
          id="home" 
          className="relative py-20 px-4 sm:px-6 lg:px-8 anchor-section"
          data-testid={TESTIDS.sectionHome}
        >
          <div className="max-w-4xl mx-auto text-center">
            <div className="mb-8">
              <Badge variant="outline" className="mb-4 px-4 py-2 text-sm font-medium bg-white/80 backdrop-blur-sm">
                ⚽ Fantasy Football Auctions
              </Badge>
              <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
                {t('landing.heroTitle', { brandName: getBrandName() })}
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                {t('landing.heroSubtitle')}
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <TestableButton
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                onClick={() => navigate('/login')}
                data-testid={TESTIDS.landingCtaCreate}
              >
                <Trophy className="w-5 h-5 mr-2" />
                Create a League
              </TestableButton>
              
              <TestableButton
                size="lg"
                variant="outline"
                className="bg-white/80 backdrop-blur-sm border-2 border-blue-200 hover:border-blue-300 px-8 py-4 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                onClick={() => navigate('/login')}
                data-testid={TESTIDS.landingCtaJoin}
              >
                <Users className="w-5 h-5 mr-2" />
                Join with an Invite
              </TestableButton>
            </div>
          </div>
        </TestableSection>

        {/* How It Works Section */}
        <TestableSection 
          id="how" 
          className="py-20 px-4 sm:px-6 lg:px-8 bg-white anchor-section"
          data-testid={TESTIDS.sectionHow}
        >
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {t('landing.howItWorksTitle')}
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                {t('landing.howItWorksSubtitle')}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="text-center p-6 shadow-lg hover:shadow-xl transition-shadow duration-200">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trophy className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{t('landing.step1Title')}</h3>
                  <p className="text-gray-600">{t('landing.step1Description')}</p>
                </CardContent>
              </Card>
              
              <Card className="text-center p-6 shadow-lg hover:shadow-xl transition-shadow duration-200">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Gavel className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{t('landing.step2Title')}</h3>
                  <p className="text-gray-600">{t('landing.step2Description')}</p>
                </CardContent>
              </Card>
              
              <Card className="text-center p-6 shadow-lg hover:shadow-xl transition-shadow duration-200">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Crown className="w-8 h-8 text-purple-600" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{t('landing.step3Title')}</h3>
                  <p className="text-gray-600">{t('landing.step3Description')}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TestableSection>

        {/* Why Choose Us Section */}
        <TestableSection 
          id="why" 
          className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 anchor-section"
          data-testid={TESTIDS.sectionWhy}
        >
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {t('landing.whyChooseTitle')}
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                {t('landing.whyChooseSubtitle')}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature1Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature1Description')}</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature2Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature2Description')}</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Globe className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature3Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature3Description')}</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Timer className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature4Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature4Description')}</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Heart className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature5Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature5Description')}</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Star className="w-6 h-6 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">{t('landing.feature6Title')}</h3>
                  <p className="text-gray-600">{t('landing.feature6Description')}</p>
                </div>
              </div>
            </div>
          </div>
        </TestableSection>

        {/* Features Section */}
        <TestableSection 
          id="features" 
          className="py-20 px-4 sm:px-6 lg:px-8 bg-white anchor-section"
          data-testid={TESTIDS.sectionFeatures}
        >
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {t('landing.featuresTitle')}
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                {t('landing.featuresSubtitle')}
              </p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Gavel className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2">{t('landing.auctionTitle')}</h3>
                    <p className="text-gray-600">{t('landing.auctionDescription')}</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Trophy className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2">{t('landing.leaderboardTitle')}</h3>
                    <p className="text-gray-600">{t('landing.leaderboardDescription')}</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Calendar className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2">{t('landing.fixturesTitle')}</h3>
                    <p className="text-gray-600">{t('landing.fixturesDescription')}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-8 text-white">
                <div className="text-center">
                  <Trophy className="w-16 h-16 mx-auto mb-4 opacity-80" />
                  <h3 className="text-2xl font-bold mb-4">{t('landing.readyToStart')}</h3>
                  <p className="text-blue-100 mb-6">{t('landing.readyToStartDescription')}</p>
                  <TestableButton
                    size="lg"
                    className="bg-white text-blue-600 hover:bg-gray-100 font-semibold px-8 py-3"
                    onClick={() => navigate('/login')}
                  >
                    {t('landing.getStarted')}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </TestableButton>
                </div>
              </div>
            </div>
          </div>
        </TestableSection>

        {/* Safety & Fair Play Section */}
        <TestableSection 
          id="safety" 
          className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 anchor-section"
          data-testid={TESTIDS.sectionSafety}
        >
          <div className="max-w-4xl mx-auto text-center">
            <div className="mb-12">
              <Shield className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {t('landing.safetyTitle')}
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                {t('landing.safetySubtitle')}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card className="p-6 shadow-lg">
                <CardContent className="pt-6">
                  <Lock className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-3">{t('landing.secureTitle')}</h3>
                  <p className="text-gray-600">{t('landing.secureDescription')}</p>
                </CardContent>
              </Card>
              
              <Card className="p-6 shadow-lg">
                <CardContent className="pt-6">
                  <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-3">{t('landing.fairTitle')}</h3>
                  <p className="text-gray-600">{t('landing.fairDescription')}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TestableSection>

        {/* FAQ Section */}
        <TestableSection 
          id="faq" 
          className="py-20 px-4 sm:px-6 lg:px-8 bg-white anchor-section"
          data-testid={TESTIDS.sectionFaq}
        >
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <HelpCircle className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {t('landing.faqTitle')}
              </h2>
              <p className="text-xl text-gray-600">
                {t('landing.faqSubtitle')}
              </p>
            </div>
            
            <div className="space-y-6">
              <Card className="p-6 shadow-lg">
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-3">{t('landing.faq1Question')}</h3>
                  <p className="text-gray-600">{t('landing.faq1Answer')}</p>
                </CardContent>
              </Card>
              
              <Card className="p-6 shadow-lg">
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-3">{t('landing.faq2Question')}</h3>
                  <p className="text-gray-600">{t('landing.faq2Answer')}</p>
                </CardContent>
              </Card>
              
              <Card className="p-6 shadow-lg">
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-3">{t('landing.faq3Question')}</h3>
                  <p className="text-gray-600">{t('landing.faq3Answer')}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TestableSection>

        {/* Final CTA Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-purple-600">
          <div className="max-w-4xl mx-auto text-center text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              {t('landing.finalCtaTitle')}
            </h2>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              {t('landing.finalCtaSubtitle')}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <TestableButton
                size="lg"
                className="bg-white text-blue-600 hover:bg-gray-100 font-semibold px-8 py-4 text-lg shadow-lg hover:shadow-xl transition-all duration-200"
                onClick={() => navigate('/login')}
              >
                <Trophy className="w-5 h-5 mr-2" />
                {t('landing.startYourLeague')}
              </TestableButton>
              
              <TestableButton
                size="lg"
                variant="outline"
                className="border-2 border-white text-white hover:bg-white hover:text-blue-600 font-semibold px-8 py-4 text-lg shadow-lg hover:shadow-xl transition-all duration-200"
                onClick={() => navigate('/login')}
              >
                <Users className="w-5 h-5 mr-2" />
                {t('landing.joinLeague')}
              </TestableButton>
            </div>
          </div>
        </section>
      </div>
    </MarketingShell>
  );
};

export default SimpleLandingPage;