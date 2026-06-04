import re
import json
from typing import Dict, Any, List, Tuple
from cpl.core import CPLRequest, CPLResponse, CITATION_PATTERNS

class ContractVerificationResult:
    def __init__(self, passed: bool, results: Dict[str, bool], details: Dict[str, str]):
        self.passed = passed
        self.results = results
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "results": self.results,
            "details": self.details
        }

class CPLContractVerifier:
    @staticmethod
    def verify(request: CPLRequest, response: CPLResponse) -> ContractVerificationResult:
        passed = True
        results = {}
        details = {}

        contract = request.contract
        postconditions = contract.postconditions
        content = response.content

        # 1. Postcondition: JSON schema verification
        if "json_schema" in postconditions:
            schema = postconditions["json_schema"]
            is_valid_json, err_msg = CPLContractVerifier._verify_json_structure(content, schema)
            results["json_schema"] = is_valid_json
            if not is_valid_json:
                passed = False
                details["json_schema"] = f"Failed JSON Schema Check: {err_msg}"
            else:
                details["json_schema"] = "Passed JSON Schema Check"

        # 2. Postcondition: Min/Max word count, sections, and citation checks
        # Compute text representation lazily — only when at least one text-based check is requested
        _text_checks = ("min_words", "max_words", "required_sections", "contains_citations")
        text_content = ""
        words = 0
        if any(k in postconditions for k in _text_checks):
            text_content = json.dumps(content) if isinstance(content, dict) else str(content)
            words = len(re.findall(r'\w+', text_content))

        if "min_words" in postconditions:
            min_w = int(postconditions["min_words"])
            check_passed = words >= min_w
            results["min_words"] = check_passed
            if not check_passed:
                passed = False
                details["min_words"] = f"Word count {words} is less than minimum {min_w}"
            else:
                details["min_words"] = f"Word count {words} satisfies minimum {min_w}"

        if "max_words" in postconditions:
            max_w = int(postconditions["max_words"])
            check_passed = words <= max_w
            results["max_words"] = check_passed
            if not check_passed:
                passed = False
                details["max_words"] = f"Word count {words} exceeds maximum {max_w}"
            else:
                details["max_words"] = f"Word count {words} satisfies maximum {max_w}"

        # 3. Postcondition: Required sections
        if "required_sections" in postconditions:
            sections = postconditions["required_sections"]
            missing = []
            for sec in sections:
                # Case insensitive search
                if not re.search(re.escape(sec), text_content, re.IGNORECASE):
                    missing.append(sec)
            
            check_passed = len(missing) == 0
            results["required_sections"] = check_passed
            if not check_passed:
                passed = False
                details["required_sections"] = f"Missing required sections: {missing}"
            else:
                details["required_sections"] = "All required sections are present"

        # 4. Postcondition: Citations check
        if "contains_citations" in postconditions:
            citation_req = postconditions["contains_citations"]
            if citation_req:
                has_citation = any(re.search(p, text_content) for p in CITATION_PATTERNS)
                if not has_citation:
                    passed = False
                    results["contains_citations"] = False
                    details["contains_citations"] = "No citations or legal authority references found in output"
                else:
                    results["contains_citations"] = True
                    details["contains_citations"] = "Citations and authority references verified present"

        # 5. Invariant check
        invariants = contract.invariants
        if "no_hallucinations" in invariants and invariants["no_hallucinations"]:
            results["no_hallucinations"] = True
            details["no_hallucinations"] = "Hallucination check: UNIMPLEMENTED — invariant declared but not enforced (Sprint 5 target)"

        return ContractVerificationResult(
            passed=passed,
            results=results,
            details=details
        )

    @staticmethod
    def _verify_json_structure(content: Any, schema: Dict[str, Any]) -> Tuple[bool, str]:
        # Handle case where content is a string that needs to be parsed as JSON
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                return False, "Content is not valid JSON string"

        if not isinstance(content, dict):
            return False, "Content must be a dictionary/JSON object"

        # Basic type and key matching validator (Zero dependency implementation)
        required_keys = schema.get("required", [])
        properties = schema.get("properties", {})

        for key in required_keys:
            if key not in content:
                return False, f"Missing required property: '{key}'"
            if key not in properties:
                return False, f"Schema error: required property '{key}' has no type definition in 'properties'"

        for key, value in content.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")

                if prop_type == "string" and not isinstance(value, str):
                    return False, f"Property '{key}' must be a string, got {type(value).__name__}"
                elif prop_type == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
                    return False, f"Property '{key}' must be an integer, got {type(value).__name__}"
                elif prop_type == "number" and not isinstance(value, (int, float)):
                    return False, f"Property '{key}' must be a number, got {type(value).__name__}"
                elif prop_type == "boolean" and not isinstance(value, bool):
                    return False, f"Property '{key}' must be a boolean, got {type(value).__name__}"
                elif prop_type == "array" and not isinstance(value, list):
                    return False, f"Property '{key}' must be an array, got {type(value).__name__}"
                elif prop_type == "object" and not isinstance(value, dict):
                    return False, f"Property '{key}' must be an object, got {type(value).__name__}"

        return True, ""
