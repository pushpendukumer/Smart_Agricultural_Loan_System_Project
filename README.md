# Smart Agricultural Loan System (SALS)

A Django-based agricultural loan management system with role-based access control, loan application processing, EMI calculations, and repayment tracking.

## Features

- **User Authentication**: Registration, login, logout with role-based access
- **User Roles**: Farmer, Bank Officer, Admin
- **Farmer Profile**: Land size, crop type, location, income, documents
- **Loan Management**: Apply for loans, EMI calculation, risk scoring
- **Loan Types**: Agricultural Equipment, Crop Loan, Farm Development
- **Repayment Tracking**: Record payments, view history
- **Dashboard**: Role-specific dashboards with statistics and charts
- **Admin Panel**: Custom Django admin with filters, search, inline views

## Requirements

- Python 3.8+
- Django 4.2

## Installation

### 1. Clone and Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin` to access the admin panel.

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn

gunicorn sals_project.wsgi:application --bind 0.0.0.0:8000
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Django secret key | Generated |
| DEBUG | Debug mode | False |
| ALLOWED_HOSTS | Comma-separated hosts | localhost,127.0.0.1 |
| EMAIL_HOST | SMTP host | smtp.gmail.com |
| EMAIL_PORT | SMTP port | 587 |
| EMAIL_HOST_USER | Email username | - |
| EMAIL_HOST_PASSWORD | Email password | - |

## Project Structure

```
Smart_Agricultural_Loan_System/
├── sals_project/          # Django project settings
├── loan_app/             # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── forms.py          # Django forms
│   ├── admin.py          # Admin configuration
│   ├── urls.py           # URL routing
│   └── templatetags/     # Custom template filters
├── templates/            # HTML templates
├── static/               # Static files
├── media/                # User uploads
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Default Loan Types

The system comes with pre-configured loan types:
- Agricultural Equipment Loan (8.5% interest, max $50,000)
- Crop Loan (6.0% interest, max $25,000)
- Farm Development Loan (7.5% interest, max $100,000)

## License

MIT License
