'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Brain,
  MessageSquare,
  FileText,
  BarChart3,
  Shield,
  Zap,
  Users,
  ArrowRight,
  CheckCircle,
  Sparkles,
  Target,
  Layers
} from 'lucide-react'

export default function LandingPage() {
  const router = useRouter()

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Intelligence',
      description: 'Advanced multi-agent system with RAG capabilities for intelligent document analysis and question answering.',
      color: 'text-blue-500',
    },
    {
      icon: MessageSquare,
      title: 'Interactive Chat',
      description: 'Natural conversations with AI that understands context and provides accurate, grounded responses.',
      color: 'text-green-500',
    },
    {
      icon: FileText,
      title: 'Document Management',
      description: 'Upload and organize PDFs, text files, and documents into a searchable knowledge base.',
      color: 'text-purple-500',
    },
    {
      icon: BarChart3,
      title: 'Explainable AI',
      description: 'Understand how AI makes decisions with confidence scores, reasoning chains, and source attribution.',
      color: 'text-orange-500',
    },
    {
      icon: Shield,
      title: 'Role-Based Access',
      description: 'Enterprise-grade security with granular permissions and user role management.',
      color: 'text-red-500',
    },
    {
      icon: Zap,
      title: 'Dual LLM Support',
      description: 'Choose between custom API endpoints or local Ollama models for flexibility and control.',
      color: 'text-yellow-500',
    },
  ]

  const useCases = [
    {
      icon: Target,
      title: 'Research & Analysis',
      description: 'Quickly analyze large document collections and extract insights with AI assistance.',
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description: 'Share knowledge across teams with organized document repositories and chat history.',
    },
    {
      icon: Layers,
      title: 'Enterprise Integration',
      description: 'Integrate with existing workflows using flexible API endpoints and authentication.',
    },
  ]

  const benefits = [
    'Real-time document processing and embedding',
    'Multi-agent orchestration for complex queries',
    'Source attribution and grounding evidence',
    'Confidence scoring for AI responses',
    'Customizable explainability levels',
    'Admin dashboard for user management',
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              AI RAG Platform
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => router.push('/auth/login')}>
              Login
            </Button>
            <Button onClick={() => router.push('/auth/register')}>
              Get Started
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container mx-auto text-center">
          <Badge className="mb-4 px-4 py-1 text-sm" variant="outline">
            <Sparkles className="h-3 w-3 mr-1 inline" />
            Next Generation AI Platform
          </Badge>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Transform Documents into
            <br />
            Intelligent Conversations
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Harness the power of Retrieval-Augmented Generation and multi-agent systems to unlock insights
            from your documents with explainable AI you can trust.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="text-lg px-8" onClick={() => router.push('/auth/register')}>
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8" onClick={() => router.push('/auth/login')}>
              View Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 bg-white">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to build intelligent, document-powered AI applications
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <feature.icon className={`h-6 w-6 ${feature.color}`} />
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Built for Every Use Case</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              From research teams to enterprise deployments, our platform scales with your needs
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {useCases.map((useCase, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="mx-auto mb-4 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-full w-16 h-16 flex items-center justify-center">
                    <useCase.icon className="h-8 w-8 text-blue-600" />
                  </div>
                  <CardTitle className="text-2xl mb-2">{useCase.title}</CardTitle>
                  <CardDescription className="text-base">
                    {useCase.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4 bg-white">
        <div className="container mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold mb-6">Why Choose Our Platform?</h2>
              <p className="text-xl text-gray-600 mb-8">
                Built with the latest AI technologies and best practices, our platform delivers
                reliable, explainable results you can depend on.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-lg text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <Card className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                <CardHeader>
                  <CardTitle className="text-3xl text-white">Ready to Get Started?</CardTitle>
                  <CardDescription className="text-blue-100 text-lg">
                    Join teams already using our platform to transform their document workflows
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="bg-white/20 p-3 rounded-lg">
                      <Users className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">10,000+</p>
                      <p className="text-blue-100">Active Users</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="bg-white/20 p-3 rounded-lg">
                      <FileText className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">1M+</p>
                      <p className="text-blue-100">Documents Processed</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="bg-white/20 p-3 rounded-lg">
                      <MessageSquare className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">5M+</p>
                      <p className="text-blue-100">Queries Answered</p>
                    </div>
                  </div>
                  <Button
                    size="lg"
                    className="w-full bg-white text-blue-600 hover:bg-gray-100"
                    onClick={() => router.push('/auth/register')}
                  >
                    Create Free Account
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="container mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">
            Ready to Transform Your Documents?
          </h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto text-blue-100">
            Start your journey with intelligent document processing today.
            No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              className="bg-white text-blue-600 hover:bg-gray-100 text-lg px-8"
              onClick={() => router.push('/auth/register')}
            >
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white text-white hover:bg-white/10 text-lg px-8"
              onClick={() => router.push('/auth/login')}
            >
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-gray-900 text-gray-300">
        <div className="container mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Brain className="h-6 w-6 text-blue-400" />
                <span className="text-xl font-bold text-white">AI RAG Platform</span>
              </div>
              <p className="text-sm text-gray-400">
                Next-generation AI platform for intelligent document processing and analysis.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">Product</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">Features</a></li>
                <li><a href="#" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">Company</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">About Us</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Careers</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">Legal</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white transition">Security</a></li>
                <li><a href="#" className="hover:text-white transition">Compliance</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
            <p>&copy; {new Date().getFullYear()} AI RAG Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
