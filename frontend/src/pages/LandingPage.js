import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-800">Odoo SaaS Platform</h1>
          </div>
          <div className="flex space-x-4">
            <Link to="/login" className="btn btn-secondary">Login</Link>
            <Link to="/register" className="btn btn-primary">Get Started</Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-5xl font-bold text-gray-800 mb-6">
          Enterprise Odoo Hosting
          <span className="text-blue-600"> Made Simple</span>
        </h2>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Launch your Odoo instance in minutes with our fully managed SaaS platform. 
          Scale effortlessly, secure by default, and backed by enterprise-grade infrastructure.
        </p>
        <div className="flex justify-center space-x-4">
          <Link to="/register" className="btn btn-primary text-lg px-8 py-4">
            Start Free Trial
          </Link>
          <Link to="/demo" className="btn btn-secondary text-lg px-8 py-4">
            View Demo
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center text-gray-800 mb-12">
            Why Choose Our Platform?
          </h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card text-center">
              <div className="text-blue-600 text-4xl mb-4">🚀</div>
              <h4 className="text-xl font-semibold mb-4">Quick Deployment</h4>
              <p className="text-gray-600">
                Deploy your Odoo instance in under 5 minutes with our one-click setup.
              </p>
            </div>
            <div className="card text-center">
              <div className="text-blue-600 text-4xl mb-4">🔒</div>
              <h4 className="text-xl font-semibold mb-4">Enterprise Security</h4>
              <p className="text-gray-600">
                Bank-grade security with SSL, backups, and compliance monitoring.
              </p>
            </div>
            <div className="card text-center">
              <div className="text-blue-600 text-4xl mb-4">📈</div>
              <h4 className="text-xl font-semibold mb-4">Auto Scaling</h4>
              <p className="text-gray-600">
                Automatically scale resources based on your business needs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center text-gray-800 mb-12">
            Simple, Transparent Pricing
          </h3>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="card text-center">
              <h4 className="text-xl font-semibold mb-4">Starter</h4>
              <div className="text-3xl font-bold text-blue-600 mb-4">$29/mo</div>
              <ul className="text-left space-y-2 mb-6">
                <li>✓ 1 Odoo Instance</li>
                <li>✓ 5 Users</li>
                <li>✓ 10GB Storage</li>
                <li>✓ Email Support</li>
              </ul>
              <Link to="/register?plan=starter" className="btn btn-primary w-full">
                Get Started
              </Link>
            </div>
            <div className="card text-center border-2 border-blue-500">
              <div className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm mb-4">
                Most Popular
              </div>
              <h4 className="text-xl font-semibold mb-4">Professional</h4>
              <div className="text-3xl font-bold text-blue-600 mb-4">$99/mo</div>
              <ul className="text-left space-y-2 mb-6">
                <li>✓ 5 Odoo Instances</li>
                <li>✓ 25 Users</li>
                <li>✓ 100GB Storage</li>
                <li>✓ Priority Support</li>
                <li>✓ Custom Domains</li>
              </ul>
              <Link to="/register?plan=professional" className="btn btn-primary w-full">
                Get Started
              </Link>
            </div>
            <div className="card text-center">
              <h4 className="text-xl font-semibold mb-4">Enterprise</h4>
              <div className="text-3xl font-bold text-blue-600 mb-4">$299/mo</div>
              <ul className="text-left space-y-2 mb-6">
                <li>✓ Unlimited Instances</li>
                <li>✓ Unlimited Users</li>
                <li>✓ 1TB Storage</li>
                <li>✓ 24/7 Phone Support</li>
                <li>✓ Custom Integrations</li>
              </ul>
              <Link to="/register?plan=enterprise" className="btn btn-primary w-full">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h5 className="text-lg font-semibold mb-4">Odoo SaaS Platform</h5>
              <p className="text-gray-400">
                The most reliable way to host and manage your Odoo instances.
              </p>
            </div>
            <div>
              <h5 className="text-lg font-semibold mb-4">Product</h5>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h5 className="text-lg font-semibold mb-4">Support</h5>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Contact Us</a></li>
                <li><a href="#" className="hover:text-white">Status Page</a></li>
              </ul>
            </div>
            <div>
              <h5 className="text-lg font-semibold mb-4">Company</h5>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Odoo SaaS Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

