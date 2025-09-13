/**
 * Custom data provider for FastAPI backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const dataProvider = {
  // Get list of resources
  getList: async (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
    const query = params.filter;

    let url = `/${resource}`;
    const queryParams = new URLSearchParams();

    // Handle pagination
    queryParams.append('skip', (page - 1) * perPage);
    queryParams.append('limit', perPage);

    // Handle sorting
    if (field) {
      queryParams.append('sort', `${field}:${order.toLowerCase()}`);
    }

    // Handle filtering
    Object.keys(query).forEach(key => {
      if (query[key]) {
        queryParams.append(key, query[key]);
      }
    });

    if (queryParams.toString()) {
      url += `?${queryParams.toString()}`;
    }

    try {
      const response = await apiClient.get(url);
      
      return {
        data: response.data.map(item => ({ ...item, id: item.id })),
        total: response.headers['x-total-count'] || response.data.length,
      };
    } catch (error) {
      throw new Error(`Failed to fetch ${resource}: ${error.message}`);
    }
  },

  // Get one resource
  getOne: async (resource, params) => {
    try {
      const response = await apiClient.get(`/${resource}/${params.id}`);
      return { data: { ...response.data, id: response.data.id } };
    } catch (error) {
      throw new Error(`Failed to fetch ${resource} ${params.id}: ${error.message}`);
    }
  },

  // Get many resources by IDs
  getMany: async (resource, params) => {
    try {
      const promises = params.ids.map(id => apiClient.get(`/${resource}/${id}`));
      const responses = await Promise.all(promises);
      return {
        data: responses.map(response => ({ ...response.data, id: response.data.id }))
      };
    } catch (error) {
      throw new Error(`Failed to fetch multiple ${resource}: ${error.message}`);
    }
  },

  // Get many resources by reference
  getManyReference: async (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
    const query = { ...params.filter, [params.target]: params.id };

    const queryParams = new URLSearchParams();
    queryParams.append('skip', (page - 1) * perPage);
    queryParams.append('limit', perPage);

    if (field) {
      queryParams.append('sort', `${field}:${order.toLowerCase()}`);
    }

    Object.keys(query).forEach(key => {
      if (query[key]) {
        queryParams.append(key, query[key]);
      }
    });

    try {
      const response = await apiClient.get(`/${resource}?${queryParams.toString()}`);
      return {
        data: response.data.map(item => ({ ...item, id: item.id })),
        total: response.headers['x-total-count'] || response.data.length,
      };
    } catch (error) {
      throw new Error(`Failed to fetch ${resource} reference: ${error.message}`);
    }
  },

  // Create resource
  create: async (resource, params) => {
    try {
      const response = await apiClient.post(`/${resource}`, params.data);
      return { data: { ...response.data, id: response.data.id } };
    } catch (error) {
      throw new Error(`Failed to create ${resource}: ${error.message}`);
    }
  },

  // Update resource
  update: async (resource, params) => {
    try {
      const response = await apiClient.put(`/${resource}/${params.id}`, params.data);
      return { data: { ...response.data, id: response.data.id } };
    } catch (error) {
      throw new Error(`Failed to update ${resource} ${params.id}: ${error.message}`);
    }
  },

  // Update many resources
  updateMany: async (resource, params) => {
    try {
      const promises = params.ids.map(id =>
        apiClient.put(`/${resource}/${id}`, params.data)
      );
      const responses = await Promise.all(promises);
      return { data: responses.map(response => response.data.id) };
    } catch (error) {
      throw new Error(`Failed to update multiple ${resource}: ${error.message}`);
    }
  },

  // Delete resource
  delete: async (resource, params) => {
    try {
      await apiClient.delete(`/${resource}/${params.id}`);
      return { data: { ...params.previousData, id: params.id } };
    } catch (error) {
      throw new Error(`Failed to delete ${resource} ${params.id}: ${error.message}`);
    }
  },

  // Delete many resources
  deleteMany: async (resource, params) => {
    try {
      const promises = params.ids.map(id => apiClient.delete(`/${resource}/${id}`));
      await Promise.all(promises);
      return { data: params.ids };
    } catch (error) {
      throw new Error(`Failed to delete multiple ${resource}: ${error.message}`);
    }
  },
};

// Custom methods for admin-specific endpoints
export const adminAPI = {
  // Get admin statistics
  getStats: async () => {
    const response = await apiClient.get('/admin/stats');
    return response.data;
  },

  // Get system health
  getSystemHealth: async () => {
    const response = await apiClient.get('/admin/system-health');
    return response.data;
  },

  // Get users for management
  getUsers: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);
    if (params.is_admin !== undefined) queryParams.append('is_admin', params.is_admin);

    const response = await apiClient.get(`/admin/users?${queryParams.toString()}`);
    return response.data;
  },

  // Get tenants for management
  getTenants: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    if (params.status) queryParams.append('status', params.status);

    const response = await apiClient.get(`/admin/tenants?${queryParams.toString()}`);
    return response.data;
  },

  // Get instances for management
  getInstances: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    if (params.status) queryParams.append('status', params.status);

    const response = await apiClient.get(`/admin/instances?${queryParams.toString()}`);
    return response.data;
  },

  // Get billing overview
  getBillingOverview: async () => {
    const response = await apiClient.get('/admin/billing-overview');
    return response.data;
  },

  // Get audit logs
  getAuditLogs: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.offset) queryParams.append('offset', params.offset);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.user_id) queryParams.append('user_id', params.user_id);
    if (params.action) queryParams.append('action', params.action);
    if (params.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);

    const response = await apiClient.get(`/admin/audit-logs?${queryParams.toString()}`);
    return response.data;
  },

  // Instance control actions
  startInstance: async (instanceId) => {
    const response = await apiClient.post(`/odoo-instances/${instanceId}/start`);
    return response.data;
  },

  stopInstance: async (instanceId) => {
    const response = await apiClient.post(`/odoo-instances/${instanceId}/stop`);
    return response.data;
  },

  restartInstance: async (instanceId) => {
    const response = await apiClient.post(`/odoo-instances/${instanceId}/restart`);
    return response.data;
  },

  // Get instance stats
  getInstanceStats: async (instanceId) => {
    const response = await apiClient.get(`/odoo-instances/${instanceId}/stats`);
    return response.data;
  },

  // Get instance health
  getInstanceHealth: async (instanceId) => {
    const response = await apiClient.get(`/odoo-instances/${instanceId}/health`);
    return response.data;
  },
};

export default dataProvider;

