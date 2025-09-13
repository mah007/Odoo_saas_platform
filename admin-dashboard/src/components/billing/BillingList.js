import React from 'react';
import {
    List,
    Datagrid,
    TextField,
    NumberField,
    DateField,
    ChipField,
    ShowButton
} from 'react-admin';

export const BillingList = (props) => (
    <List {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="tenant_id" />
            <NumberField source="amount" />
            <TextField source="currency" />
            <ChipField source="status" />
            <TextField source="plan_name" />
            <DateField source="billing_period_start" />
            <DateField source="billing_period_end" />
            <DateField source="created_at" />
            <DateField source="paid_at" />
            <ShowButton />
        </Datagrid>
    </List>
);

