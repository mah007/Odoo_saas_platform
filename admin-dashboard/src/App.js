import React from 'react';
import { Admin, Resource, ListGuesser, EditGuesser, ShowGuesser } from 'react-admin';
import jsonServerProvider from 'ra-data-json-server';
import { Dashboard } from './components/Dashboard';
import { UserList, UserEdit, UserShow } from './components/users/UserList';
import { TenantList, TenantEdit, TenantShow } from './components/tenants/TenantList';
import { BillingList } from './components/billing/BillingList';
import { InstanceList } from './components/instances/InstanceList';

// Custom data provider for our FastAPI backend
const dataProvider = jsonServerProvider('/api/v1');

const App = () => (
  <Admin 
    dataProvider={dataProvider} 
    dashboard={Dashboard}
    title="Odoo SaaS Admin"
  >
    <Resource 
      name="users" 
      list={UserList} 
      edit={UserEdit} 
      show={UserShow}
      options={{ label: 'Users' }}
    />
    <Resource 
      name="tenants" 
      list={TenantList} 
      edit={TenantEdit} 
      show={TenantShow}
      options={{ label: 'Tenants' }}
    />
    <Resource 
      name="billing" 
      list={BillingList}
      options={{ label: 'Billing' }}
    />
    <Resource 
      name="instances" 
      list={InstanceList}
      options={{ label: 'Odoo Instances' }}
    />
  </Admin>
);

export default App;

