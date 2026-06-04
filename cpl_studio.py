#!/usr/bin/env python3
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from cpl.core import CPLRequest
from cpl.validator import CPLValidator
from cpl.negotiator import CPLNegotiator, ModelManifest
from cpl.contract import CPLContractVerifier
from cpl.models import GeminiModel, CPLPromptCompiler
from cpl.extensions.legal import CPLLegalValidator

PORT = 8085

MOCK_MANIFESTS = {
    "gemini-2.5-flash": {
        "model_id": "gemini-2.5-flash",
        "capabilities": {
            "operations": ["ANALYZE", "SYNTHESIZE", "TRANSFORM", "VERIFY"],
            "domains": ["software_engineering", "analysis", "creative_content", "legal"],
            "structured_output": True
        },
        "constraints": {
            "context_window": 1000000
        }
    },
    "claude-3-5-sonnet": {
        "model_id": "claude-3-5-sonnet",
        "capabilities": {
            "operations": ["ANALYZE", "SYNTHESIZE", "TRANSFORM", "VERIFY"],
            "domains": ["software_engineering", "analysis", "legal"],
            "structured_output": True
        },
        "constraints": {
            "context_window": 200000
        }
    },
    "llama-3-1-8b": {
        "model_id": "llama-3-1-8b",
        "capabilities": {
            "operations": ["ANALYZE", "SYNTHESIZE", "TRANSFORM"],
            "domains": ["software_engineering", "analysis"],
            "structured_output": False
        },
        "constraints": {
            "context_window": 128000
        }
    }
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPL Studio · Cognitive Prompting Language</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #080B10;
        }
        .code-font {
            font-family: 'JetBrains Mono', monospace;
        }
        .glass {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glass-strong {
            background: rgba(10, 15, 26, 0.9);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body class="text-zinc-100 min-h-screen flex flex-col antialiased">

    <!-- Header -->
    <header class="border-b border-white/5 py-4 px-6 bg-zinc-950/80 backdrop-blur sticky top-0 z-50 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center font-black text-zinc-950 text-lg shadow-lg shadow-cyan-500/20">Ω</div>
            <div>
                <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                    CPL STUDIO <span class="text-[10px] font-black uppercase bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-1.5 py-0.5 rounded">v1.0.0 OpenSource</span>
                </h1>
                <p class="text-[10px] text-zinc-400">Cognitive Prompting Language Framework & Verification Engine</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 text-xs text-zinc-400">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Local Engine Active
            </div>
        </div>
    </header>

    <!-- Content -->
    <main class="flex-1 p-6 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
        
        <!-- Left Panel: Editor & Selection -->
        <div class="space-y-6 flex flex-col h-[calc(100vh-140px)]">
            
            <!-- Spec Selection -->
            <div class="glass p-4 rounded-xl space-y-3 shrink-0">
                <label class="text-xs font-bold text-zinc-400 uppercase tracking-wider block">1. Select standard CPL template</label>
                <div class="flex gap-2">
                    <button onclick="loadTemplate('legal')" id="btn-tmpl-legal" class="flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-cyan-600 text-white transition-all">
                        CPL-Legal (Contract Audit)
                    </button>
                    <button onclick="loadTemplate('code')" id="btn-tmpl-code" class="flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-zinc-900 text-zinc-400 hover:bg-zinc-800 transition-all">
                        CPL-Code (Algo Gen)
                    </button>
                    <button onclick="loadTemplate('creative')" id="btn-tmpl-creative" class="flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-zinc-900 text-zinc-400 hover:bg-zinc-800 transition-all">
                        CPL-Creative (Sci-Fi)
                    </button>
                </div>
            </div>

            <!-- Workspace Editor -->
            <div class="glass rounded-xl flex-1 flex flex-col overflow-hidden relative">
                <div class="bg-zinc-900/60 border-b border-white/5 px-4 py-2 flex justify-between items-center">
                    <span class="text-xs font-bold text-zinc-400 tracking-wider">CPL SPECIFICATION (JSON)</span>
                    <button onclick="prettifyJSON()" class="text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded border border-white/5">Prettify</button>
                </div>
                <textarea id="editor" class="flex-1 w-full bg-zinc-950/80 p-4 code-font text-xs text-emerald-400 border-0 outline-none resize-none focus:ring-0"></textarea>
            </div>

            <!-- Model Catalog -->
            <div class="glass p-4 rounded-xl space-y-3 shrink-0">
                <div class="flex justify-between items-center">
                    <label class="text-xs font-bold text-zinc-400 uppercase tracking-wider block">2. Target Model Manifest</label>
                    <select id="model-select" onchange="updateModelManifest()" class="bg-zinc-900 text-xs font-semibold text-white px-2 py-1 rounded border border-white/10 outline-none">
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                        <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                        <option value="llama-3-1-8b">LLaMA 3.1 8B</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-4 text-[11px] bg-zinc-950/40 p-3 rounded-lg border border-white/5 code-font">
                    <div>
                        <span class="text-zinc-500">Model ID:</span> <span id="lbl-model-id" class="text-white"></span><br/>
                        <span class="text-zinc-500">Ops:</span> <span id="lbl-model-ops" class="text-cyan-400"></span>
                    </div>
                    <div>
                        <span class="text-zinc-500">Domains:</span> <span id="lbl-model-domains" class="text-purple-400"></span><br/>
                        <span class="text-zinc-500">Context Window:</span> <span id="lbl-model-context" class="text-yellow-400"></span>
                    </div>
                </div>
                
                <!-- API Credentials -->
                <div class="pt-2 flex gap-2 items-center">
                    <input id="api-key" type="password" placeholder="Gemini API Key (Optional for real API execution)" class="flex-1 bg-zinc-900 text-xs px-3 py-2 rounded-lg border border-white/10 outline-none focus:border-cyan-500 text-white placeholder-zinc-500"/>
                </div>
            </div>
        </div>

        <!-- Right Panel: Diagnostics Terminal -->
        <div class="space-y-6 flex flex-col h-[calc(100vh-140px)]">
            
            <!-- Execution Actions -->
            <div class="grid grid-cols-3 gap-2 shrink-0">
                <button onclick="doAction('validate')" class="py-2.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-bold rounded-lg text-xs tracking-wider transition-all border border-white/5">
                    1. VALIDATE SPEC
                </button>
                <button onclick="doAction('negotiate')" class="py-2.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-bold rounded-lg text-xs tracking-wider transition-all border border-white/5">
                    2. NEGOTIATE
                </button>
                <button onclick="doAction('run')" class="py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-zinc-950 font-extrabold rounded-lg text-xs tracking-wider transition-all shadow-lg shadow-cyan-500/10">
                    3. RUN & VERIFY
                </button>
            </div>

            <!-- Diagnostics Console -->
            <div class="glass rounded-xl flex-1 flex flex-col overflow-hidden">
                <div class="bg-zinc-900/60 border-b border-white/5 px-4 py-2 flex items-center justify-between">
                    <span class="text-xs font-bold text-zinc-400 tracking-wider">DIAGNOSTICS & VERIFICATION ENGINE</span>
                    <button onclick="clearConsole()" class="text-[10px] text-zinc-500 hover:text-zinc-300">Clear</button>
                </div>
                <div id="console-output" class="flex-1 overflow-auto p-4 space-y-4 text-xs code-font">
                    <div class="text-zinc-500 border-b border-white/5 pb-2">Initialize console... Select a CPL standard spec and press actions above to test execution.</div>
                </div>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-white/5 py-3 text-center text-zinc-500 text-[10px] shrink-0">
        🕉️ Mahaakali CSIG Frameworks · Common Prompt Language (CPL) Standard Initiative 2026.
    </footer>

    <!-- Template Data -->
    <script>
        const TEMPLATES = {
            legal: {
                "cpl_version": "1.0.0",
                "domain_extension": "CPL-Legal",
                "operation": "ANALYZE",
                "spec": {
                    "document_type": "Contract",
                    "jurisdiction": "US-Federal",
                    "document_text": "Clause 4. Limitation of Liability. The contractor represents unlimited liability for all damages, breach of warranties and negligence claims arising from this engagement. No governing law is set.",
                    "authorities": ["Restatement (Second) of Contracts", "UCC Article 2"]
                },
                "context": {
                    "domains": ["legal", "analysis"],
                    "temporal_bounds": "2026"
                },
                "constraints": [
                    { "type": "max_context_tokens", "value": 15000, "priority": "MUST" },
                    { "type": "structured_output", "value": true, "priority": "SHOULD" }
                ],
                "contract": {
                    "preconditions": {
                        "input_present": "document_text"
                    },
                    "postconditions": {
                        "contains_citations": true,
                        "required_sections": ["issue", "rule", "analysis", "conclusion"],
                        "json_schema": {
                            "type": "object",
                            "properties": {
                                "issue": { "type": "string" },
                                "rule": { "type": "string" },
                                "analysis": { "type": "string" },
                                "conclusion": { "type": "string" }
                            },
                            "required": ["issue", "rule", "analysis", "conclusion"]
                        }
                    },
                    "invariants": {
                        "no_hallucinations": true
                    }
                }
            },
            code: {
                "cpl_version": "1.0.0",
                "domain_extension": "CPL-Code",
                "operation": "SYNTHESIZE",
                "spec": {
                    "task": "implement_function",
                    "signature": "def find_k_largest(nums: List[int], k: int) -> List[int]",
                    "constraints": {
                        "time_complexity": "O(n log k)",
                        "space_complexity": "O(k)"
                    }
                },
                "context": {
                    "domains": ["software_engineering", "algorithms"]
                },
                "constraints": [
                    { "type": "max_context_tokens", "value": 5000, "priority": "MUST" }
                ],
                "contract": {
                    "postconditions": {
                        "min_words": 50,
                        "required_sections": ["def find_k_largest"]
                    }
                }
            },
            creative: {
                "cpl_version": "1.0.0",
                "domain_extension": "CPL-Creative",
                "operation": "SYNTHESIZE",
                "spec": {
                    "genre": "science_fiction",
                    "prompt": "Write a narrative about an AI pilot realizing its spaceship crew has been simulated."
                },
                "context": {
                    "domains": ["creative_content"]
                },
                "constraints": [
                    { "type": "max_context_tokens", "value": 8000, "priority": "MUST" }
                ],
                "contract": {
                    "postconditions": {
                        "min_words": 200,
                        "max_words": 1000
                    }
                }
            }
        };

        const MODEL_MANIFESTS = """ + json.dumps(MOCK_MANIFESTS) + """;

        function loadTemplate(name) {
            // Update tabs highlight
            ['legal', 'code', 'creative'].forEach(t => {
                const btn = document.getElementById('btn-tmpl-' + t);
                if (t === name) {
                    btn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-cyan-600 text-white transition-all";
                } else {
                    btn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-zinc-900 text-zinc-400 hover:bg-zinc-800 transition-all";
                }
            });

            document.getElementById('editor').value = JSON.stringify(TEMPLATES[name], null, 2);
        }

        function prettifyJSON() {
            const editor = document.getElementById('editor');
            try {
                const parsed = JSON.parse(editor.value);
                editor.value = JSON.stringify(parsed, null, 2);
            } catch(e) {
                alert("Invalid JSON format!");
            }
        }

        function updateModelManifest() {
            const selected = document.getElementById('model-select').value;
            const model = MODEL_MANIFESTS[selected];
            
            document.getElementById('lbl-model-id').innerText = model.model_id;
            document.getElementById('lbl-model-ops').innerText = model.capabilities.operations.join(', ');
            document.getElementById('lbl-model-domains').innerText = model.capabilities.domains.join(', ');
            document.getElementById('lbl-model-context').innerText = model.constraints.context_window.toLocaleString() + ' tokens';
        }

        function clearConsole() {
            document.getElementById('console-output').innerHTML = '<div class="text-zinc-500 border-b border-white/5 pb-2">Console cleared.</div>';
        }

        function logToConsole(title, content, type = 'info') {
            const consoleEl = document.getElementById('console-output');
            let typeColor = 'text-cyan-400';
            if (type === 'error') typeColor = 'text-red-400';
            if (type === 'success') typeColor = 'text-emerald-400';
            if (type === 'warning') typeColor = 'text-yellow-400';

            const section = document.createElement('div');
            section.className = 'border-b border-white/5 pb-3 space-y-1.5';
            
            const header = document.createElement('div');
            header.className = 'flex justify-between items-center font-semibold text-zinc-300';
            header.innerHTML = `<span>[${title.toUpperCase()}]</span> <span class="${typeColor} text-[10px] uppercase font-bold">${type}</span>`;
            
            const body = document.createElement('pre');
            body.className = 'whitespace-pre-wrap pl-2 text-zinc-400 leading-relaxed max-h-96 overflow-auto';
            body.innerHTML = content;

            section.appendChild(header);
            section.appendChild(body);
            consoleEl.appendChild(section);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        async function doAction(action) {
            const specText = document.getElementById('editor').value;
            const modelId = document.getElementById('model-select').value;
            const apiKey = document.getElementById('api-key').value;

            let parsedSpec;
            try {
                parsedSpec = JSON.parse(specText);
            } catch(e) {
                logToConsole("Parser", "JSON formatting error: " + e.message, "error");
                return;
            }

            const payload = {
                spec: parsedSpec,
                model_id: modelId,
                api_key: apiKey
            };

            logToConsole("System", `Initiating ${action.toUpperCase()} workflow for ${modelId}...`, "info");

            try {
                const response = await fetch('/api/' + action, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (action === 'validate') {
                    if (data.is_valid) {
                        logToConsole("Validator", "CPL core schema check: VALID\\nCPL specifications parsed successfully.", "success");
                    } else {
                        logToConsole("Validator", "CPL core schema check: FAILED\\nErrors:\\n" + data.errors.map(e => "  - " + e).join('\\n'), "error");
                    }
                }
                
                else if (action === 'negotiate') {
                    const statusType = data.negotiation.can_fulfill ? "success" : "error";
                    let details = `Model compatibility match score: ${data.negotiation.score * 100}%\\nCan Fulfill constraints: ${data.negotiation.can_fulfill ? 'YES' : 'NO'}\\n`;
                    if (data.negotiation.reasons && data.negotiation.reasons.length > 0) {
                        details += `\\nGaps/Advisories:\\n` + data.negotiation.reasons.map(r => "  ⚠️ " + r).join('\\n');
                    }
                    if (data.negotiation.missing_optional && data.negotiation.missing_optional.length > 0) {
                        details += `\\n\\nMissing Optional Capabilities:\\n` + data.negotiation.missing_optional.map(m => "  - " + m).join('\\n');
                    }
                    logToConsole("Negotiator", details, statusType);
                }
                
                else if (action === 'run') {
                    // Log compile output
                    logToConsole("Compiler", "CPL Spec compiled to standard system instruction block successfully:\\n\\n" + data.compiled_prompt, "info");
                    
                    // Log output
                    let outputStr = "Model Output received:\\n-------------------------------\\n";
                    if (typeof data.response.content === 'object') {
                        outputStr += JSON.stringify(data.response.content, null, 2);
                    } else {
                        outputStr += data.response.content;
                    }
                    logToConsole("Model Execution", outputStr + `\\n-------------------------------\\nSource: ${data.response.model_id} (${data.response.execution_trace.mode || 'API'})`, "info");
                    
                    // Log contract check
                    const verifyStatus = data.verification.passed ? "success" : "error";
                    let checkList = `Contract verification: ${data.verification.passed ? 'PASSED' : 'FAILED'}\\n\\nChecklist:\\n`;
                    for (const [key, value] of Object.entries(data.verification.results)) {
                        const icon = value ? '✅' : '❌';
                        checkList += `  ${icon} ${key}: ${data.verification.details[key] || ''}\\n`;
                    }
                    
                    if (data.legal_verification) {
                        checkList += `\\nCPL-Legal Domain Checklist:\\n`;
                        const icon = data.legal_verification.is_valid ? '✅' : '❌';
                        if (data.legal_verification.is_valid) {
                            checkList += `  ✅ IRAC format structure matches standard.\\n  ✅ Authority citations present.\\n`;
                        } else {
                            data.legal_verification.errors.forEach(err => {
                                checkList += `  ❌ ${err}\\n`;
                            });
                        }
                    }
                    
                    logToConsole("Contract Verifier", checkList, verifyStatus);
                }
            } catch(e) {
                logToConsole("System", "Failed to connect to backend engine API: " + e.message, "error");
            }
        }

        // Initialize template
        loadTemplate('legal');
        updateModelManifest();
    </script>
</body>
</html>
"""

class CPLStudioRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence verbose request logs
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'] or 0)
        body = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON payload"}')
            return

        spec_data = payload.get("spec", {})
        model_id = payload.get("model_id", "gemini-2.5-flash")
        api_key = payload.get("api_key", "")

        response_data = {}

        if self.path == '/api/validate':
            is_valid, errors = CPLValidator.validate_dict(spec_data)
            response_data = {"is_valid": is_valid, "errors": errors}

        elif self.path == '/api/negotiate':
            req = CPLRequest.from_dict(spec_data)
            manifest = ModelManifest.from_dict(MOCK_MANIFESTS.get(model_id, MOCK_MANIFESTS["gemini-2.5-flash"]))
            res = CPLNegotiator.negotiate(req, manifest)
            response_data = {"negotiation": res.to_dict()}

        elif self.path == '/api/run':
            # Create request
            req = CPLRequest.from_dict(spec_data)
            manifest = ModelManifest.from_dict(MOCK_MANIFESTS.get(model_id, MOCK_MANIFESTS["gemini-2.5-flash"]))
            
            # Negotiate
            negotiation_res = CPLNegotiator.negotiate(req, manifest)
            
            # Compile prompt
            compiled_prompt = CPLPromptCompiler.compile(req)
            
            # Execute
            model = GeminiModel(model_id=model_id, api_key=api_key)
            cpl_response = model.execute(req)
            
            # Verify Contract
            verify_res = CPLContractVerifier.verify(req, cpl_response)
            
            # Compile response payload
            response_data = {
                "negotiation": negotiation_res.to_dict(),
                "compiled_prompt": compiled_prompt,
                "response": cpl_response.to_dict(),
                "verification": verify_res.to_dict()
            }

            # Optional Legal Domain check in output if applicable
            if req.domain_extension == "CPL-Legal" or "legal" in req.context.domains:
                is_legal_valid, legal_errors = CPLLegalValidator.verify_legal_response(cpl_response)
                response_data["legal_verification"] = {
                    "is_valid": is_legal_valid,
                    "errors": legal_errors
                }
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

def run_server():
    server = HTTPServer(('0.0.0.0', PORT), CPLStudioRequestHandler)
    print(f"\\n\\x1b[36m====================================================\\x1b[0m")
    print(f"\\x1b[32m🕉️  CPL Web Studio successfully initialized!\\x1b[0m")
    print(f"\\x1b[35m -> Hosting interface at: \\x1b[4mhttp://localhost:{PORT}\\x1b[0m")
    print(f"\\x1b[36m====================================================\\x1b[0m\\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down CPL Studio server...")
        server.server_close()

if __name__ == "__main__":
    run_server()
