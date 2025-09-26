/**
 * Simple Landing Page for Testing
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Trophy, Users, Shield, Clock, Target, Star, 
  Check, ArrowRight, Zap, Award, Eye, Heart, MessageCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BrandBadge } from './ui/brand-badge';
import { LandingFooter } from './ui/footer';

const SimpleLandingPage = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-theme-surface">
      {/* Hero Section */}
      <section id="home" className="pt-16 bg-gradient-to-br from-blue-50 via-theme-surface to-indigo-50 min-h-screen flex items-center">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="text-center">
            {/* Brand Logo */}
            <div className="flex justify-center mb-8">
              <BrandBadge variant="full" size="lg" className="scale-125" />
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-theme-text mb-6 leading-tight">
              {t('branding.heroTitle')}
              <span className="text-blue-600 block">{t('branding.heroTitleAccent')}</span>
            </h1>

            {/* Caption */}
            <p className="text-xl sm:text-2xl text-theme-text-secondary mb-4 max-w-3xl mx-auto font-light">
              {t('branding.heroCaption')}
            </p>

            {/* Subheadline */}
            <p className="text-lg text-gray-700 mb-10 max-w-2xl mx-auto">
              {t('branding.heroSubheading')}
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Button 
                size="lg" 
                onClick={() => navigate('/login')}
                className="w-full sm:w-auto text-lg px-8 py-4 shadow-lg hover:shadow-xl transition-all"
              >
                <Trophy className="w-5 h-5 mr-2" />
                {t('branding.ctaButtons.createLeague')}
              </Button>
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => navigate('/login')}
                className="w-full sm:w-auto text-lg px-8 py-4"
              >
                <Users className="w-5 h-5 mr-2" />
                {t('branding.ctaButtons.joinInvite')}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how" className="py-20 bg-theme-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.howItWorks.title')}
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              {t('landing.howItWorks.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Users className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">{t('landing.howItWorks.steps.create.step')}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">{t('landing.howItWorks.steps.create.title')}</h3>
              <p className="text-gray-600">
                {t('landing.howItWorks.steps.create.description')}
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Trophy className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">{t('landing.howItWorks.steps.auction.step')}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">{t('landing.howItWorks.steps.auction.title')}</h3>
              <p className="text-gray-600">
                {t('landing.howItWorks.steps.auction.description')}
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Trophy className="w-8 h-8" />
              </div>
              <div className="text-sm font-semibold text-blue-600 mb-2">{t('landing.howItWorks.steps.score.step')}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">{t('landing.howItWorks.steps.score.title')}</h3>
              <p className="text-gray-600">
                {t('landing.howItWorks.steps.score.description')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why Friends of PIFA Section */}
      <section id="why" className="py-20 bg-theme-surface-secondary">
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
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-8 text-center">
                <Shield className="w-12 h-12 text-green-600 mx-auto mb-6" />
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  No Gambling, All Strategy
                </h3>
                <p className="text-gray-600">
                  Pure skill-based competition with zero wagering. Your football knowledge and tactical decisions determine success.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 text-blue-600 mx-auto mb-6" />
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  The Social Arena
                </h3>
                <p className="text-gray-600">
                  Where skill beats luck. Compete with friends in a fair environment built for strategy and friendly rivalry.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-8 text-center">
                <Heart className="w-12 h-12 text-red-600 mx-auto mb-6" />
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Built for Friends
                </h3>
                <p className="text-gray-600">
                  Private leagues create the perfect space for banter, competition, and shared football passion.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.features.title')}
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              {t('landing.features.subtitle')}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Users,
                title: t('landing.features.items.privateLeagues.title'),
                description: t('landing.features.items.privateLeagues.description')
              },
              {
                icon: Target,
                title: t('landing.features.items.configurable.title'),
                description: t('landing.features.items.configurable.description')
              },
              {
                icon: Clock,
                title: t('landing.features.items.antiSnipe.title'),
                description: t('landing.features.items.antiSnipe.description')
              },
              {
                icon: Zap,
                title: t('landing.features.items.realTimeScoring.title'),
                description: t('landing.features.items.realTimeScoring.description')
              },
              {
                icon: Award,
                title: t('landing.features.items.leaderboards.title'),
                description: t('landing.features.items.leaderboards.description')
              },
              {
                icon: MessageCircle,
                title: t('landing.features.items.communication.title'),
                description: t('landing.features.items.communication.description')
              }
            ].map((feature, index) => (
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

      {/* Safety & Fair Play Section */}
      <section id="safety" className="py-20 bg-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {t('landing.fairPlay.title')}
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('landing.fairPlay.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              {[
                {
                  title: t('landing.fairPlay.items.noWagering.title'),
                  description: t('landing.fairPlay.items.noWagering.description')
                },
                {
                  title: t('landing.fairPlay.items.performance.title'),
                  description: t('landing.fairPlay.items.performance.description')
                },
                {
                  title: t('landing.fairPlay.items.transparent.title'),
                  description: t('landing.fairPlay.items.transparent.description')
                },
                {
                  title: t('landing.fairPlay.items.private.title'),
                  description: t('landing.fairPlay.items.private.description')
                }
              ].map((item, index) => (
                <div key={index} className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <Check className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                    <p className="text-gray-600">{item.description}</p>
                  </div>
                </div>
              ))}
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

      {/* FAQ Section */}
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
            {[
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
            ].map((faq, index) => (
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

      {/* Sticky CTA (mobile) */}
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
      
      {/* Bottom padding for sticky CTA on mobile */}
      <div className="h-20 md:hidden" />

      {/* Footer */}
      <LandingFooter />
    </div>
  );
};

export default SimpleLandingPage;