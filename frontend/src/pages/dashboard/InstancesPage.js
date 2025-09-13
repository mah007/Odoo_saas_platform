import React from 'react';

const InstancesPage = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Instances</h1>
        <p className="text-gray-600">Manage your Odoo instances</p>
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Your Instances</h2>
          <button className="btn btn-primary">
            Create Instance
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Instance Card 1 */}
          <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Production</h3>
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                Running
              </span>
            </div>
            <div className="space-y-2 mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium">URL:</span> prod.example.com
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Version:</span> Odoo 16.0
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Users:</span> 15/25
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Storage:</span> 45 GB
              </p>
            </div>
            <div className="flex space-x-2">
              <button className="btn btn-primary text-sm flex-1">
                Open
              </button>
              <button className="btn btn-secondary text-sm">
                Settings
              </button>
            </div>
          </div>

          {/* Instance Card 2 */}
          <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Staging</h3>
              <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                Updating
              </span>
            </div>
            <div className="space-y-2 mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium">URL:</span> staging.example.com
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Version:</span> Odoo 16.0
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Users:</span> 5/10
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Storage:</span> 12 GB
              </p>
            </div>
            <div className="flex space-x-2">
              <button className="btn btn-primary text-sm flex-1" disabled>
                Open
              </button>
              <button className="btn btn-secondary text-sm">
                Settings
              </button>
            </div>
          </div>

          {/* Instance Card 3 */}
          <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Development</h3>
              <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                Stopped
              </span>
            </div>
            <div className="space-y-2 mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium">URL:</span> dev.example.com
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Version:</span> Odoo 17.0
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Users:</span> 3/5
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Storage:</span> 8 GB
              </p>
            </div>
            <div className="flex space-x-2">
              <button className="btn btn-success text-sm flex-1">
                Start
              </button>
              <button className="btn btn-secondary text-sm">
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Instance Actions */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="btn btn-secondary text-sm">
              Backup All
            </button>
            <button className="btn btn-secondary text-sm">
              Update All
            </button>
            <button className="btn btn-secondary text-sm">
              Monitor Health
            </button>
            <button className="btn btn-secondary text-sm">
              View Logs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InstancesPage;

