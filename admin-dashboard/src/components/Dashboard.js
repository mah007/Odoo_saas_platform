import React from 'react';
import { Card, CardContent, CardHeader } from '@mui/material';
import { Title, useGetList } from 'react-admin';

export const Dashboard = () => {
    const { data: users, total: totalUsers } = useGetList('users');
    const { data: tenants, total: totalTenants } = useGetList('tenants');
    const { data: instances, total: totalInstances } = useGetList('instances');

    return (
        <div style={{ margin: '1em' }}>
            <Title title="Admin Dashboard" />
            
            <div style={{ display: 'flex', gap: '1em', marginBottom: '2em' }}>
                <Card style={{ flex: 1 }}>
                    <CardHeader title="Total Users" />
                    <CardContent>
                        <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#1976d2' }}>
                            {totalUsers || 0}
                        </div>
                    </CardContent>
                </Card>
                
                <Card style={{ flex: 1 }}>
                    <CardHeader title="Total Tenants" />
                    <CardContent>
                        <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#388e3c' }}>
                            {totalTenants || 0}
                        </div>
                    </CardContent>
                </Card>
                
                <Card style={{ flex: 1 }}>
                    <CardHeader title="Active Instances" />
                    <CardContent>
                        <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#f57c00' }}>
                            {totalInstances || 0}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader title="Welcome to Odoo SaaS Admin Dashboard" />
                <CardContent>
                    <p>
                        Manage your multi-tenant Odoo SaaS platform from this comprehensive admin interface.
                    </p>
                    <ul>
                        <li><strong>Users:</strong> Manage user accounts and permissions</li>
                        <li><strong>Tenants:</strong> Create and manage tenant organizations</li>
                        <li><strong>Billing:</strong> Monitor subscriptions and payments</li>
                        <li><strong>Instances:</strong> Control Odoo instance deployments</li>
                    </ul>
                </CardContent>
            </Card>
        </div>
    );
};

