# CloudForge — Internal Developer Platform (IDP)

> **Enterprise Multi-Cloud Infrastructure Provisioner, Architecture Advisor & FinOps Arbitrage Platform**

CloudForge is a production-grade Internal Developer Platform built with **FastAPI** (Python backend), **React & TypeScript** (Frontend with modern dark enterprise styling), and **Terraform** (Infrastructure as Code). It provides automated infrastructure provisioning, rule-based architecture recommendations, multi-cloud cost modeling & arbitrage across AWS, Azure, and Google Cloud, live CloudWatch observability, and resource inventory discovery.

---

## Key Highlights

- **Multi-Cloud FinOps Arbitrage (Option A)**:
  - Direct on-demand cost comparison between **AWS**, **Microsoft Azure**, and **Google Cloud Platform (GCP)**.
  - Identifies cheapest cloud providers and calculates monthly/annual arbitrage savings.
  - Architecture equivalence mapping (e.g. AWS EC2 ↔ Azure Virtual Machines ↔ GCP Compute Engine).
- **Automated Infrastructure Provisioning (Terraform)**:
  - Guided wizard for VPC, EC2, S3, RDS (PostgreSQL/MySQL), and IAM.
  - Generates sanitized, valid HCL; performs isolated `terraform validate` and `terraform plan`.
  - Security guardrails & cost estimations before apply.
  - Mandatory confirmation phrase (`CONFIRM` for apply, `DESTROY` for teardown).
  - Background execution worker with live log terminal and automatic secret redaction (`AKIA*`, `ASIA*`, passwords).
- **Rule-Based Architecture Advisor**:
  - 5-step interactive questionnaire covering workload type, concurrent users, traffic patterns, sizing, databases, SLA, and budget.
  - Sizing logic calculates required vCPUs, RAM, storage, network bandwidth, and HA tier.
  - Downloadable multi-page PDF executive reports generated with ReportLab.
- **Security & Cross-Account Access Model**:
  - Zero static AWS keys stored or requested.
  - AWS STS cross-account `AssumeRole` with unique `ExternalId` (prevents confused deputy attacks).
  - Least-privilege IAM policy generator for read-only discovery and template-scoped provisioning.
  - Built-in Demo Sandbox mode for complete exploration without live AWS billing.
- **Resource Inventory & Telemetry**:
  - Live discovery of EC2, RDS, VPCs, and S3 resources with status tags and management attribution.
  - Real CloudWatch metrics overview (CPU, Network In/Out, RDS DB Connections) with honest data attribution.

---

## Project Structure & File Locations

```
cloudforge/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dashboard.py         # Summary metrics & recent operations
│   │   │   ├── provisioning.py      # Terraform plan, apply, destroy, log stream
│   │   │   ├── advisor.py           # Questionnaire & architecture recommendation
│   │   │   ├── reports.py           # Downloadable PDF report endpoint
│   │   │   ├── pricing.py           # Single-cloud & multi-cloud arbitrage calculator
│   │   │   ├── aws_account.py       # STS AssumeRole & connection management
│   │   │   ├── inventory.py         # Cloud resource inventory
│   │   │   └── monitoring.py        # Telemetry & CloudWatch metrics
│   │   ├── core/
│   │   │   ├── config.py            # App settings & CORS configuration
│   │   │   ├── security.py          # Input sanitizer & secret redactor
│   │   │   └── audit.py             # Event audit logger
│   │   ├── schemas/                 # Pydantic v2 validation models
│   │   │   ├── advisor.py
│   │   │   ├── aws.py
│   │   │   ├── inventory.py
│   │   │   ├── monitoring.py
│   │   │   ├── pricing.py           # MultiCloudCostComparison & ProviderCostBreakdown
│   │   │   └── provisioning.py
│   │   ├── services/
│   │   │   ├── advisor_engine.py    # Rule-based sizing & multi-cloud equivalence
│   │   │   ├── aws_service.py       # STS AssumeRole & CloudWatch client
│   │   │   ├── pdf_generator.py     # ReportLab multi-page PDF builder
│   │   │   ├── pricing_service.py   # AWS, Azure, GCP reference catalog & arbitrage engine
│   │   │   └── terraform_service.py # HCL templates & isolated background runner
│   │   └── main.py                  # FastAPI application & static asset mount
│   ├── tests/
│   │   ├── test_advisor.py          # Sizing, rules & PDF test
│   │   ├── test_pricing.py          # Multi-cloud arbitrage & cost calculations
│   │   ├── test_terraform.py        # HCL generation, confirmation guard & secret redaction
│   │   └── test_api_integration.py  # API route tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # Context header & breadcrumbs
│   │   │   └── Sidebar.tsx          # Multi-cloud navigation & cloud status badges
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Overview & FinOps cards
│   │   │   ├── Provisioning.tsx     # Terraform wizard, live terminal & confirmation modals
│   │   │   ├── Advisor.tsx          # 5-step questionnaire & recommendations
│   │   │   ├── CostEstimation.tsx   # Multi-cloud FinOps modeler & arbitrage table
│   │   │   ├── ConnectAWS.tsx       # STS AssumeRole & IAM policy generator
│   │   │   ├── Inventory.tsx        # Resource table with filters
│   │   │   └── Monitoring.tsx       # Telemetry charts (SVG sparklines)
│   │   ├── services/
│   │   │   └── api.ts               # Typed API client
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript domain models
│   │   ├── App.tsx                  # Root router & global state
│   │   ├── main.tsx                 # React DOM mount
│   │   └── index.css                # Enterprise dark design system
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── README.md
```

---

## Prerequisites

1. **Python 3.10+** (Python 3.14 verified)
2. **Node.js 18+** & **npm**
3. **Terraform CLI** (Optional: falls back gracefully to high-fidelity isolated dry-run engine when CLI is not in system PATH).

---

## Quick Start & How to Run

### Step 1: Start Backend (FastAPI)

```powershell
cd C:\Users\MAYANK\.gemini\antigravity\scratch\cloudforge\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will start at `http://127.0.0.1:8000`:
- Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Probe: `http://127.0.0.1:8000/health`
- Production Web App: `http://127.0.0.1:8000/` (served directly from compiled frontend)

### Step 2: Start Frontend in Development Mode (Vite)

In a separate terminal:

```powershell
cd C:\Users\MAYANK\.gemini\antigravity\scratch\cloudforge\frontend
npm run dev
```

Open `http://localhost:5173` in your browser. All `/api` requests are automatically proxied to the backend on port 8000.

---

## Running the Automated Test Suite

### Run Backend Tests (Pytest)

```powershell
cd C:\Users\MAYANK\.gemini\antigravity\scratch\cloudforge\backend
python -m pytest tests -v
```

All 15 tests covering the architecture advisor, multi-cloud pricing calculations, Terraform HCL validation, and API routes pass in ~1.5 seconds.

### Build and Validate Frontend

```powershell
cd C:\Users\MAYANK\.gemini\antigravity\scratch\cloudforge\frontend
npm run build
```

Compiles all TypeScript and CSS into `dist/` with zero errors.

---

## Security Model

1. **Anti-Confused-Deputy Defense**:
   All cross-account role assumptions require an STS `ExternalId` unique to each tenant.
2. **Secrets Protection**:
   `core/security.py` redacts AWS credentials, temporary tokens (`ASIA*`), and database passwords across all API outputs and background command logs.
3. **Two-Factor Operator Safeguards**:
   - `terraform apply` requires explicit phrase entry (`CONFIRM`).
   - `terraform destroy` requires explicit phrase entry (`DESTROY`).
4. **State Isolation**:
   Every plan operates inside a dedicated, isolated subfolder under `.workspaces/`.
