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
  DateInput,
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
  SelectInput,
  ChipField,
  FunctionField,
  useRecordContext,
} from 'react-admin';
import {
  Chip,
  Avatar,
  Box,
  Typography,
} from '@mui/material';
import {
  Person,
  AdminPanelSettings,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';

// Custom field components
const UserAvatar = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  return (
    <Avatar sx={{ width: 40, height: 40 }}>
      {record.full_name ? record.full_name.charAt(0).toUpperCase() : record.email.charAt(0).toUpperCase()}
    </Avatar>
  );
};

const UserStatusChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  return (
    <Chip
      icon={record.is_active ? <CheckCircle /> : <Cancel />}
      label={record.is_active ? 'Active' : 'Inactive'}
      color={record.is_active ? 'success' : 'error'}
      size="small"
    />
  );
};

const UserRoleChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  return (
    <Chip
      icon={record.is_admin ? <AdminPanelSettings /> : <Person />}
      label={record.is_admin ? 'Admin' : 'User'}
      color={record.is_admin ? 'primary' : 'default'}
      size="small"
    />
  );
};

// Filters for the list
const userFilters = [
  <SearchInput source="search" placeholder="Search users..." alwaysOn />,
  <SelectInput
    source="is_active"
    label="Status"
    choices={[
      { id: true, name: 'Active' },
      { id: false, name: 'Inactive' },
    ]}
    allowEmpty
  />,
  <SelectInput
    source="is_admin"
    label="Role"
    choices={[
      { id: true, name: 'Admin' },
      { id: false, name: 'User' },
    ]}
    allowEmpty
  />,
];

// List actions
const UserListActions = () => (
  <TopToolbar>
    <FilterButton />
    <CreateButton />
    <ExportButton />
  </TopToolbar>
);

// Custom toolbar for forms
const UserToolbar = (props) => (
  <Toolbar {...props}>
    <SaveButton />
    <FormDeleteButton />
  </Toolbar>
);

// User List Component
export const UserList = () => (
  <List
    filters={userFilters}
    actions={<UserListActions />}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
  >
    <Datagrid rowClick="show" bulkActionButtons={false}>
      <FunctionField
        label="Avatar"
        render={() => <UserAvatar />}
        sortable={false}
      />
      <TextField source="full_name" label="Full Name" />
      <EmailField source="email" label="Email" />
      <FunctionField
        label="Status"
        render={() => <UserStatusChip />}
        sortable={false}
      />
      <FunctionField
        label="Role"
        render={() => <UserRoleChip />}
        sortable={false}
      />
      <DateField source="created_at" label="Created" showTime />
      <DateField source="last_login_at" label="Last Login" showTime />
      <EditButton />
      <ShowButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// User Create Component
export const UserCreate = () => (
  <Create>
    <SimpleForm toolbar={<UserToolbar />}>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          User Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="full_name"
            label="Full Name"
            validate={[required()]}
            fullWidth
          />
          <EmailField
            source="email"
            label="Email"
            validate={[required(), email()]}
            fullWidth
          />
        </Box>
        
        <TextInput
          source="password"
          label="Password"
          type="password"
          validate={[required()]}
          fullWidth
        />
        
        <Box display="flex" gap={2}>
          <BooleanInput
            source="is_active"
            label="Active"
            defaultValue={true}
          />
          <BooleanInput
            source="is_admin"
            label="Admin"
            defaultValue={false}
          />
          <BooleanInput
            source="is_verified"
            label="Email Verified"
            defaultValue={false}
          />
        </Box>
      </Box>
    </SimpleForm>
  </Create>
);

// User Edit Component
export const UserEdit = () => (
  <Edit>
    <SimpleForm toolbar={<UserToolbar />}>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          User Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="full_name"
            label="Full Name"
            validate={[required()]}
            fullWidth
          />
          <EmailField
            source="email"
            label="Email"
            validate={[required(), email()]}
            fullWidth
          />
        </Box>
        
        <TextInput
          source="password"
          label="New Password (leave blank to keep current)"
          type="password"
          fullWidth
        />
        
        <Box display="flex" gap={2}>
          <BooleanInput
            source="is_active"
            label="Active"
          />
          <BooleanInput
            source="is_admin"
            label="Admin"
          />
          <BooleanInput
            source="is_verified"
            label="Email Verified"
          />
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Timestamps
        </Typography>
        
        <Box display="flex" gap={2}>
          <DateField source="created_at" label="Created At" showTime />
          <DateField source="updated_at" label="Updated At" showTime />
          <DateField source="last_login_at" label="Last Login" showTime />
        </Box>
      </Box>
    </SimpleForm>
  </Edit>
);

// User Show Component
export const UserShow = () => (
  <Show>
    <SimpleShowLayout>
      <Box display="flex" flexDirection="column" gap={3} width="100%">
        <Box display="flex" alignItems="center" gap={2}>
          <UserAvatar />
          <Box>
            <Typography variant="h5">
              <TextField source="full_name" />
            </Typography>
            <Typography variant="body2" color="textSecondary">
              <EmailField source="email" />
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={2}>
          <UserStatusChip />
          <UserRoleChip />
          {/* Add more status chips as needed */}
        </Box>
        
        <Typography variant="h6" gutterBottom>
          Account Details
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Email Verified</Typography>
            <BooleanField source="is_verified" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Account Active</Typography>
            <BooleanField source="is_active" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Admin User</Typography>
            <BooleanField source="is_admin" />
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
            <Typography variant="body2" color="textSecondary">Last Login</Typography>
            <DateField source="last_login_at" showTime />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Email Verified At</Typography>
            <DateField source="email_verified_at" showTime />
          </Box>
        </Box>
      </Box>
    </SimpleShowLayout>
  </Show>
);

