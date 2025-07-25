# Kale - Enterprise Email API Platform

**Open Source Email API Platform by [Pradyumn Tandon](https://pradyumntandon.com)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

A professional email API service that allows users to send emails through their configured SMTP servers with comprehensive template management, API access, and advanced analytics.

## 🚀 Features

### Core Functionality
- **User Management**: Secure registration, authentication with JWT tokens
- **SMTP Integration**: Support for any SMTP provider (Gmail, SendGrid, AWS SES, custom servers)
- **Template Engine**: Rich HTML email templates with variable substitution
- **API Access**: RESTful API with personal endpoint structure
- **Rate Limiting**: Configurable limits (1k emails/day for unverified, unlimited for verified users)
- **Admin Dashboard**: Comprehensive system monitoring and user management
- **Progressive Web App**: PWA support for mobile-first experience

### Enterprise Security
- **JWT Authentication**: Secure token-based authentication
- **Password Encryption**: bcrypt hashing with configurable rounds
- **API Key Management**: Secure API key generation and validation
- **Rate Limiting**: Redis-based rate limiting and throttling
- **Input Sanitization**: XSS and injection attack prevention
- **CORS Configuration**: Secure cross-origin resource sharing

### Technical Excellence
- **Modern Architecture**: FastAPI + SQLite/PostgreSQL + Redis
- **Responsive UI**: Tailwind CSS with vanilla JavaScript
- **Real-time Updates**: WebSocket support for live statistics
- **Monitoring**: Health checks and performance metrics
- **Logging**: Structured logging with rotation
- **Caching**: Redis-based caching for optimal performance

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Frontend      │    │    Backend       │    │   External       │
│                 │    │                  │    │                  │
│ • HTML/CSS/JS   │◄──►│ • FastAPI        │◄──►│ • SMTP Servers   │
│ • Tailwind CSS  │    │ • SQLite/PgSQL   │    │ • Redis Cache    │
│ • PWA Support   │    │ • Redis Cache    │    │ • Email Providers│
│ • Responsive    │    │ • JWT Auth       │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## 🔗 API Structure

```
https://your-domain.com/{username}/{template_id}
```

Example: `https://kale.kanopus.org/johndoe/welcome-email`

## 🛠️ Tech Stack

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **Cache**: Redis
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Authentication**: JWT tokens, bcrypt
- **Email**: SMTP with connection pooling
- **Monitoring**: Prometheus metrics, structured logging

## 📦 Quick Setup

### Prerequisites
- Python 3.8 or higher
- Redis server (optional but recommended)
- SMTP server credentials

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Kanopusdev/Kale.git
cd Kale
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

6. **Access the application**
- Main Interface: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- Admin Panel: http://localhost:8000/admin
- API Documentation: http://localhost:8000/docs

### Demo Credentials
For testing purposes, you can use these demo credentials:
- **Email**: demo@kanopus.org
- **Password**: Demio@2025

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | Random generated |
| `DATABASE_URL` | Database connection string | `sqlite:///./kale.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DEBUG` | Debug mode | `false` |
| `DOMAIN` | Application domain | `localhost` |
| `ADMIN_EMAILS` | Admin email addresses | None |
| `ALLOWED_ORIGINS` | CORS allowed origins | Local hosts |

See `.env.example` for complete configuration options.

## 📚 API Documentation

### Authentication
```bash
# Register user
POST /api/v1/auth/register
{
  "username": "johndoe",
  "email": "john@example.com", 
  "password": "SecurePassword123!"
}

# Login
POST /api/v1/auth/login
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

### Email Sending
```bash
# Send email via API
POST /api/v1/email/send
Authorization: Bearer <token>
{
  "template_id": "welcome-email",
  "recipient_email": "user@example.com",
  "variables": {
    "name": "John Doe",
    "company": "Acme Corp"
  }
}
```

### Personal API Endpoint
```bash
# Send via personal endpoint
POST /johndoe/welcome-email
{
  "recipient_email": "user@example.com",
  "variables": {
    "name": "John Doe"
  }
}
```

## 🏭 Production Deployment

### Docker Deployment
```bash
docker build -t kale-email-api .
docker run -d -p 8000:8000 --env-file .env kale-email-api
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure Redis server
3. Set environment variables for production
4. Use gunicorn or uvicorn for WSGI server
5. Set up reverse proxy (nginx)
6. Configure SSL certificates

See `DEPLOYMENT.md` for detailed production setup instructions.

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run authentication tests
python test_auth.py
```

## 📊 Monitoring

- **Health Check**: `/health`
- **Metrics**: Prometheus metrics on `/metrics`
- **Admin Dashboard**: System monitoring and user management
- **Logging**: Structured JSON logging with rotation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Pradyumn Tandon** ([@Gamecooler19](https://github.com/Gamecooler19))
- Website: [pradyumntandon.com](https://pradyumntandon.com)
- GitHub: [@Gamecooler19](https://github.com/Gamecooler19)

## 🏢 Organization

**Kanopus** - Open Source Software Development
- Website: [kanopus.org](https://kanopus.org)
- GitHub: [@Kanopusdev](https://github.com/Kanopusdev)

## 🙏 Acknowledgments

- FastAPI framework for the excellent async web framework
- Tailwind CSS for the utility-first CSS framework
- Redis for high-performance caching
- All contributors and the open-source community

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/Kanopusdev/Kale/wiki)
- **Issues**: [GitHub Issues](https://github.com/Kanopusdev/Kale/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kanopusdev/Kale/discussions)
- **Email**: support@kanopus.org

---

⭐ **Star this repository if you find it helpful!**
