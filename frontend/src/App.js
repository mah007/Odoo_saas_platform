import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import TenantsPage from './pages/dashboard/TenantsPage';
import BillingPage from './pages/dashboard/BillingPage';
import InstancesPage from './pages/dashboard/InstancesPage';

// Components
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/common/Layout';

// Styles
import './styles/globals.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected routes */}
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="instances" element={<InstancesPage />} />
              <Route path="tenants" element={<TenantsPage />} />
              <Route path="billing" element={<BillingPage />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

