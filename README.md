# AS400 API Wrapper

A lightweight FastAPI-based project that helps expose IBM i (AS400) programs and data as REST APIs. Ideal for organizations looking to modernize without rewriting core RPGLE/CL programs.

## 🚀 Purpose
This project bridges legacy IBM i logic with modern RESTful APIs. It helps:
- Expose RPGLE programs as endpoints
- Connect DB2 tables to cloud/web systems
- Serve as a modernization bridge between green-screen systems and modern UIs

## 👨‍💻 Who is this for?
- IBM i developers integrating with web frontends
- Backend engineers needing to call IBM i logic
- Teams modernizing AS400 without full migration

## 🧩 Use Cases
- Inventory or order APIs from RPGLE
- Bridge IBM i to cloud dashboards
- Secure access to AS400 data from mobile apps

## 🧱 Folder Structure

```
as400-api-wrapper/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   └── as400_bridge.py
│   └── models/
│       └── request.py
├── scripts/
│   └── call_rpgle.py
├── tests/
├── requirements.txt
└── README.md
```

