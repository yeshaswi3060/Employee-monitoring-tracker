# Employee Monitoring Tracker

A **Windows-based employee monitoring tool** designed to track and log various activities on a system.  
It helps monitor productivity, system usage, and network activity, providing detailed insights for administrators.

---

## 🚀 Features

- **Activity Tracking** – Logs application usage and system activity.
- **App Usage Tracker** – Monitors which applications are opened and used.
- **Audio Monitoring** – Detects audio input/output activity.
- **File Transfer Monitoring** – Tracks file transfers for security and auditing.
- **Internet Monitoring** – Logs internet activity and network changes.
- **System Monitoring Dashboard** – A web interface to view logs and reports.
- **Cross-Module Logging** – Centralized logging of multiple trackers.

---

## 📂 Project Structure

\\\
Employee-monitoring-tracker/
│
├── templates/                 # HTML templates for the dashboard
├── LocalMonitorWeb.py         # Web interface script
├── activity_tracker.py        # Tracks active applications
├── app_usage_tracker.py       # Logs app usage data
├── audio_monitor.py           # Monitors audio events
├── build.py                   # Build script
├── check_network.py           # Tracks network connectivity
├── dashboard.spec             # PyInstaller spec file
├── file_transfer_monitor.py   # Monitors file transfers
├── internet_monitor.py        # Tracks internet activity
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
\\\

---

## 🔧 Installation

1. **Clone the repository**
   \\\ash
   git clone https://github.com/yeshaswi3060/Employee-monitoring-tracker.git
   cd Employee-monitoring-tracker
   \\\

2. **Create a virtual environment (Recommended)**
   \\\ash
   python -m venv venv
   venv\Scripts\activate   # On Windows
   \\\

3. **Install dependencies**
   \\\ash
   pip install -r requirements.txt
   \\\

4. **Run the main monitoring script**
   \\\ash
   python LocalMonitorWeb.py
   \\\

---

## 📊 Usage

- Open the local dashboard in your browser to view activity logs.
- Configure the scripts to start automatically on system startup for continuous tracking.
- Logs are stored locally in the project folder unless configured otherwise.

---

## ⚠ Disclaimer

This tool is intended **for authorized use only**.  
Make sure to comply with local laws and obtain **explicit consent** before monitoring any device.

---

## 📄 License

This project is licensed under the **MIT License** – feel free to modify and distribute it.
