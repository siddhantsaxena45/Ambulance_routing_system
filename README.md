# Hybrid Soft Computing Framework for Real-Time Ambulance Routing

This project implements an intelligent system for real-time ambulance routing using Genetic Algorithms (GA), Artificial Neural Networks (ANN), and Fuzzy Logic.

## Prerequisites
- Python 3.9+
- Node.js 18+

## Backend Setup
It is highly recommended to use a Python virtual environment to manage dependencies.

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

## Frontend Setup
The frontend uses standard Node.js package management. You do not need a virtual environment, but you must install the NPM packages.

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install the necessary dependencies (Node modules):
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```

## Usage
- Open `http://localhost:5173` in your browser.
- The system will automatically download the map for "Noida Sector 62, UP, India" on the first load (this may take a few seconds).
- Adjust the **Emergency Urgency** slider.
- Click **"Find Optimal Route"** to run the Genetic Algorithm and Dijkstra Baseline.
- The GA route will be drawn in solid blue, and the Baseline route in dashed gray.
- Click **"Simulate New Traffic"** to randomize traffic and road blockages, then route again to see the dynamic behavior.
