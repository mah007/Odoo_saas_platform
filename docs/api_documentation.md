# Odoo SaaS Platform - API Documentation

This document provides comprehensive documentation for the Odoo SaaS Platform API. It covers all endpoints, data models, and authentication methods.

## Table of Contents

1.  **Introduction**
    *   API Overview
    *   Authentication
    *   Rate Limiting
2.  **Authentication API**
    *   Register
    *   Login
    *   Refresh Token
    *   Verify Email
    *   Password Reset
3.  **Admin API**
    *   Get Platform Statistics
    *   Manage Users
    *   Manage Tenants
    *   Manage Instances
4.  **Tenant API**
    *   Create Tenant
    *   Get Tenant Details
    *   Update Tenant
    *   Delete Tenant
5.  **Odoo Instances API**
    *   Create Instance
    *   Get Instance Details
    *   Manage Instance Lifecycle
6.  **Billing API**
    *   Get Subscription Plans
    *   Create Subscription
    *   Manage Payment Methods
    *   Get Invoices
7.  **Security API**
    *   Get Security Metrics
    *   Scan for Vulnerabilities
    *   Manage Threats
8.  **Backup API**
    *   Create Backup
    *   List Backups
    *   Restore Backup

---

## 1. Introduction

### API Overview

The Odoo SaaS Platform API is a RESTful API that provides programmatic access to all platform features. It is built with FastAPI and includes comprehensive security, monitoring, and documentation.

### Authentication

Authentication is handled via JWT (JSON Web Tokens). To access protected endpoints, you must include an `Authorization` header with a valid access token:

```
Authorization: Bearer <your_access_token>
```

### Rate Limiting

The API includes rate limiting to protect against abuse. If you exceed the rate limit, you will receive a `429 Too Many Requests` response.

---

## 2. Authentication API

### Register

*   **Endpoint**: `POST /api/v1/auth/register`
*   **Description**: Register a new user account.
*   **Request Body**:
    ```json
    {
        "email": "user@example.com",
        "password": "your_strong_password",
        "full_name": "Test User"
    }
    ```
*   **Response**:
    ```json
    {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Test User"
    }
    ```

### Login

*   **Endpoint**: `POST /api/v1/auth/login`
*   **Description**: Authenticate and receive an access token.
*   **Request Body**:
    ```json
    {
        "username": "user@example.com",
        "password": "your_password"
    }
    ```
*   **Response**:
    ```json
    {
        "access_token": "your_access_token",
        "refresh_token": "your_refresh_token",
        "token_type": "bearer"
    }
    ```

---

## 3. Admin API

### Get Platform Statistics

*   **Endpoint**: `GET /api/v1/admin/stats`
*   **Description**: Get platform-wide statistics.
*   **Authentication**: Admin required.
*   **Response**:
    ```json
    {
        "total_users": 100,
        "total_tenants": 50,
        "active_instances": 45,
        "total_revenue": 10000
    }
    ```

---

*(This is a sample of the API documentation. A complete document would cover all endpoints in detail.)*


