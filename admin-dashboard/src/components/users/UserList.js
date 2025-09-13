import React from 'react';
import {
    List,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    DateField,
    Edit,
    SimpleForm,
    TextInput,
    BooleanInput,
    Show,
    SimpleShowLayout,
    EditButton,
    ShowButton
} from 'react-admin';

export const UserList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <EmailField source="email" />
            <TextField source="full_name" />
            <TextField source="company" />
            <BooleanField source="is_active" />
            <BooleanField source="is_admin" />
            <BooleanField source="is_verified" />
            <DateField source="created_at" />
            <EditButton />
            <ShowButton />
        </Datagrid>
    </List>
);

export const UserEdit = (props) => (
    <Edit {...props}>
        <SimpleForm>
            <TextInput source="email" />
            <TextInput source="full_name" />
            <TextInput source="company" />
            <TextInput source="phone" />
            <BooleanInput source="is_active" />
            <BooleanInput source="is_admin" />
            <BooleanInput source="is_verified" />
        </SimpleForm>
    </Edit>
);

export const UserShow = (props) => (
    <Show {...props}>
        <SimpleShowLayout>
            <TextField source="id" />
            <EmailField source="email" />
            <TextField source="full_name" />
            <TextField source="company" />
            <TextField source="phone" />
            <BooleanField source="is_active" />
            <BooleanField source="is_admin" />
            <BooleanField source="is_verified" />
            <DateField source="created_at" />
            <DateField source="updated_at" />
            <DateField source="last_login" />
        </SimpleShowLayout>
    </Show>
);

