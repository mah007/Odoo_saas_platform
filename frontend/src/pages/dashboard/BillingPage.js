import React from 'react';

const BillingPage = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Billing</h1>
        <p className="text-gray-600">Manage your subscription and billing information</p>
      </div>

      {/* Current Plan */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Plan</h2>
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium">Professional Plan</h3>
            <p className="text-gray-600">$99/month • 5 instances • 25 users</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-green-600">$99.00</div>
            <p className="text-sm text-gray-600">Next billing: Feb 15, 2024</p>
          </div>
        </div>
        <div className="mt-4">
          <button className="btn btn-primary mr-3">Upgrade Plan</button>
          <button className="btn btn-secondary">Change Plan</button>
        </div>
      </div>

      {/* Usage */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Usage</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">Instances</span>
              <span className="text-sm font-medium">3 / 5</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '60%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">Users</span>
              <span className="text-sm font-medium">18 / 25</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-600 h-2 rounded-full" style={{ width: '72%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">Storage</span>
              <span className="text-sm font-medium">156 GB / 200 GB</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '78%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Method */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Payment Method</h2>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-12 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold mr-3">
              VISA
            </div>
            <div>
              <p className="font-medium">•••• •••• •••• 4242</p>
              <p className="text-sm text-gray-600">Expires 12/25</p>
            </div>
          </div>
          <button className="btn btn-secondary">Update</button>
        </div>
      </div>

      {/* Billing History */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Billing History</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Invoice
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  Jan 15, 2024
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  Professional Plan - Monthly
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  $99.00
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Paid
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-600 hover:text-blue-900">Download</button>
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  Dec 15, 2023
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  Professional Plan - Monthly
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  $99.00
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Paid
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-600 hover:text-blue-900">Download</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BillingPage;

