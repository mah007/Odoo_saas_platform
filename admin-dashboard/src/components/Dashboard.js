import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  People,
  Business,
  Computer,
  AttachMoney,
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  Storage,
  Memory,
  Speed,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { adminAPI } from '../dataProvider';

const StatCard = ({ title, value, icon, color, subtitle, trend }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="body2">
            {title}
          </Typography>
          <Typography variant="h4" component="h2" color={color}>
            {value}
          </Typography>
          {subtitle && (
            <Typography color="textSecondary" variant="body2">
              {subtitle}
            </Typography>
          )}
          {trend && (
            <Box display="flex" alignItems="center" mt={1}>
              <TrendingUp fontSize="small" color={trend > 0 ? 'success' : 'error'} />
              <Typography variant="body2" color={trend > 0 ? 'success.main' : 'error.main'}>
                {trend > 0 ? '+' : ''}{trend}%
              </Typography>
            </Box>
          )}
        </Box>
        <Box color={`${color}.main`}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const SystemHealthCard = ({ health }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle />;
      case 'degraded': return <Warning />;
      case 'error': return <Error />;
      default: return <CircularProgress size={24} />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Health
        </Typography>
        <Box mb={2}>
          <Box display="flex" alignItems="center" mb={1}>
            {getStatusIcon(health.status)}
            <Typography variant="h6" ml={1}>
              Overall Status: 
              <Chip 
                label={health.status?.toUpperCase()} 
                color={getStatusColor(health.status)}
                size="small"
                sx={{ ml: 1 }}
              />
            </Typography>
          </Box>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Database</Typography>
            <Chip 
              label={health.database_status} 
              color={getStatusColor(health.database_status)}
              size="small"
            />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Redis</Typography>
            <Chip 
              label={health.redis_status} 
              color={getStatusColor(health.redis_status)}
              size="small"
            />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Docker</Typography>
            <Chip 
              label={health.docker_status} 
              color={getStatusColor(health.docker_status)}
              size="small"
            />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Connections</Typography>
            <Typography variant="body2">{health.active_connections}</Typography>
          </Grid>
        </Grid>

        <Box mt={2}>
          <Typography variant="body2" color="textSecondary">CPU Usage</Typography>
          <LinearProgress 
            variant="determinate" 
            value={health.cpu_usage_percent} 
            color={health.cpu_usage_percent > 80 ? 'error' : 'primary'}
          />
          <Typography variant="caption">{health.cpu_usage_percent}%</Typography>
        </Box>

        <Box mt={1}>
          <Typography variant="body2" color="textSecondary">Memory Usage</Typography>
          <LinearProgress 
            variant="determinate" 
            value={health.memory_usage_percent} 
            color={health.memory_usage_percent > 80 ? 'error' : 'primary'}
          />
          <Typography variant="caption">{health.memory_usage_percent}%</Typography>
        </Box>

        <Box mt={1}>
          <Typography variant="body2" color="textSecondary">Disk Usage</Typography>
          <LinearProgress 
            variant="determinate" 
            value={health.disk_usage_percent} 
            color={health.disk_usage_percent > 80 ? 'error' : 'primary'}
          />
          <Typography variant="caption">{health.disk_usage_percent}%</Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [billing, setBilling] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsData, healthData, billingData] = await Promise.all([
          adminAPI.getStats(),
          adminAPI.getSystemHealth(),
          adminAPI.getBillingOverview(),
        ]);
        
        setStats(statsData);
        setHealth(healthData);
        setBilling(billingData);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboard data: {error}
      </Alert>
    );
  }

  // Sample data for charts (replace with real data)
  const revenueData = [
    { month: 'Jan', revenue: 4000, users: 240 },
    { month: 'Feb', revenue: 3000, users: 139 },
    { month: 'Mar', revenue: 2000, users: 980 },
    { month: 'Apr', revenue: 2780, users: 390 },
    { month: 'May', revenue: 1890, users: 480 },
    { month: 'Jun', revenue: 2390, users: 380 },
  ];

  const instanceStatusData = [
    { name: 'Running', value: stats?.running_instances || 0, color: '#4caf50' },
    { name: 'Stopped', value: (stats?.total_instances || 0) - (stats?.running_instances || 0), color: '#f44336' },
  ];

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      
      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={stats?.total_users || 0}
            icon={<People fontSize="large" />}
            color="primary"
            subtitle={`${stats?.active_users || 0} active`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Tenants"
            value={stats?.total_tenants || 0}
            icon={<Business fontSize="large" />}
            color="secondary"
            subtitle={`${stats?.active_tenants || 0} active`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Odoo Instances"
            value={stats?.total_instances || 0}
            icon={<Computer fontSize="large" />}
            color="info"
            subtitle={`${stats?.running_instances || 0} running`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Monthly Revenue"
            value={`$${billing?.monthly_revenue || 0}`}
            icon={<AttachMoney fontSize="large" />}
            color="success"
            subtitle={`$${billing?.total_revenue || 0} total`}
          />
        </Grid>
      </Grid>

      {/* System Health and Charts */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <SystemHealthCard health={health || {}} />
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Revenue & User Growth
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="revenue" fill="#8884d8" name="Revenue ($)" />
                  <Line yAxisId="right" type="monotone" dataKey="users" stroke="#82ca9d" name="New Users" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Instance Status and Billing */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Instance Status Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={instanceStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {instanceStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Billing Overview
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Active Subscriptions</Typography>
                  <Typography variant="h6">{billing?.active_subscriptions || 0}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Trial Subscriptions</Typography>
                  <Typography variant="h6">{billing?.trial_subscriptions || 0}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Cancelled</Typography>
                  <Typography variant="h6">{billing?.cancelled_subscriptions || 0}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">ARPU</Typography>
                  <Typography variant="h6">${billing?.average_revenue_per_user || 0}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">Churn Rate</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(billing?.churn_rate || 0) * 100} 
                    color={billing?.churn_rate > 0.1 ? 'error' : 'success'}
                  />
                  <Typography variant="caption">{((billing?.churn_rate || 0) * 100).toFixed(1)}%</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;

