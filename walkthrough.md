# Walkthrough - CPL Open Source Framework

We have successfully built and verified the open-source implementation of the **Common Prompt Language (CPL)** framework. All files are stored strictly within the `/home/gopinath/Documents/CPL` workspace folder.

---

## What was Built

### 1. The Core CPL SDK (`cpl/`)
* **[core.py](file:///home/gopinath/Documents/CPL/cpl/core.py)**: Holds standard Python models for `CPLRequest`, `CPLResponse`, `Context`, `Constraint`, and `Contract`, matching the proposed W3C/consortium-style specification.
* **[validator.py](file:///home/gopinath/Documents/CPL/cpl/validator.py)**: A schema validation engine verifying structures and parameters.
* **[negotiator.py](file:///home/gopinath/Documents/CPL/cpl/negotiator.py)**: Implements the *Capability Negotiation Protocol* matching request requirements against model manifests.
* **[contract.py](file:///home/gopinath/Documents/CPL/cpl/contract.py)**: Enforces postconditions (schema matching, word count bounds, citations present) and invariants.
* **[models.py](file:///home/gopinath/Documents/CPL/cpl/models.py)**: Translates CPL requests into target prompts and connects to mock/real APIs.

### 2. Specialized Extensions
* **[extensions/legal.py](file:///home/gopinath/Documents/CPL/cpl/extensions/legal.py)**: The `CPL-Legal` domain extension checking for jurisdiction, authority citations, and IRAC (Issue, Rule, Analysis, Conclusion) format verification.

### 3. Tooling & Visual Studio
* **[cpl_cli.py](file:///home/gopinath/Documents/CPL/cpl_cli.py)**: CLI helper to `validate`, `negotiate`, and `run` CPL files.
* **[cpl_studio.py](file:///home/gopinath/Documents/CPL/cpl_studio.py)**: A standalone web playground hosted at `http://localhost:8085` that lets users edit CPL specifications, simulate negotiation/execution, and visualize contract validation rules on outputs in real-time.
* **[setup.py](file:///home/gopinath/Documents/CPL/setup.py)**: Standard package configuration.
* **[README.md](file:///home/gopinath/Documents/CPL/README.md)**: Open-source getting started documentation.
* **[examples/](file:///home/gopinath/Documents/CPL/examples/)**: Sample `legal_contract.json` spec and `gemini_manifest.json` capability model manifest.

---

## Verification & Testing

### 1. Python SDK Unit Tests
Run unit tests checking all SDK features:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
**Status**: `7 tests passed (OK)`.

### 2. CLI Execution
Validating and negotiating using the CLI works out of the box:
```bash
python3 cpl_cli.py validate examples/legal_contract.json
python3 cpl_cli.py negotiate examples/legal_contract.json examples/gemini_manifest.json
python3 cpl_cli.py run examples/legal_contract.json
```
**Status**: All actions executed successfully. Outputs verified to meet the contract.

### 3. Visual CPL Studio Dashboard
The background server is running:
* **Endpoint**: [http://localhost:8085](http://localhost:8085)
* Custom Tailwind CSS interface loaded with preset templates (Legal Contract Audit, Python Algorithm Generator, Creative Narrative).
* Real-time negotiation score calculation.
* Contract checklists are color-coded (emerald for compliant check, red for non-compliant gaps).
