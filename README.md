# 📧 Activity Alert System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Google Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Deployed-blue.svg)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automated email alert system that monitors Google Sheets activities and sends real-time notifications about task deadlines, delays, and completions.

---

## 🚀 Overview

The **Activity Alert System** is a production-ready solution that integrates with Google Sheets to track project activities and automatically send email alerts to team members. It monitors task start dates, due dates, and status changes, sending notifications for:

- 📋 **Starting tasks** - Alert when a task should begin today
- ⚠️ **Delayed tasks** - Notify when a task is past its due date
- ✅ **Completed tasks** - Congratulate when a task is marked as complete
- 📊 **Daily reports** - Send a consolidated summary to project coordinators

Built with **FastAPI** and designed to run serverlessly on **Google Cloud Run**, the system is cost-effective, scalable, and requires zero maintenance.

---

## ✨ Features

- 🔗 **Google Sheets Integration** - Reads activities and researcher data directly from your spreadsheets
- 📧 **Automated Email Alerts** - Sends beautifully formatted HTML emails via Gmail SMTP
- 🧪 **Test Mode** - Simulate email sending without actually delivering messages
- 📊 **Multi-Project Support** - Monitor multiple projects from a single instance
- 👥 **Multiple Assignees** - Supports multiple responsible persons per activity
- 🔄 **Smart Alert Logic** - Prevents duplicate alerts and respects completion status
- 🚀 **Cloud Native** - Designed for Google Cloud Run with auto-scaling and pay-per-use pricing
- 📖 **Interactive API Docs** - Full Swagger UI documentation at `/docs`
- 🐳 **Docker Ready** - Containerized for easy deployment anywhere

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Core programming language |
| **FastAPI** | Web framework for REST API |
| **gspread** | Google Sheets API integration |
| **Pydantic** | Data validation & serialization |
| **Uvicorn** | ASGI server |
| **Docker** | Containerization |
| **Google Cloud Run** | Serverless deployment |

---

## 📋 Prerequisites

- Python 3.11+
- Google Cloud Platform account (for deployment)
- Google Service Account with Sheets API enabled
- Gmail account with App Password configured
- Google Sheets with:
  - `ENTREGA DE ATIVIDADES` worksheet (activities)
  - `PESQUISADORES` worksheet (researchers)

---

## 🔧 Installation

### Local Development

#### Clone the repository
- git clone https://github.com/rudaaranha/email-automation.git
- cd email-automation

#### Create virtual environment
- python -m venv venv
- source venv/bin/activate  # On Windows: venv\Scripts\activate

#### Install dependencies
- pip install -r requirements.txt

#### Copy environment variables
- cp .env.example .env

- Edit .env with your credentials
- EMAIL_NATS=your_email@gmail.com
- PASSWORD_APP_NATS=your_app_password
- SPREADSHEET_ID_PROJECT01=your_sheet_id

- Run the application
python main.py
