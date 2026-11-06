# Iron Frontier — Advanced Strategy Game (v2.0)

A deployable full-stack, turn-based strategy game. The browser client is built with React + Vite; a Python FastAPI service owns the game rules, combat calculations, movement validation, recruitment and enemy-turn logic.

This is an original fictional strategy game inspired by classic territory-control games. It does not reproduce World Conqueror 4's proprietary maps, art, scenarios or assets.

## Features

- 7 × 5 tactical theatre with cities, forests, mountains, rivers, plains and desert.
- Four unit classes: infantry, heavy tank, field artillery and recon vehicle.
- Server-validated movement with terrain movement costs and unit-specific ranges.
- Server-side combat, terrain defence, counter-fire, unit losses and veteran progression.
- Python enemy AI that attacks, advances and captures allied cities.
- Three operations with different starting conditions and victory objectives.
- Recruitment, requisition credits, city income, victory points and mission rewards.
- Browser save/restore. A saved campaign can be restored after a backend restart.
- Responsive command interface, mission briefing, dispatch log and server status.

## Project structure

```text
iron_frontier_advanced/
├── backend/
│   ├── engine.py            # Game state, rules, combat, AI and objectives
│   ├── main.py              # FastAPI REST endpoints
│   ├── requirements.txt
│   └── tests/test_engine.py
├── frontend/
│   ├── src/App.jsx          # React game interface and API client
│   ├── src/styles.css
│   ├── src/main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── vercel.json
├── render.yaml
├── .gitignore
└── README.md
```

## Run locally

You need **Python 3.10+** and **Node.js 18.18+** (Node 20 LTS recommended). Node.js includes npm.

### 1. Start the Python backend

Open a terminal in the project root:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again. Alternatively, skip activation and run `.venv\Scripts\python.exe -m pip install -r requirements.txt` followed by `.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`.

API health check: http://127.0.0.1:8000/health
Interactive API docs: http://127.0.0.1:8000/docs

### 2. Start the React frontend

Open a **second terminal** in the project root:

```bash
cd frontend
npm install
```

Create a file named `.env` inside `frontend` using `.env.example` as its template:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Then run:

```bash
npm run dev
```

Open the Vite URL shown in the terminal, usually http://localhost:5173.

## Deploy online for free-tier testing

The frontend and Python backend are separate services. Deploy both; Vercel does not run the Python FastAPI process as a persistent web server in this setup.

### A. Deploy the backend on Render

1. Push the entire project to a GitHub repository.
2. In Render, create **New → Blueprint** or a new **Web Service** from that repository.
3. If using a Web Service, set **Root Directory** to `backend`, **Build Command** to `pip install -r requirements.txt`, **Start Command** to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Deploy and copy the service URL, for example `https://your-api.onrender.com`.
5. Verify `https://your-api.onrender.com/health` returns `{"status":"ok",...}`.

### B. Deploy the frontend on Vercel

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to Vite, **Build Command** to `npm run build`, and **Output Directory** to `dist`.
4. Add environment variable `VITE_API_URL` with your deployed Render service URL (no trailing slash).
5. Deploy. If you change the environment variable later, redeploy the frontend.

The `frontend/vercel.json` file provides the SPA fallback. In Vercel, set the project root directory to `frontend` and use the Vite settings above. You may also deploy from a separate frontend repository if preferred.

## Save behaviour and free-hosting limitations

- Campaign snapshots are saved in the user's browser using localStorage. The backend holds active game sessions in memory.
- If the backend restarts or a free host suspends the service, restore the campaign from the browser save. The game client sends the saved state to the API restore endpoint.
- Free hosting providers can have cold starts, usage limits, and changing plan restrictions. Check the provider's current pricing and sleep policies before relying on continuous availability.
- CORS is open for this prototype. For a public production launch, restrict `allow_origins` in `backend/main.py` to the exact deployed frontend domain and add authentication, request validation, rate limits and persistent database storage.

## Run backend tests

From the `backend` directory, install the backend requirements and run:

```bash
python -m unittest discover -s tests -v
```

## Gameplay

1. Select an allied unit on the map.
2. Green-highlighted tiles are legal moves; red-highlighted hostile units are legal attack targets.
3. Capture an empty city by moving onto it.
4. To recruit, select an unoccupied allied city and use the recruitment panel.
5. End your turn. Hostile AI acts, city income is paid, and allied units refresh their orders.
6. Save and restore from the header controls.

## Important scope notes

This is an advanced playable prototype, not a complete commercial-scale World Conqueror 4 equivalent. It uses a fictional grid map and a tactical turn system. It does not yet include a global geographic map, animated 3D units, historical campaign database, multiplayer, user accounts, cloud database, sound design or a sophisticated strategic planner. The backend AI is heuristic and can be improved in later versions.
