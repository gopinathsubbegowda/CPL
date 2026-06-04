# Common Prompt Language (CPL) Specification & SDK

An open-source standard and toolkit for future-agnostic Cognitive Prompting Language (CPL) to solve the diversity problem of fragmented AI model behaviors. CPL decouples the cognitive intent of a prompt from specific model implementations using a standard type system, operation enums, and contract-based validation (DbC).

---

## Architecture Overview

1. **Universal Core Layer**: Core primitives for task intents (ANALYZE, SYNTHESIZE, TRANSFORM, VERIFY) and input/output contracts.
2. **Domain-Specific Extensions (DSEs)**: Domain-specific schemas and validation rules (e.g. CPL-Legal, CPL-Code).
3. **Capability Negotiation Protocol**: Compares request requirements with a model's capabilities manifest to ensure compatibility.
4. **Contract-Based Validation**: Enforces preconditions, invariants, and postconditions (schema matching, word count bounds, citations checks) on outputs.

---

## Folder Structure

* `cpl/core.py`: Core data structures (`CPLRequest`, `CPLResponse`, `Constraint`, `Context`, `Contract`).
* `cpl/validator.py`: Base schema validation engine.
* `cpl/negotiator.py`: Capability negotiation mechanism and model manifests.
* `cpl/contract.py`: Pre/postconditions and invariants contract verifier.
* `cpl/extensions/legal.py`: Domain extension for legal analysis (jurisdiction, authorities, and IRAC checks).
* `cpl/models.py`: Model integration adapter and prompt compiler.
* `cpl_cli.py`: CPL Command Line Interface.
* `cpl_studio.py`: Visual web playground dashboard.
* `tests/`: SDK test suite.

---

## Getting Started

### Prerequisites

* Python 3.8+

### Running unit tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

### Running the CPL Web Studio

Launch the interactive visual dashboard on port 8085:

```bash
python3 cpl_studio.py
```

Then open `http://localhost:8085` in your browser.

---

## Using the CLI

### 1. Schema Validation
Validate that a CPL specification follows the standard core schema:
```bash
python3 cpl_cli.py validate examples/legal_contract.json
```

### 2. Capability Negotiation
Negotiate capabilities of a CPL request against a model's manifest:
```bash
python3 cpl_cli.py negotiate examples/legal_contract.json examples/gemini_manifest.json
```

### 3. Run and Verify Compliance
Compile the CPL request to a standard instruction block, send it to a model (simulated or real Gemini API), and run the contract compliance verifier:
```bash
python3 cpl_cli.py run examples/legal_contract.json --model gemini-2.5-flash
```

---

## Python API Usage

```python
import json
from cpl.core import CPLRequest, Operation
from cpl.models import GeminiModel
from cpl.contract import CPLContractVerifier

# 1. Parse your CPL spec
with open("examples/legal_contract.json") as f:
    spec_dict = json.load(f)
req = CPLRequest.from_dict(spec_dict)

# 2. Execute on a model
model = GeminiModel(model_id="gemini-2.5-flash")
response = model.execute(req)

# 3. Verify compliance
verify_res = CPLContractVerifier.verify(req, response)
print(f"Compliance Pass: {verify_res.passed}")
```
