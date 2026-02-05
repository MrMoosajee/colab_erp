# Colab ERP

## Overview

Colab ERP is an Enterprise Resource Planning (ERP) system designed for Colab. It is a Streamlit application with a PostgreSQL backend.

## Features

*   **Multi-Tenancy Support**: Supports multiple tenants (TECH/TRAINING) while maintaining global exclusion constraints.
*   **Database-Backed Authentication**: Uses bcrypt for secure, database-backed authentication.
*   **Comprehensive Error Handling**: Robust error handling across all views.
*   **ACID Compliant**: All changes preserve strict ACID compliance.
*   **Calendar View**: Shows room bookings.
*   **Admin Dashboard**: Displays key performance indicators (KPIs).

## Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: Python
*   **Database**: PostgreSQL
*   **Authentication**: bcrypt

## Getting Started

### Prerequisites

*   Python 3
*   PostgreSQL
*   [Tailscale](https://tailscale.com/) (for remote access)

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd colab_erp
    ```

2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up the database:
    *   Make sure you have a PostgreSQL server running.
    *   Apply the database migrations:
        ```bash
        psql -h <host> -U <user> -d <database> -f migrations/v2.2_add_tenancy.sql
        ```

4.  Run the application:
    ```bash
    streamlit run src/app.py
    ```

## Project Structure

```
.
├── .streamlit/       # Streamlit configuration
├── files/            # Miscellaneous files
├── infra/            # Infrastructure-related files
├── migrations/       # Database migrations
├── src/              # Source code
│   ├── app.py        # Streamlit frontend
│   ├── auth.py       # Authentication logic
│   └── db.py         # Database logic
├── venv/             # Python virtual environment
├── .gitignore
├── HANDOVER_v2.2.md  # Handover document
└── requirements.txt  # Python dependencies
```

## Contributing

Please read the `HANDOVER_v2.2.md` file for details on the project's history, architecture, and development process.
