import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  MagnifyingGlassIcon,
  SparklesIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowRightIcon,
  PlayIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  EyeIcon,
  StarIcon,
  CogIcon,
  RocketLaunchIcon,
  CheckIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

const HomePage: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  const deviceRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
          }
        });
      },
      { threshold: 0.1 }
    );

    const elements = document.querySelectorAll('.animate-on-scroll');
    elements.forEach((el) => observer.observe(el));

    // Hero animation trigger
    setTimeout(() => setIsVisible(true), 500);

    return () => {
      elements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  // Mock company logos
  const companies = [
    'TechCorp', 'CreativeStudio', 'MediaFlow', 'ContentLab', 'VideoWorks', 
    'StreamTech', 'DigitalEdge', 'NextGen', 'CloudMedia', 'InnovateLab'
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Custom CSS Animations */}
      <style dangerouslySetInnerHTML={{
        __html: `
          .metaview-gradient {
            background: radial-gradient(ellipse at center, #00ffd0 0%, #00d4ff 35%, #0099ff 100%);
            background-size: 100% 100%;
            background-attachment: fixed;
          }
          
          .floating-ui {
            animation: float 3s ease-in-out infinite;
          }
          
          @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-8px) rotate(1deg); }
          }
          
          .logo-scroll {
            animation: scroll 20s linear infinite;
          }
          
          @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          
          .navbar-glass {
            backdrop-filter: blur(12px);
            background: rgba(255, 255, 255, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
          }
          
          .glass-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.1);
          }
          
          .glass-darker {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
          }
          
          .green-glow {
            box-shadow: 0 0 30px rgba(0, 255, 170, 0.3);
          }
        `
      }} />

      {/* Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 navbar-glass">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center mr-3">
                    <span className="text-white font-bold text-lg">YT</span>
                  </div>
                  <span className="text-xl font-bold text-black">YouTube Discovery</span>
                </div>
              </div>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <Link to="/search" className="flex items-center text-black hover:text-gray-700 transition-colors cursor-pointer">
                <span>Search</span>
              </Link>
              <Link to="/analytics" className="flex items-center text-black hover:text-gray-700 transition-colors cursor-pointer">
                <span>Analytics</span>
              </Link>
              <Link to="/trends" className="flex items-center text-black hover:text-gray-700 transition-colors cursor-pointer">
                <span>Trends</span>
              </Link>
              <span className="text-black hover:text-gray-700 transition-colors cursor-pointer">Pricing</span>
              <span className="text-black hover:text-gray-700 transition-colors cursor-pointer">About</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-blue-600 hover:text-blue-700 transition-colors cursor-pointer font-medium">Sign in</span>
              <button className="text-black border border-black border-opacity-30 px-4 py-2 rounded-lg hover:bg-black hover:bg-opacity-5 transition-colors font-medium">Book a demo</button>
              <Link 
                to="/search"
                className="bg-green-400 green-glow text-black px-4 py-2 rounded-lg hover:bg-green-300 transition-all duration-200 font-medium"
              >
                Start for free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="metaview-gradient relative overflow-hidden pt-16 min-h-screen">
        {/* Feature Announcement Banner */}
        <div className="flex justify-center pt-8 pb-8">
          <div className="glass-darker text-white px-6 py-3 rounded-full flex items-center space-x-3">
            <span className="bg-white text-black px-3 py-1 rounded-full text-xs font-bold">NEW FEATURE</span>
            <span className="text-sm font-medium">The most powerful YouTube content discovery just got an upgrade! Check out AI Search 2.0.</span>
            <span className="text-sm underline cursor-pointer hover:text-green-300 transition-colors">Learn more</span>
            <ArrowRightIcon className="w-4 h-4" />
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left Content */}
            <div className="text-left">
              <h1 className="text-6xl sm:text-7xl lg:text-8xl font-bold text-black mb-8 leading-tight">
                The{' '}
                <span className="italic" style={{ fontFamily: 'Georgia, serif' }}>#1</span>
                <span className="block">AI discovery</span>
                <span className="block">for creators</span>
              </h1>

              <p className="text-xl text-black mb-8 leading-relaxed max-w-lg">
                With YouTube Discovery's AI platform, every{' '}
                <span className="bg-green-400 text-black px-1 font-medium">search is analyzed</span>,{' '}
                <span className="bg-green-400 text-black px-1 font-medium">transcripts extracted</span>, and{' '}
                <span className="bg-green-400 text-black px-1 font-medium">results ranked</span>{' '}
                in{' '}
                <span className="bg-green-400 text-black px-1 font-medium">seconds</span>
                {' '}- helping content creators make faster, better discovery decisions.
              </p>

              <button className="bg-black text-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-gray-800 transition-all duration-200 shadow-lg">
                Try Discovery Now
              </button>
            </div>

            {/* Right Mockup */}
            <div className="relative">
              <div className="floating-ui">
                {/* Main Search Results Interface */}
                <div className="glass-card rounded-3xl p-6 transform rotate-2">
                  {/* Navigation Tabs */}
                  <div className="flex items-center space-x-6 mb-6 border-b border-white border-opacity-20 pb-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-sm font-medium text-gray-700">Search</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                      <span className="text-sm text-gray-600">Analytics</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                      <span className="text-sm text-gray-600">Trends</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                      <span className="text-sm text-gray-600">Transcripts</span>
                    </div>
                  </div>

                  {/* Search Results Content */}
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Video Results</h3>
                    
                    {/* Video Result Item */}
                    <div className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <div className="w-16 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
                          <PlayIcon className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900 mb-1">
                            How to Build AI Applications
                          </div>
                          <div className="text-xs text-gray-500 mb-2">
                            TechChannel • 1.2M views • 92% relevance
                          </div>
                          <div className="flex items-center space-x-3 text-xs text-gray-400">
                            <span className="text-green-600">✓ Transcript</span>
                            <span>✓ High quality</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Search Insights */}
                    <div className="border-t pt-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">Search Insights</div>
                      <div className="text-xs text-gray-500 space-y-1">
                        <div>— Found: 847 relevant videos</div>
                        <div>— Categories: Programming, AI/ML, Tutorials</div>
                        <div>— Avg. Quality Score: 8.4/10</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating Analytics Card */}
                <div className="absolute -top-6 -right-6 glass-card rounded-2xl p-4 w-64">
                  <div className="text-sm font-semibold text-gray-900 mb-3">Analytics</div>
                  <div className="text-xs text-gray-600 mb-3">Search performance metrics</div>
                  
                  {/* Chart Mockup */}
                  <div className="h-20 bg-gray-50 bg-opacity-50 rounded-lg flex items-end justify-center space-x-1 p-3">
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className="bg-blue-400 rounded-t" style={{ height: `${30 + Math.random() * 40}%`, width: '6px' }}></div>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                    <span className="flex items-center">
                      <span className="w-3 h-3 bg-blue-400 rounded mr-1"></span>
                      1.2K
                    </span>
                    <span className="flex items-center">
                      <span className="w-3 h-3 bg-green-400 rounded mr-1"></span>
                      89%
                    </span>
                  </div>
                </div>

                {/* AI Assistant Card */}
                <div className="absolute -bottom-6 -left-6 glass-card rounded-2xl p-4 w-72">
                  <div className="text-sm font-semibold text-gray-900 mb-3">AI Assistant</div>
                  <div className="text-xs text-gray-600 mb-3">
                    What are the trending topics in AI content this week?
                  </div>
                  <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-green-400 rounded-full" style={{ width: '60%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Company Logos Section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-gray-600 text-lg">
              Loved by content creators, marketers & researchers at{' '}
              <span className="font-semibold text-gray-900">500+</span> organizations
            </p>
          </div>
          
          {/* Scrolling Logos */}
          <div className="overflow-hidden">
            <div className="flex items-center space-x-12 logo-scroll">
              {[...companies, ...companies].map((company, index) => (
                <div key={index} className="flex-shrink-0">
                  <div className="text-gray-400 font-semibold text-lg tracking-wide">
                    {company}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid - Metaview Style */}
      <div className="py-20 bg-gradient-to-br from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 animate-on-scroll">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              Everything you need for
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-green-600">
                intelligent content discovery
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our comprehensive platform combines AI-powered search, advanced analytics, and seamless workflow integration to transform how you discover and analyze YouTube content.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: MagnifyingGlassIcon,
                title: 'AI-Powered Search',
                description: 'Natural language queries that understand context and intent, delivering precisely relevant results every time.',
                color: 'cyan',
                features: ['Semantic understanding', 'Context-aware results', 'Smart filtering']
              },
              {
                icon: DocumentTextIcon,
                title: 'Complete Transcript Access',
                description: 'Full video transcription with advanced search, export capabilities, and content analysis tools.',
                color: 'green', 
                features: ['Full text extraction', 'Multi-format export', 'Content insights']
              },
              {
                icon: ChartBarIcon,
                title: 'Advanced Analytics',
                description: 'Comprehensive metrics and insights to help you understand content performance and trends.',
                color: 'blue',
                features: ['Performance tracking', 'Trend analysis', 'Quality scoring']
              },
              {
                icon: BoltIcon,
                title: 'Lightning Fast Results',
                description: 'Optimized algorithms and intelligent caching deliver results in under 2 seconds.',
                color: 'yellow',
                features: ['Sub-2s response time', 'Smart caching', 'Real-time updates']
              },
              {
                icon: ArrowTrendingUpIcon,
                title: 'Trend Discovery',
                description: 'Identify emerging topics and trending content opportunities in your industry.',
                color: 'purple',
                features: ['Trend identification', 'Market analysis', 'Opportunity mapping']
              },
              {
                icon: RocketLaunchIcon,
                title: 'Seamless Integration',
                description: 'Easy-to-use APIs and export tools that integrate with your existing workflow.',
                color: 'indigo',
                features: ['API access', 'Bulk operations', 'Workflow automation']
              }
            ].map((feature, index) => {
              const Icon = feature.icon;
              const colorClasses = {
                cyan: 'from-cyan-500 to-cyan-600 text-cyan-600 bg-cyan-50',
                green: 'from-green-500 to-green-600 text-green-600 bg-green-50',
                blue: 'from-blue-500 to-blue-600 text-blue-600 bg-blue-50',
                yellow: 'from-yellow-500 to-yellow-600 text-yellow-600 bg-yellow-50',
                purple: 'from-purple-500 to-purple-600 text-purple-600 bg-purple-50',
                indigo: 'from-indigo-500 to-indigo-600 text-indigo-600 bg-indigo-50'
              };
              const colors = colorClasses[feature.color as keyof typeof colorClasses];
              
              return (
                <div key={index} className="animate-on-scroll group" style={{animationDelay: `${index * 0.1}s`}}>
                  <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-1 border border-gray-100 h-full">
                    <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl mb-6 bg-gradient-to-r ${colors.split(' ')[0]} ${colors.split(' ')[1]} group-hover:scale-110 transition-all duration-300 shadow-lg`}>
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                    
                    <h3 className="text-xl font-bold text-gray-900 mb-4 group-hover:text-cyan-600 transition-colors">
                      {feature.title}
                    </h3>
                    
                    <p className="text-gray-600 leading-relaxed mb-6">
                      {feature.description}
                    </p>
                    
                    <ul className="space-y-2">
                      {feature.features.map((item, idx) => (
                        <li key={idx} className="flex items-center text-sm text-gray-500">
                          <CheckIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
          
          <div className="text-center mt-16 animate-on-scroll">
            <Link
              to="/search"
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-cyan-600 to-green-600 hover:from-cyan-700 hover:to-green-700 text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 shadow-xl"
            >
              <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
              Start Discovering Now
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </div>

      {/* Final CTA Section - Metaview Style */}
      <div className="metaview-gradient py-20 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-full h-full opacity-20">
            <div className="absolute top-10 left-10 w-32 h-32 border border-white rounded-full floating-ui"></div>
            <div className="absolute top-20 right-20 w-24 h-24 border border-white rounded-full floating-ui" style={{animationDelay: '2s'}}></div>
            <div className="absolute bottom-20 left-32 w-40 h-40 border border-white rounded-full floating-ui" style={{animationDelay: '4s'}}></div>
            <div className="absolute bottom-10 right-10 w-20 h-20 border border-white rounded-full floating-ui" style={{animationDelay: '1s'}}></div>
          </div>
        </div>
        
        <div className="relative max-w-5xl mx-auto text-center px-6 lg:px-8">
          <div className="animate-on-scroll">
            <h2 className="text-4xl sm:text-6xl font-bold text-black mb-6">
              Ready to unlock the power of
              <span className="block font-serif italic">#1 AI discovery?</span>
            </h2>
            <p className="text-xl sm:text-2xl text-black mb-12 leading-relaxed">
              Join thousands of creators, researchers, and marketers who trust our platform for intelligent YouTube content discovery.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Link
                to="/search"
                className="group inline-flex items-center px-10 py-5 bg-black hover:bg-gray-800 text-white font-bold rounded-full transition-all duration-300 transform hover:scale-105 shadow-2xl text-lg"
              >
                <MagnifyingGlassIcon className="w-6 h-6 mr-3 group-hover:rotate-12 transition-transform" />
                Start Discovering
                <ArrowRightIcon className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform" />
              </Link>
              
              <button className="inline-flex items-center px-10 py-5 bg-transparent hover:bg-black hover:bg-opacity-10 text-black font-bold rounded-full border-2 border-black border-opacity-30 transition-all duration-300 backdrop-blur-sm text-lg">
                <PlayIcon className="w-6 h-6 mr-3" />
                View Demo
              </button>
            </div>
            
            {/* Trust indicators */}
            <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
              <div className="text-black text-opacity-80">
                <div className="text-3xl font-bold text-black mb-2">99.9%</div>
                <div className="text-sm">Uptime Reliability</div>
              </div>
              <div className="text-black text-opacity-80">
                <div className="text-3xl font-bold text-black mb-2">10k+</div>
                <div className="text-sm">Happy Users</div>
              </div>
              <div className="text-black text-opacity-80">
                <div className="text-3xl font-bold text-black mb-2">24/7</div>
                <div className="text-sm">Support Available</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;