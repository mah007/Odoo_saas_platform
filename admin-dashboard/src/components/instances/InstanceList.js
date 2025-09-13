import React from 'react';
import {
    List,
    Datagrid,
    TextField,
    NumberField,
    DateField,
    ChipField,
    BooleanField,
    ShowButton,
    Button,
    useRecordContext,
    useNotify,
    useRefresh
} from 'react-admin';

const StartButton = () => {
    const record = useRecordContext();
    const notify = useNotify();
    const refresh = useRefresh();

    const handleStart = async () => {
        try {
            const response = await fetch(`/api/v1/odoo/${record.id}/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (response.ok) {
                notify('Instance start initiated', { type: 'success' });
                refresh();
            } else {
                notify('Failed to start instance', { type: 'error' });
            }
        } catch (error) {
            notify('Error starting instance', { type: 'error' });
        }
    };

    return (
        <Button 
            label="Start" 
            onClick={handleStart}
            disabled={record.status === 'running'}
        />
    );
};

const StopButton = () => {
    const record = useRecordContext();
    const notify = useNotify();
    const refresh = useRefresh();

    const handleStop = async () => {
        try {
            const response = await fetch(`/api/v1/odoo/${record.id}/stop`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (response.ok) {
                notify('Instance stop initiated', { type: 'success' });
                refresh();
            } else {
                notify('Failed to stop instance', { type: 'error' });
            }
        } catch (error) {
            notify('Error stopping instance', { type: 'error' });
        }
    };

    return (
        <Button 
            label="Stop" 
            onClick={handleStop}
            disabled={record.status !== 'running'}
        />
    );
};

export const InstanceList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="tenant_name" />
            <TextField source="container_name" />
            <ChipField source="status" />
            <NumberField source="port" />
            <TextField source="url" />
            <TextField source="odoo_version" />
            <BooleanField source="is_running" />
            <DateField source="created_at" />
            <StartButton />
            <StopButton />
            <ShowButton />
        </Datagrid>
    </List>
);

