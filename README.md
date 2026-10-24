# 🌾 AgriVersion - AI-Powered Multilingual Rice Leaf Disease Detection & Farm Advisory

AgriVersion is an intelligent, full-stack agricultural decision-support platform designed to detect and diagnose rice leaf diseases using deep learning, assess severity, generate downloadable diagnostic reports, and provide multilingual organic/chemical treatment advisories for farmers.

---

## 🌟 Key Features

- **🔬 20 Disease & Health Classifications**: Powered by PyTorch (`RiceNet`) to identify diseases including Bacterial Leaf Blight, Rice Blast, Brown Spot, Sheath Blight, Tungro, and more.
- **🌐 Multilingual Support**: Farmer-friendly translations across multiple regional and global languages.
- **📄 Automated PDF Reports**: Instant generation of comprehensive diagnostic reports with treatment schedules, severity ratings, and farm details.
- **👥 Role-Based Access Control**:
  - **👨‍🌾 Farmer Portal**: Scan leaves, view disease history, download PDF advisory reports, and track crop health.
  - **👤 Admin Dashboard**: Analytics, disease outbreak heatmaps, user management, and system logs.
- **🛡️ Blur & Quality Validation**: Built-in image pre-validation ensures submitted leaf images are clear and suitable for model inference.

---

## 📂 Project Structure

```text
├── backend/                  # Flask REST API and core business logic
│   ├── app.py                # Flask app factory and initialization
│   ├── config.py             # App configuration and environment loading
│   ├── database/             # Database models and session management
│   ├── routes/               # Modular API and view blueprints
│   ├── services/             # Report generation, notification, and analytics services
│   └── utils/                # Image validation and helper utilities
├── frontend/                 # Web interface (HTML5, CSS3, JavaScript)
├── ml/                       # Machine learning inference pipelines
├── models/                   # PyTorch weights (ricenet_weights.pth) & class mapping
├── static_reports/           # Generated PDF diagnostic reports storage
├── translations/             # Multilingual locale JSON files
├── uploads/                  # Temporary image uploads
├── requirements.txt          # Python project dependencies
├── run.py                    # Application entry point
└── .env.example              # Environment variables template
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9+ or Python 3.10+
- Git

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 3. Create a Virtual Environment

```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` to configure optional AI Multimodal API keys (Gemini / Groq), database URI (SQLite by default), and secret keys.

### 6. Run the Application

```bash
python run.py
```

The application will launch at:
👉 **`http://127.0.0.1:5000`**

#### Default Test Accounts:
- **Admin**: `admin@agriversion.com` / `Admin@123`
- **Farmer**: `farmer@agriversion.com` / `Farmer@123`

---

## 🦠 Detected Diseases (20 Classes)

1. Healthy Rice Leaf
2. Brown Spot
3. Leaf Smut
4. Bacterial Leaf Blight
5. Rice Blast
6. Sheath Blight
7. False Smut
8. Tungro
9. Bacterial Leaf Streak
10. Sheath Rot
11. Narrow Brown Leaf Spot
12. Rice Hispa
13. Bacterial Panicle Blight
14. Bakanae
15. Stem Borer Damage
16. Rice Grassy Stunt
17. Rice Ragged Stunt
18. Dirty Panicle
19. Kernel Smut
20. Udbatta Disease

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
