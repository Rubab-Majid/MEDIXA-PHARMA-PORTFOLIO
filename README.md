# MEDIXA PHARMA — Pharmacy Inventory Management System



A production-oriented pharmacy inventory management system developed for a private business.



The application provides a web-based interface for managing medicines, purchases, sales, inventory balances, profit calculations, manufacturing and expiry information, and user authentication.



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

&#x20; Ã¢â€â€š

&#x20; Ã¢â€“Â¼

Web Browser

&#x20; Ã¢â€â€š

&#x20; Ã¢â€“Â¼

Flask Application

&#x20; Ã¢â€â€š

&#x20; Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Authentication

&#x20; Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Medicine Management

&#x20; Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Purchase Management

&#x20; Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Sales Management

&#x20; Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Inventory Management

&#x20; Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Profit / Expiry Tracking

&#x20; Ã¢â€â€š

&#x20; Ã¢â€“Â¼

Database

```



The application uses environment-based database configuration so that local development and production environments can use different database systems without changing the application code.



### Local Development



```text

Local Computer

&#x20;     Ã¢â€â€š

&#x20;     Ã¢â€“Â¼

Flask Application

&#x20;     Ã¢â€â€š

&#x20;     Ã¢â€“Â¼

SQLite Database

```



### Production Environment



```text

Cloud Hosting

&#x20;     Ã¢â€â€š

&#x20;     Ã¢â€“Â¼

Flask Application

&#x20;     Ã¢â€â€š

&#x20;     Ã¢â€“Â¼

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

Ã¢â€â€š

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app.py

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ wsgi.py

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ README.md

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .env.example

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .gitignore

Ã¢â€â€š

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ static/

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app.js

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ style.css

Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ medixa_logo.png

Ã¢â€â€š

Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ templates/

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ add_medicine.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ auth_base.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ base.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ edit_medicine.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ expiry.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ forgot_password.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ home.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ inventory.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ login.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ medicine_details.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ purchase.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ register.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ reset_password.html

Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ sell.html

Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ transactions.html

Ã¢â€â€š

Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ screenshots/

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



**Skills:** Python Ã¢â‚¬Â¢ Flask Ã¢â‚¬Â¢ PostgreSQL Ã¢â‚¬Â¢ SQL Ã¢â‚¬Â¢ HTML Ã¢â‚¬Â¢ CSS Ã¢â‚¬Â¢ JavaScript Ã¢â‚¬Â¢ Web Development