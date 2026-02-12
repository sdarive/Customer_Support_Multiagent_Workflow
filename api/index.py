from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
from google.oauth2 import service_account
from agents.coordinator import TicketCoordinator

app = FastAPI()

# --- Configuration & Credentials ---
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")

print(f"DEBUG: Vercel Environment Check")
print(f"DEBUG: PROJECT_ID exists: {bool(PROJECT_ID)}")
print(f"DEBUG: API_KEY exists: {bool(API_KEY)}")
print(f"DEBUG: GCP_SA_KEY exists: {bool(GCP_SA_KEY)}")


# Initialize credentials if provided
if GCP_SA_KEY:
    try:
        # Create a temporary file for the credentials so libraries can find it
        # This is a common pattern for serverless environments
        with open("/tmp/gcp_key.json", "w") as f:
            f.write(GCP_SA_KEY)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
    except Exception as e:
        print(f"Error handling GCP_SA_KEY: {e}")

# Lazy initialization of the coordinator
coordinator = None
def get_coordinator():
    global coordinator
    if coordinator is None:
        if not PROJECT_ID:
            raise HTTPException(status_code=500, detail="GCP_PROJECT_ID environment variable not set")
        coordinator = TicketCoordinator(PROJECT_ID, api_key=API_KEY)
    return coordinator

# --- Data Models ---
class TicketRequest(BaseModel):
    description: str

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Support Ticket Router</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; }
            .gradient-text {
                background: linear-gradient(to right, #4285F4, #db4437, #f4b400, #0f9d58);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
        </style>
    </head>
    <body class="bg-slate-50 min-h-screen text-slate-800">
        <main class="max-w-4xl mx-auto px-4 py-12">
            <!-- Header -->
            <div class="text-center mb-12">
                <div class="inline-flex items-center justify-center p-2 bg-white rounded-full shadow-sm mb-4">
                    <span class="text-xs font-semibold tracking-wider uppercase px-2 text-slate-500">Enterprise AI Demo</span>
                </div>
                <h1 class="text-4xl md:text-5xl font-bold mb-4">Support Ticket <span class="gradient-text">Router</span></h1>
                <p class="text-lg text-slate-600 max-w-2xl mx-auto">
                    Experience proactive support automation. Our multi-agent system classifies, retrieves solutions, and routes tickets in milliseconds.
                </p>
            </div>

            <!-- Interactive Demo Area -->
            <div class="grid md:grid-cols-2 gap-8 items-start">
                
                <!-- Input Section -->
                <div class="bg-white rounded-2xl shadow-xl p-6 border border-slate-100">
                    <h2 class="text-xl font-semibold mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        Submit a Ticket
                    </h2>
                    <form id="ticketForm" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-slate-700 mb-1">Customer Issue</label>
                            <textarea id="description" rows="5" class="w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none" placeholder="e.g., I was charged twice for my subscription but the payment failed..."></textarea>
                        </div>
                        <div class="flex gap-2">
                            <button type="button" onclick="fillExample('billing')" class="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1 rounded-full transition-colors">Example: Billing</button>
                            <button type="button" onclick="fillExample('technical')" class="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1 rounded-full transition-colors">Example: Technical</button>
                        </div>
                        <button type="submit" id="submitBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-all shadow-md hover:shadow-lg flex items-center justify-center">
                            <span>Process Ticket</span>
                            <svg id="arrowIcon" class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                            <svg id="loadingIcon" class="hidden animate-spin ml-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        </button>
                    </form>
                </div>

                <!-- Results Section -->
                <div id="resultsCard" class="hidden bg-white rounded-2xl shadow-xl p-0 border border-slate-100 overflow-hidden">
                    <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                        <h2 class="text-sm font-semibold text-slate-500 uppercase tracking-wider">Analysis Result</h2>
                        <span id="latencyTag" class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">-- ms</span>
                    </div>
                    
                    <div class="p-6 space-y-6">
                        <!-- Classification -->
                        <div class="flex gap-4">
                            <div class="flex-1">
                                <span class="text-xs text-slate-400 block mb-1">Category</span>
                                <span id="resCategory" class="font-medium text-slate-800 capitalize bg-slate-100 px-2 py-1 rounded">--</span>
                            </div>
                            <div class="flex-1">
                                <span class="text-xs text-slate-400 block mb-1">Priority</span>
                                <span id="resPriority" class="font-medium text-slate-800 capitalize bg-slate-100 px-2 py-1 rounded">--</span>
                            </div>
                        </div>

                        <!-- Routing -->
                        <div class="bg-blue-50 rounded-lg p-4 border border-blue-100">
                            <div class="flex items-start">
                                <div class="flex-shrink-0">
                                    <svg class="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                                </div>
                                <div class="ml-3">
                                    <h3 class="text-sm font-medium text-blue-800">Routed to: <span id="resTeam" class="font-bold">--</span></h3>
                                    <div class="mt-1 text-sm text-blue-600">
                                        <p>SLA Target: <span id="resSLA" class="font-semibold">--</span> hours</p>
                                        <p id="resReason" class="text-xs mt-1 text-blue-400"></p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Solutions -->
                        <div>
                            <h3 class="text-sm font-medium text-slate-700 mb-2">Suggested Solutions (RAG)</h3>
                            <div id="solutionsList" class="space-y-2">
                                <!-- Solutions injected here -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Empty State -->
                <div id="emptyState" class="bg-white rounded-2xl shadow-sm p-8 border border-slate-100 text-center flex flex-col items-center justify-center h-full min-h-[400px]">
                    <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                        <svg class="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                    </div>
                    <h3 class="text-slate-500 font-medium">Ready to Analyze</h3>
                    <p class="text-slate-400 text-sm mt-1">Submit a ticket to see the AI agents in action.</p>
                </div>

            </div>
        </main>

        <script>
            function fillExample(type) {
                const examples = {
                    'billing': "My credit card was charged twice for the subscription. I need a refund immediately.",
                    'technical': "The export to CSV feature is throwing a 500 error every time I try to download the monthly report."
                };
                document.getElementById('description').value = examples[type] || "";
            }

            document.getElementById('ticketForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const desc = document.getElementById('description').value;
                if (!desc) return;

                // UI Loading State
                const btn = document.getElementById('submitBtn');
                const loadingIcon = document.getElementById('loadingIcon');
                const arrowIcon = document.getElementById('arrowIcon');
                btn.disabled = true;
                loadingIcon.classList.remove('hidden');
                arrowIcon.classList.add('hidden');
                
                // Hide old results
                document.getElementById('resultsCard').classList.add('hidden');
                document.getElementById('emptyState').classList.remove('hidden');

                try {
                    const start = Date.now();
                    const response = await fetch('/api/process-ticket', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ description: desc })
                    });
                    
                    const data = await response.json();
                    
                    if (!response.ok) {
                        const errorMsg = data.detail || (response.status === 404 ? "API Route Not Found (404)" : "Server Error");
                        throw new Error(errorMsg);
                    }

                    const latency = Date.now() - start;

                    // Populate UI
                    document.getElementById('latencyTag').textContent = `${latency} ms`;
                    document.getElementById('resCategory').textContent = data.classification.category;

                    document.getElementById('resPriority').textContent = data.classification.priority;
                    
                    // Color code priority
                    const p = data.classification.priority.toLowerCase();
                    const pEl = document.getElementById('resPriority');
                    pEl.className = `font-medium capitalize px-2 py-1 rounded ${
                        p === 'critical' ? 'bg-red-100 text-red-700' : 
                        p === 'high' ? 'bg-orange-100 text-orange-700' : 
                        'bg-blue-100 text-blue-700'
                    }`;

                    document.getElementById('resTeam').textContent = data.routing.assigned_team;
                    document.getElementById('resSLA').textContent = data.routing.sla_hours;
                    document.getElementById('resReason').textContent = data.routing.routing_reason;

                    const solutionsList = document.getElementById('solutionsList');
                    solutionsList.innerHTML = '';
                    if (data.suggested_solutions && data.suggested_solutions.length > 0) {
                        data.suggested_solutions.forEach(sol => {
                            const div = document.createElement('div');
                            div.className = 'p-3 bg-slate-50 rounded border border-slate-100 text-sm hover:border-blue-200 transition-colors cursor-default';
                            div.innerHTML = `
                                <div class="flex justify-between mb-1">
                                    <span class="font-medium text-slate-700">${sol.solution_id.substring(0,8)}...</span>
                                    <span class="text-xs text-green-600 bg-green-50 px-1.5 rounded">Success Rate: ${(sol.success_rate * 100).toFixed(0)}%</span>
                                </div>
                                <p class="text-slate-600 text-xs">${sol.solution_text}</p>
                            `;
                            solutionsList.appendChild(div);
                        });
                    } else {
                        solutionsList.innerHTML = '<p class="text-xs text-slate-400 italic">No historical solutions found.</p>';
                    }

                    // Show Results
                    document.getElementById('emptyState').classList.add('hidden');
                    document.getElementById('resultsCard').classList.remove('hidden');

                } catch (err) {
                    console.error(err);
                    alert(`${err.message}`);
                } finally {
                    btn.disabled = false;
                    loadingIcon.classList.add('hidden');
                    arrowIcon.classList.remove('hidden');
                }
            });
        </script>
    </body>
    </html>
    """
