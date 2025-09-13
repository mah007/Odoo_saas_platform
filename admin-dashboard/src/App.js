import React from 'react';
import { Admin, Resource } from 'react-admin';
import Dashboard from './components/Dashboard';
import { UserList, UserEdit, UserShow } from './components/users/UserList';
import { TenantList, TenantEdit, TenantShow } from './components/tenants/TenantList';
import { BillingList } from './components/billing/BillingList';
import { InstanceList } from './components/instances/InstanceList';
import dataProvider from './dataProvider';

const App = () => (
  <Admin 
    dataProvider={dataProvider} 
    dashboard={Dashboard}
    title="Odoo SaaS Admin"
  >
    <Resource 
      name="admin/users" 
      list={UserList} 
      edit={UserEdit} 
      show={UserShow}
      options={{ label: 'Users' }}
    />
    <Resource 
      name="admin/tenants" 
      list={TenantList} 
      edit={TenantEdit} 
      show={TenantShow}
      options={{ label: 'Tenants' }}
    />
    <Resource 
      name="admin/billing" 
      list={BillingList}
      options={{ label: 'Billing' }}
    />
    <Resource 
      name="admin/instances" 
      list={InstanceList}
      options={{ label: 'Odoo Instances' }}
    />
  </Admin>
);

export default App;

