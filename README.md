# MEDIXA PHARMA — Pharmacy Inventory Management System

A production-oriented pharmacy inventory management system developed for a private business.

The system is designed to manage medicines, purchasing, sales, inventory balances, profit calculations, manufacturing and expiry information, user authentication, and database-backed operations through a web-based interface.

> **Portfolio Notice:** This repository is a recruiter-safe portfolio version. The actual client's production repository and business data are kept private.

## Project Overview

MEDIXA PHARMA provides a centralized interface for managing pharmacy inventory and daily stock transactions.

### Core Features

- User registration and login
- Secure password hashing
- Password reset workflow
- Medicine management
- Medicine type classification
- Purchase management
- Sales management
- Automatic inventory balance updates
- Purchase and selling price tracking
- Unit and total profit calculation
- Manufacturing date tracking
- Expiry date tracking
- Medicine details
- Inventory management dashboard
- Responsive web interface
- PostgreSQL production database support
- SQLite local-development support
- Production deployment with Railway

## Technology Stack

**Backend**
- Python
- Flask
- Waitress / Gunicorn

**Database**
- SQLite for local development
- PostgreSQL for production
- psycopg

**Frontend**
- HTML5
- CSS3
- JavaScript
- Jinja2 templates

**Deployment**
- GitHub
- Railway
- Neon PostgreSQL

**Security**
- Password hashing
- Environment-based secrets
- Secure session configuration
- Production database credentials kept outside source control

## System Architecture

```text
User
  │
  ▼
Web Browser
  │
  ▼
Flask Application
  │
  ├── Authentication
  ├── Medicine Management
  ├── Purchase Management
  ├── Sales Management
  ├── Inventory Management
  └── Profit / Expiry Tracking
  │
  ▼
PostgreSQL Database
```

## Development Architecture

Local development uses SQLite so the application can be tested without requiring an external database.

```text
Local Computer
      │
      ▼
Flask Application
      │
      ▼
SQLite
```

The production deployment uses PostgreSQL:

```text
GitHub
   │
   ▼
Railway
   │
   ▼
Flask Application
   │
   ▼
Neon PostgreSQL
```

## Engineering Highlights

### Inventory Management

The application maintains medicine stock by processing purchase and sale transactions and updating available inventory accordingly.

### Profit Calculation

The system tracks purchase price, selling price, unit profit, and transaction-level profit to provide useful business information.

### Authentication

Users can create accounts and authenticate through the application. Passwords are stored using secure password hashing rather than plain text.

### Database Flexibility

The application supports SQLite during development and PostgreSQL in production through environment-based database configuration.

### Production Deployment

The application has been deployed as a live Flask web application using Railway with Neon PostgreSQL as the persistent production database.

## Screenshots

Screenshots can be added to the `screenshots/` directory to demonstrate the dashboard, inventory, purchase, sales, authentication, and other interfaces.

## My Role

I designed and developed the application with a focus on:

- Backend development
- Flask application structure
- Database design and integration
- Authentication
- Inventory and transaction logic
- Profit calculation
- Responsive user interface
- Production configuration
- Cloud deployment
- Database migration from local SQLite to PostgreSQL

## Live Demo

The production application is privately operated for the client.

[Open MEDIXA PHARMA Production Application](https://medixa-pharma-production-production.up.railway.app)

## Portfolio Note

This public repository is intended to demonstrate my software engineering work while protecting the client's private source code, business information, credentials, and production data.

The production repository is maintained separately as a private repository.

## Author

**Rubab Majid**

Software Engineering Student  
Python • Flask • PostgreSQL • Web Development