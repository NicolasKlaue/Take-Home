# 🚀 Streamlit Secure App with SQLite

## 📖 Project Description

This project is a simple, production-ready **Streamlit web application** with:

* User authentication (login/logout)
* Secure password handling
* SQLite database integration
* Docker support for easy deployment
* Ready-to-deploy setup for Railway

It’s designed as a **minimal full-stack template** for building data-driven apps with authentication.

---

## ✨ Features

* 🔐 **User Authentication**

  * Login system with hashed passwords (`bcrypt`)
  * Session management using Streamlit

* 🗄️ **Database Integration**

  * SQLite database
  * User table + sample data table

* 📊 **Interactive Dashboard**

  * Personalized welcome message
  * Fetch and display data in a table

* 🐳 **Docker Support**

  * Lightweight production-ready Dockerfile
  * docker-compose for local development

* ☁️ **Cloud Deployment**

  * Optimized for Railway deployment

---

## 🛠️ Project Structure

```
.
├── app.py              # Main Streamlit app
├── auth.py             # Authentication logic
├── db.py               # Database access layer
├── init_db.sql         # Database initialization
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container setup
├── docker-compose.yml  # Local container orchestration
└── .env                # Environment variables
```

---

## ⚙️ Setup Instructions

### ✅ 1. Local Setup (Without Docker)

#### Step 1: Clone the repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

#### Step 2: Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

#### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Configure environment variables

Create a `.env` file:

```
DATABASE_PATH=./database.db
SECRET_KEY=your-secret-key
```

#### Step 5: Initialize the database

```bash
sqlite3 database.db < init_db.sql
```

#### Step 6: Run the app

```bash
streamlit run app.py
```

App will be available at:

```
http://localhost:8501
```

---

### 🐳 2. Run with Docker

#### Step 1: Build and start containers

```bash
docker-compose up --build
```

#### Step 2: Open in browser

```
http://localhost:8501
```

---

## ☁️ Deploy on Railway

### Step 1: Create a Railway project

* Go to Railway
* Click **New Project**
* Select **Deploy from GitHub**

### Step 2: Connect your repository

### Step 3: Add Environment Variables

In Railway dashboard → Variables tab:

```
DATABASE_PATH=/app/database.db
SECRET_KEY=your-secret-key
```

### Step 4: Deploy

Railway will:

* Build using the `Dockerfile`
* Expose port `8501`
* Start the Streamlit app automatically

---

## 🔑 Environment Variables

| Variable        | Description                         | Example            |
| --------------- | ----------------------------------- | ------------------ |
| `DB_PATH` | Path to SQLite database file        | `./database.db`    |
| `SECRET_KEY`    | Secret key for session/security use | `super-secret-key` |

### Notes:

* In Docker/Railway, paths should be **inside the container** (e.g. `/app/database.db`)
* Keep `SECRET_KEY` private in production

---

## 🔒 Default Credentials

After initializing the database:

```
Username: admin
Password: (as defined in init_db.sql)
```

---

## 🧩 Future Improvements

* User registration page
* Password reset functionality
* Role-based access control
* PostgreSQL support
* API layer (FastAPI)

---

## 📜 License

This project is open-source and free to use.

---

If you want, I can also generate a **GitHub-ready version with badges and screenshots** or tailor it for your CV/portfolio.
