# MEDIXA PHARMA — Pharmacy Inventory Management System

A production-oriented pharmacy inventory management system developed for a private business.

The application provides a web-based interface for managing medicines, purchases, sales, inventory balances, profit calculations, manufacturing and expiry information, user authentication, and database-backed operations.

> **Project Note:** The client's production environment and business data are maintained separately and are not included in this public repository.

## Project Overview

MEDIXA PHARMA provides a centralized interface for managing pharmacy inventory and day-to-day stock transactions.

The system was developed with a focus on practical business requirements, reliable inventory calculations, database integration, and maintainable application structure.

## Core Features

- User registration and login
- Password hashing
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
- Inventory dashboard
- Responsive web interface
- SQLite support for local development
- PostgreSQL support for production environments

## Technology Stack

### Backend

- Python
- Flask
- Jinja2
- Gunicorn
- Waitress

### Database

- SQLite
- PostgreSQL
- psycopg

### Frontend

- HTML5
- CSS3
- JavaScript

### Development & Deployment

- Git
- GitHub
- Railway
- Neon PostgreSQL

## Application Architecture

```text
User
 |
 v
Web Browser
 |
 v
Flask Application
 |
 +-- Authentication
 +-- Medicine Management
 +-- Purchase Management
 +-- Sales Management
 +-- Inventory Management
 +-- Profit / Expiry Tracking
 |
 v
Database
```

The application uses environment-based database configuration so that local development and production environments can use different database systems without changing the application code.

### Local Development

```text
Local Computer
      |
      v
Flask Application
      |
      v
SQLite Database
```

### Production Environment

```text
Cloud Hosting
      |
      v
Flask Application
      |
      v
PostgreSQL Database
```

The production environment is maintained separately from this public repository.

## Engineering Highlights

### Inventory Management

The application processes purchase and sale transactions and updates available medicine stock accordingly.

### Profit Calculation

Purchase price, selling price, unit profit, quantity, and transaction-level profit are tracked to provide useful business information.

### Authentication

Users can create accounts and authenticate through the application. Passwords are stored using password hashing rather than plain text.

### Database Flexibility

The application supports SQLite during local development and PostgreSQL in production through environment-based database configuration.

### Production Configuration

Sensitive configuration values such as database credentials and application secrets are stored outside source control through environment variables.

## Screenshots

Screenshots of the application's main interfaces are included in the `screenshots/` directory.

The screenshots demonstrate areas such as:

- Dashboard
- Inventory
- Purchase management
- Sales management
- Transactions
- Medicine details
- Authentication
- Expiry management

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
- Migration from local SQLite development to PostgreSQL production

## Demo

A public interactive demo is not currently provided.

The production application is privately operated for the client and is not exposed through this portfolio repository because it contains private business data and production configuration.

The screenshots and documentation in this repository provide an overview of the application's functionality and implementation.

## Project Structure

```text
MEDIXA-PHARMA-PORTFOLIO/
|
+-- app.py
+-- requirements.txt
+-- wsgi.py
+-- README.md
+-- .env.example
+-- .gitignore
|
+-- static/
|   +-- app.js
|   +-- style.css
|   +-- medixa_logo.png
|
+-- templates/
|   +-- add_medicine.html
|   +-- auth_base.html
|   +-- base.html
|   +-- edit_medicine.html
|   +-- expiry.html
|   +-- forgot_password.html
|   +-- home.html
|   +-- inventory.html
|   +-- login.html
|   +-- medicine_details.html
|   +-- purchase.html
|   +-- register.html
|   +-- reset_password.html
|   +-- sell.html
|   +-- transactions.html
|
+-- screenshots/
```

## Running Locally

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file based on `.env.example`, configure the application for local development, and run:

```bash
python app.py
```

The application can then be accessed through the local Flask development server.

## Development Notes

The public repository is intended to demonstrate the technical implementation and development work behind the project.

Client-specific production credentials, private business information, and production database data are intentionally excluded.

## Future Improvements

Potential future enhancements include:

- Batch-level inventory management
- FEFO-based stock handling
- Inventory reporting and exports
- Audit logging
- Role-based access control
- Automated database backups
- Enhanced reporting and analytics

## Author

**Rubab Majid**

Software Engineering Student

**Skills:** Python, Flask, PostgreSQL, SQL, HTML, CSS, JavaScript, Web Development