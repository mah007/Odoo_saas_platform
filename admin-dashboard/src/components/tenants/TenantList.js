import React from 'react';
import {
    List,
    Datagrid,
    TextField,
    DateField,
    Edit,
    SimpleForm,
    TextInput,
    SelectInput,
    Show,
    SimpleShowLayout,
    EditButton,
    ShowButton,
    ChipField
} from 'react-admin';

const statusChoices = [
    { id: 'pending', name: 'Pending' },
    { id: 'active', name: 'Active' },
    { id: 'suspended', name: 'Suspended' },
    { id: 'cancelled', name: 'Cancelled' },
];

export const TenantList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="name" />
            <TextField source="subdomain" />
            <ChipField source="status" />
            <TextField source="owner_email" />
            <TextField source="full_domain" />
            <DateField source="created_at" />
            <EditButton />
            <ShowButton />
        </Datagrid>
    </List>
);

export const TenantEdit = (props) => (
    <Edit {...props}>
        <SimpleForm>
            <TextInput source="name" />
            <TextInput source="subdomain" />
            <SelectInput source="status" choices={statusChoices} />
            <TextInput source="domain" />
            <TextInput source="odoo_version" />
            <TextInput source="max_users" />
            <TextInput source="storage_limit_gb" />
        </SimpleForm>
    </Edit>
);

export const TenantShow = (props) => (
    <Show {...props}>
        <SimpleShowLayout>
            <TextField source="id" />
            <TextField source="name" />
            <TextField source="subdomain" />
            <ChipField source="status" />
            <TextField source="domain" />
            <TextField source="full_domain" />
            <TextField source="owner_email" />
            <TextField source="odoo_version" />
            <TextField source="odoo_port" />
            <TextField source="odoo_database" />
            <TextField source="max_users" />
            <TextField source="storage_limit_gb" />
            <TextField source="plan_id" />
            <DateField source="created_at" />
            <DateField source="updated_at" />
            <DateField source="expires_at" />
        </SimpleShowLayout>
    </Show>
);

