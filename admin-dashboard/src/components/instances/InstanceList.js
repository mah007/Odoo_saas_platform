import React, { useState } from 'react';
import {
  List,
  Datagrid,
  TextField,
  DateField,
  EditButton,
  ShowButton,
  DeleteButton,
  Show,
  SimpleShowLayout,
  TopToolbar,
  ExportButton,
  FilterButton,
  SearchInput,
  SelectInput,
  FunctionField,
  useRecordContext,
  ReferenceField,
  NumberField,
  useRefresh,
  useNotify,
} from 'react-admin';
import {
  Chip,
  Avatar,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
} from '@mui/material';
import {
  Computer,
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  Backup,
  Restore,
  Settings,
  CheckCircle,
  Cancel,
  Warning,
  Pause,
  Storage,
  Memory,
  Speed,
} from '@mui/icons-material';
import { adminAPI } from '../dataProvider';

// Custom field components
const InstanceAvatar = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getAvatarColor = (status) => {
    switch (status) {
      case 'running': return 'success.main';
      case 'stopped': return 'error.main';
      case 'creating': return 'info.main';
      case 'updating': return 'warning.main';
      default: return 'grey.500';
    }
  };
  
  return (
    <Avatar sx={{ width: 40, height: 40, bgcolor: getAvatarColor(record.status) }}>
      <Computer />
    </Avatar>
  );
};

const InstanceStatusChip = () => {
  const record = useRecordContext();
  if (!record) return null;
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'error';
      case 'creating': return 'info';
      case 'updating': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <CheckCircle />;
      case 'stopped': return <Cancel />;
      case 'creating': return <Settings />;
      case 'updating': return <Refresh />;
      case 'error': return <Warning />;
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

const InstanceActions = () => {
  const record = useRecordContext();
  const refresh = useRefresh();
  const notify = useNotify();
  const [loading, setLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null });

  if (!record) return null;

  const handleAction = async (action) => {
    setLoading(true);
    try {
      switch (action) {
        case 'start':
          await adminAPI.startInstance(record.id);
          notify('Instance started successfully', { type: 'success' });
          break;
        case 'stop':
          await adminAPI.stopInstance(record.id);
          notify('Instance stopped successfully', { type: 'success' });
          break;
        case 'restart':
          await adminAPI.restartInstance(record.id);
          notify('Instance restarted successfully', { type: 'success' });
          break;
        case 'backup':
          // Implement backup functionality
          notify('Backup initiated', { type: 'info' });
          break;
      }
      refresh();
    } catch (error) {
      notify(`Failed to ${action} instance: ${error.message}`, { type: 'error' });
    } finally {
      setLoading(false);
      setConfirmDialog({ open: false, action: null });
    }
  };

  const openConfirmDialog = (action) => {
    setConfirmDialog({ open: true, action });
  };

  const closeConfirmDialog = () => {
    setConfirmDialog({ open: false, action: null });
  };

  return (
    <>
      <Box display="flex" gap={0.5}>
        <Tooltip title="Start Instance">
          <span>
            <IconButton 
              size="small" 
              onClick={() => handleAction('start')}
              disabled={loading || record.status === 'running'}
              color="success"
            >
              <PlayArrow />
            </IconButton>
          </span>
        </Tooltip>
        
        <Tooltip title="Stop Instance">
          <span>
            <IconButton 
              size="small" 
              onClick={() => openConfirmDialog('stop')}
              disabled={loading || record.status === 'stopped'}
              color="error"
            >
              <Stop />
            </IconButton>
          </span>
        </Tooltip>
        
        <Tooltip title="Restart Instance">
          <span>
            <IconButton 
              size="small" 
              onClick={() => openConfirmDialog('restart')}
              disabled={loading || record.status !== 'running'}
              color="warning"
            >
              <Refresh />
            </IconButton>
          </span>
        </Tooltip>
        
        <Tooltip title="Create Backup">
          <span>
            <IconButton 
              size="small" 
              onClick={() => handleAction('backup')}
              disabled={loading || record.status !== 'running'}
              color="info"
            >
              <Backup />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      <Dialog open={confirmDialog.open} onClose={closeConfirmDialog}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to {confirmDialog.action} this instance?
            {confirmDialog.action === 'stop' && ' This will make the instance unavailable to users.'}
            {confirmDialog.action === 'restart' && ' This will temporarily interrupt service.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeConfirmDialog}>Cancel</Button>
          <Button 
            onClick={() => handleAction(confirmDialog.action)} 
            color="primary"
            variant="contained"
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// Filters for the list
const instanceFilters = [
  <SearchInput source="search" placeholder="Search instances..." alwaysOn />,
  <SelectInput
    source="status"
    label="Status"
    choices={[
      { id: 'running', name: 'Running' },
      { id: 'stopped', name: 'Stopped' },
      { id: 'creating', name: 'Creating' },
      { id: 'updating', name: 'Updating' },
      { id: 'error', name: 'Error' },
    ]}
    allowEmpty
  />,
  <SelectInput
    source="odoo_version"
    label="Odoo Version"
    choices={[
      { id: '17.0', name: '17.0' },
      { id: '16.0', name: '16.0' },
      { id: '15.0', name: '15.0' },
    ]}
    allowEmpty
  />,
];

// List actions
const InstanceListActions = () => (
  <TopToolbar>
    <FilterButton />
    <ExportButton />
  </TopToolbar>
);

// Instance List Component
export const InstanceList = () => (
  <List
    filters={instanceFilters}
    actions={<InstanceListActions />}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
  >
    <Datagrid rowClick="show" bulkActionButtons={false}>
      <FunctionField
        label="Avatar"
        render={() => <InstanceAvatar />}
        sortable={false}
      />
      <TextField source="container_name" label="Container Name" />
      <TextField source="tenant_name" label="Tenant" />
      <FunctionField
        label="Status"
        render={() => <InstanceStatusChip />}
        sortable={false}
      />
      <TextField source="odoo_version" label="Version" />
      <NumberField source="port" label="Port" />
      <TextField source="url" label="URL" />
      <DateField source="created_at" label="Created" showTime />
      <FunctionField
        label="Actions"
        render={() => <InstanceActions />}
        sortable={false}
      />
      <ShowButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Instance Show Component
export const InstanceShow = () => (
  <Show>
    <SimpleShowLayout>
      <Box display="flex" flexDirection="column" gap={3} width="100%">
        <Box display="flex" alignItems="center" gap={2}>
          <InstanceAvatar />
          <Box>
            <Typography variant="h5">
              <TextField source="container_name" />
            </Typography>
            <Typography variant="body2" color="textSecondary">
              <TextField source="url" />
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={2}>
          <InstanceStatusChip />
          <Chip label={`Odoo ${record?.odoo_version}`} variant="outlined" />
        </Box>
        
        <Typography variant="h6" gutterBottom>
          Instance Details
        </Typography>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">Tenant</Typography>
            <TextField source="tenant_name" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Port</Typography>
            <NumberField source="port" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Odoo Version</Typography>
            <TextField source="odoo_version" />
          </Box>
          <Box>
            <Typography variant="body2" color="textSecondary">Running</Typography>
            <TextField source="is_running" />
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
        </Box>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Instance Actions
        </Typography>
        
        <InstanceActions />
      </Box>
    </SimpleShowLayout>
  </Show>
);

