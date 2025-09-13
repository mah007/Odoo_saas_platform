import React from 'react';
import {
  List,
  Datagrid,
  TextField,
  EmailField,
  BooleanField,
  DateField,
  EditButton,
  ShowButton,
  DeleteButton,
  Create,
  Edit,
  Show,
  SimpleForm,
  SimpleShowLayout,
  TextInput,
  BooleanInput,
  NumberInput,
  SelectInput,
  required,
  email,
  Toolbar,
  SaveButton,
  DeleteButton as FormDeleteButton,
  TopToolbar,
  CreateButton,
  ExportButton,
  FilterButton,
  SearchInput,
  ChipField,
  FunctionField,
  useRecordContext,
  ReferenceField,
  NumberField,
} from 'react-admin';
import {
  Chip,
  Avatar,
  Box,
  Typography,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Business,
  CheckCircle,
  Cancel,
  Warning,
  PlayArrow,
  Stop,
  Refresh,
  Storage,
  Computer,
  AttachMoney,
} from '@mui/icons-material';
import { adminAPI } from '../../dataProvider';

// Custom field components
const TenantAvatar = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  return (
    <Avatar sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}>
      <Business />
    </Avatar>
  );
};

const TenantStatusChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'error';
      case 'suspended': return 'warning';
      case 'trial': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle />;
      case 'inactive': return <Cancel />;
      case 'suspended': return <Warning />;
      case 'trial': return <CheckCircle />;
      default: return null;
    }
  };
  
  return (
    <Chip
      icon={getStatusIcon(record.status)}
      label={record.status?.toUpperCase()}
      color={getStatusColor(record.status)}
      size="small"
    />
  );
};

const TenantPlanChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getPlanColor = (plan) => {
    switch (plan) {
      case 'enterprise': return 'primary';
      case 'professional': return 'secondary';
      case 'basic': return 'default';
      case 'trial': return 'info';
      default: return 'default';
    }
  };
  
  return (
    <Chip
      label={record.plan?.toUpperCase()}
      color={getPlanColor(record.plan)}
      size="small"
      variant="outlined"
    />
  );
};

// Filters for the list
const tenantFilters = [
  <SearchInput source="search" placeholder="Search tenants..." alwaysOn />,
  <SelectInput
    source="status"
    label="Status"
    choices={[
      { id: 'active', name: 'Active' },
      { id: 'inactive', name: 'Inactive' },
      { id: 'suspended', name: 'Suspended' },
      { id: 'trial', name: 'Trial' },
    ]}
    allowEmpty
  />,
];

// List actions
const TenantListActions = () => (
  <TopToolbar>
    <FilterButton />
    <CreateButton />
    <ExportButton />
  </TopToolbar>
);

// Custom toolbar for forms
const TenantToolbar = (props) => (
  <Toolbar {...props}>
    <SaveButton />
    <FormDeleteButton />
  </Toolbar>
);

// Tenant List Component
export const TenantList = () => (
  <List
    filters={tenantFilters}
    actions={<TenantListActions />}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
  >
    <Datagrid rowClick="show" bulkActionButtons={false}>
      <FunctionField
        label="Avatar"
        render={() => <TenantAvatar />}
        sortable={false}
      />
      <TextField source="name" label="Tenant Name" />
      <TextField source="subdomain" label="Subdomain" />
      <FunctionField
        label="Status"
        render={() => <TenantStatusChip />}
        sortable={false}
      />
      <TextField source="owner_email" label="Owner Email" />
      <DateField source="created_at" label="Created" showTime />
      <EditButton />
      <ShowButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Tenant Create Component
export const TenantCreate = () => (
  <Create>
    <SimpleForm toolbar={<TenantToolbar />}>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          Tenant Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="name"
            label="Tenant Name"
            validate={[required()]}
            fullWidth
          />
          <TextInput
            source="subdomain"
            label="Subdomain"
            validate={[required()]}
            fullWidth
            helperText="Used for tenant-specific URLs"
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <SelectInput
            source="status"
            label="Status"
            choices={[
              { id: 'active', name: 'Active' },
              { id: 'inactive', name: 'Inactive' },
              { id: 'suspended', name: 'Suspended' },
              { id: 'trial', name: 'Trial' },
            ]}
            defaultValue="trial"
            validate={[required()]}
          />
          <TextInput
            source="owner_email"
            label="Owner Email"
            validate={[required(), email()]}
            fullWidth
          />
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Resource Limits
        </Typography>
        
        <Box display="flex" gap={2}>
          <NumberInput
            source="max_users"
            label="Max Users"
            defaultValue={5}
            min={1}
          />
          <NumberInput
            source="storage_limit_gb"
            label="Storage Limit (GB)"
            defaultValue={10}
            min={1}
          />
        </Box>
      </Box>
    </SimpleForm>
  </Create>
);

// Tenant Edit Component
export const TenantEdit = () => (
  <Edit>
    <SimpleForm toolbar={<TenantToolbar />}>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          Tenant Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="name"
            label="Tenant Name"
            validate={[required()]}
            fullWidth
          />
          <TextInput
            source="subdomain"
            label="Subdomain"
            validate={[required()]}
            fullWidth
            helperText="Used for tenant-specific URLs"
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <SelectInput
            source="status"
            label="Status"
            choices={[
              { id: 'active', name: 'Active' },
              { id: 'inactive', name: 'Inactive' },
              { id: 'suspended', name: 'Suspended' },
              { id: 'trial', name: 'Trial' },
            ]}
            validate={[required()]}
          />
          <TextInput
            source="owner_email"
            label="Owner Email"
            validate={[required(), email()]}
            fullWidth
          />
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Resource Limits
        </Typography>
        
        <Box display="flex" gap={2}>
          <NumberInput
            source="max_users"
            label="Max Users"
            min={1}
          />
          <NumberInput
            source="storage_limit_gb"
            label="Storage Limit (GB)"
            min={1}
          />
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Timestamps
        </Typography>
        
        <Box display="flex" gap={2}>
          <DateField source="created_at" label="Created At" showTime />
          <DateField source="updated_at" label="Updated At" showTime />
          <DateField source="expires_at" label="Expires At" showTime />
        </Box>
      </Box>
    </SimpleForm>
  </Edit>
);

// Tenant Show Component
export const TenantShow = () => (
  <Show>
    <SimpleShowLayout>
      <Box display="flex" flexDirection="column" gap={3} width="100%">
        <Box display="flex" alignItems="center" gap={2}>
          <TenantAvatar />
          <Box>
            <Typography variant="h5">
              <TextField source="name" />
            </Typography>
            <Typography variant="body2" color="textSecondary">
              <TextField source="subdomain" />.odoo-saas.com
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={2}>
          <TenantStatusChip />
        </Box>
        
        <Typography variant="h6" gutterBottom>
          Tenant Details
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Owner Email</Typography>
            <TextField source="owner_email" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Full Domain</Typography>
            <TextField source="full_domain" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Odoo Version</Typography>
            <TextField source="odoo_version" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Odoo Port</Typography>
            <TextField source="odoo_port" />
          </Box>
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Resource Limits
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Max Users</Typography>
            <NumberField source="max_users" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Storage Limit (GB)</Typography>
            <NumberField source="storage_limit_gb" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Plan ID</Typography>
            <TextField source="plan_id" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Database</Typography>
            <TextField source="odoo_database" />
          </Box>
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Timestamps
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Created At</Typography>
            <DateField source="created_at" showTime />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Updated At</Typography>
            <DateField source="updated_at" showTime />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Expires At</Typography>
            <DateField source="expires_at" showTime />
          </Box>
        </Box>
      </Box>
    </SimpleShowLayout>
  </Show>
);

