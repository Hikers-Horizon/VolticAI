# Premium AI Intraday Trading Platform

A production-grade AI-powered intraday trading platform for the Indian stock market with Bloomberg Terminal quality and Apple-level minimalism.

## Features

- **AI-Powered Signals**: Advanced AI analysis with 75%+ confidence recommendations
- **Multi-Broker Support**: Dhan, Angel One, Zerodha, Upstox
- **Real-time Data**: WebSocket-based live market data streaming
- **Technical Analysis**: 14+ indicators including EMA, RSI, MACD, Supertrend, VWAP
- **Paper Trading**: Safe simulation mode by default
- **Trading Journal**: Track performance and emotions
- **Backtesting**: Test strategies on historical data
- **Premium UI**: Black & white minimal design with glassmorphism

## Tech Stack

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL (Database)
- Redis (Caching & WebSocket)
- SQLAlchemy (ORM)
- Pandas/NumPy (Data analysis)

### Frontend
- Next.js 14 (React)
- TypeScript
- TailwindCSS
- ShadcN UI Components
- Lightweight Charts (TradingView)
- Framer Motion (Animations)

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   ├── brokers/     # Broker integrations
│   │   ├── ai/          # AI engine
│   │   └── indicators/  # Technical indicators
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # App router
│   │   ├── components/ # UI components
│   │   ├── lib/        # Utilities
│   │   └── hooks/      # React hooks
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Development Setup

1. Clone the repository
2. Set up backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Configure .env with your settings
   uvicorn app.main:app --reload
   ```

3. Set up frontend:
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Setup

```bash
docker-compose up --build
```

## Configuration

### Broker API Setup
1. Enable paper trading mode (default)
2. Connect your broker account (optional)
3. Configure API keys in Settings

### Supported Markets
- NSE Stocks
- NIFTY Index
- BANKNIFTY Index
- FINNIFTY Index

## Safety & Disclaimer

⚠️ **Important**: AI recommendations are probabilistic and not guaranteed. This platform is for educational and research purposes. Trade at your own risk. Past performance does not guarantee future results.

Default mode is **Paper Trading**. Live trading requires explicit activation and broker connection.

## License

Proprietary - All Rights Reserved
