import React from 'react';
import {
  List,
  Datagrid,
  TextField,
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
  NumberInput,
  SelectInput,
  DateInput,
  required,
  Toolbar,
  SaveButton,
  DeleteButton as FormDeleteButton,
  TopToolbar,
  CreateButton,
  ExportButton,
  FilterButton,
  SearchInput,
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
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  AttachMoney,
  CheckCircle,
  Cancel,
  Warning,
  Schedule,
  Receipt,
  CreditCard,
  AccountBalance,
} from '@mui/icons-material';

// Custom field components
const BillingAvatar = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getAvatarColor = (status) => {
    switch (status) {
      case 'paid': return 'success.main';
      case 'pending': return 'warning.main';
      case 'failed': return 'error.main';
      case 'refunded': return 'info.main';
      default: return 'grey.500';
    }
  };
  
  return (
    <Avatar sx={{ width: 40, height: 40, bgcolor: getAvatarColor(record.status) }}>
      <Receipt />
    </Avatar>
  );
};

const BillingStatusChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'paid': return 'success';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      case 'refunded': return 'info';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'paid': return <CheckCircle />;
      case 'pending': return <Schedule />;
      case 'failed': return <Cancel />;
      case 'refunded': return <AccountBalance />;
      case 'cancelled': return <Cancel />;
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

const AmountField = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  return (
    <Box display="flex" alignItems="center" gap={1}>
      <AttachMoney fontSize="small" />
      <Typography variant="body2" fontWeight="bold">
        ${(record.amount / 100).toFixed(2)} {record.currency?.toUpperCase()}
      </Typography>
    </Box>
  );
};

// Filters for the list
const billingFilters = [
  <SearchInput source="search" placeholder="Search billing..." alwaysOn />,
  <SelectInput
    source="status"
    label="Status"
    choices={[
      { id: 'paid', name: 'Paid' },
      { id: 'pending', name: 'Pending' },
      { id: 'failed', name: 'Failed' },
      { id: 'refunded', name: 'Refunded' },
      { id: 'cancelled', name: 'Cancelled' },
    ]}
    allowEmpty
  />,
];

// List actions
const BillingListActions = () => (
  <TopToolbar>
    <FilterButton />
    <CreateButton />
    <ExportButton />
  </TopToolbar>
);

// Billing List Component
export const BillingList = () => (
  <List
    filters={billingFilters}
    actions={<BillingListActions />}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
  >
    <Datagrid rowClick="show" bulkActionButtons={false}>
      <FunctionField
        label="Avatar"
        render={() => <BillingAvatar />}
        sortable={false}
      />
      <TextField source="id" label="ID" />
      <TextField source="tenant_id" label="Tenant ID" />
      <FunctionField
        label="Amount"
        render={() => <AmountField />}
        sortable={false}
      />
      <FunctionField
        label="Status"
        render={() => <BillingStatusChip />}
        sortable={false}
      />
      <TextField source="plan_name" label="Plan" />
      <DateField source="billing_period_start" label="Period Start" />
      <DateField source="billing_period_end" label="Period End" />
      <DateField source="created_at" label="Created" showTime />
      <DateField source="paid_at" label="Paid At" showTime />
      <EditButton />
      <ShowButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Billing Create Component
export const BillingCreate = () => (
  <Create>
    <SimpleForm>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          Billing Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="tenant_id"
            label="Tenant ID"
            validate={[required()]}
            fullWidth
          />
          <NumberInput
            source="amount"
            label="Amount (cents)"
            validate={[required()]}
            min={0}
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="currency"
            label="Currency"
            defaultValue="USD"
            validate={[required()]}
          />
          <SelectInput
            source="status"
            label="Status"
            choices={[
              { id: 'pending', name: 'Pending' },
              { id: 'paid', name: 'Paid' },
              { id: 'failed', name: 'Failed' },
              { id: 'refunded', name: 'Refunded' },
              { id: 'cancelled', name: 'Cancelled' },
            ]}
            defaultValue="pending"
            validate={[required()]}
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="plan_name"
            label="Plan Name"
            validate={[required()]}
            fullWidth
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <DateInput
            source="billing_period_start"
            label="Billing Period Start"
            validate={[required()]}
          />
          <DateInput
            source="billing_period_end"
            label="Billing Period End"
            validate={[required()]}
          />
        </Box>
      </Box>
    </SimpleForm>
  </Create>
);

// Billing Edit Component
export const BillingEdit = () => (
  <Edit>
    <SimpleForm>
      <Box display="flex" flexDirection="column" gap={2} width="100%">
        <Typography variant="h6" gutterBottom>
          Billing Information
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="tenant_id"
            label="Tenant ID"
            validate={[required()]}
            fullWidth
          />
          <NumberInput
            source="amount"
            label="Amount (cents)"
            validate={[required()]}
            min={0}
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="currency"
            label="Currency"
            validate={[required()]}
          />
          <SelectInput
            source="status"
            label="Status"
            choices={[
              { id: 'pending', name: 'Pending' },
              { id: 'paid', name: 'Paid' },
              { id: 'failed', name: 'Failed' },
              { id: 'refunded', name: 'Refunded' },
              { id: 'cancelled', name: 'Cancelled' },
            ]}
            validate={[required()]}
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <TextInput
            source="plan_name"
            label="Plan Name"
            validate={[required()]}
            fullWidth
          />
        </Box>
        
        <Box display="flex" gap={2}>
          <DateInput
            source="billing_period_start"
            label="Billing Period Start"
            validate={[required()]}
          />
          <DateInput
            source="billing_period_end"
            label="Billing Period End"
            validate={[required()]}
          />
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Timestamps
        </Typography>
        
        <Box display="flex" gap={2}>
          <DateField source="created_at" label="Created At" showTime />
          <DateField source="paid_at" label="Paid At" showTime />
        </Box>
      </Box>
    </SimpleForm>
  </Edit>
);

// Billing Show Component
export const BillingShow = () => (
  <Show>
    <SimpleShowLayout>
      <Box display="flex" flexDirection="column" gap={3} width="100%">
        <Box display="flex" alignItems="center" gap={2}>
          <BillingAvatar />
          <Box>
            <Typography variant="h5">
              Billing Record #{<TextField source="id" />}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              <AmountField />
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={2}>
          <BillingStatusChip />
        </Box>
        
        <Typography variant="h6" gutterBottom>
          Billing Details
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Tenant ID</Typography>
            <TextField source="tenant_id" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Amount</Typography>
            <NumberField source="amount" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Currency</Typography>
            <TextField source="currency" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Plan Name</Typography>
            <TextField source="plan_name" />
          </Box>
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Billing Period
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Period Start</Typography>
            <DateField source="billing_period_start" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Period End</Typography>
            <DateField source="billing_period_end" />
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
            <Typography variant="body2" color="textSecondary">Paid At</Typography>
            <DateField source="paid_at" showTime />
          </Box>
        </Box>
      </Box>
    </SimpleShowLayout>
  </Show>
);

