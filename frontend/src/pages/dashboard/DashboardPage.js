import React from 'react';

const DashboardPage = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome to your Odoo SaaS Platform dashboard</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">3</h3>
              <p className="text-sm text-gray-600">Active Instances</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">24</h3>
              <p className="text-sm text-gray-600">Total Users</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">156 GB</h3>
              <p className="text-sm text-gray-600">Storage Used</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">$299</h3>
              <p className="text-sm text-gray-600">Monthly Cost</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Instances</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <h4 className="font-medium">Production Instance</h4>
                <p className="text-sm text-gray-600">prod.example.com</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                Running
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <h4 className="font-medium">Staging Instance</h4>
                <p className="text-sm text-gray-600">staging.example.com</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                Updating
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <h4 className="font-medium">Development Instance</h4>
                <p className="text-sm text-gray-600">dev.example.com</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                Stopped
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn btn-primary text-sm">
              Create Instance
            </button>
            <button className="btn btn-secondary text-sm">
              View Billing
            </button>
            <button className="btn btn-secondary text-sm">
              Manage Users
            </button>
            <button className="btn btn-secondary text-sm">
              Support
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

