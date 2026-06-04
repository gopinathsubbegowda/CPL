import copy
import unittest
import json
from cpl.core import CPLRequest, Operation, Constraint, ConstraintPriority, Context, Contract, CPLResponse
from cpl.validator import CPLValidator
from cpl.negotiator import CPLNegotiator, ModelManifest
from cpl.contract import CPLContractVerifier
from cpl.extensions.legal import CPLLegalValidator
from cpl.models import CPLPromptCompiler, GeminiModel

class TestCPLCore(unittest.TestCase):
    def setUp(self):
        self.valid_req_dict = {
            "cpl_version": "1.0.0",
            "operation": "ANALYZE",
            "spec": {
                "document_text": "Sample liability waiver. Unlimited liability governs all actions.",
                "document_type": "Contract",
                "jurisdiction": "US-Federal",
                "authorities": ["Common Law", "Restatement of Contracts § 19"]
            },
            "context": {
                "domains": ["legal", "analysis"]
            },
            "constraints": [
                {
                    "type": "max_context_tokens",
                    "value": 10000,
                    "priority": "MUST"
                }
            ],
            "contract": {
                "preconditions": {
                    "input_matches": "text_present"
                },
                "postconditions": {
                    "contains_citations": True,
                    "required_sections": ["issue", "rule", "analysis", "conclusion"]
                },
                "invariants": {
                    "no_hallucinations": True
                }
            }
        }

    def test_validation_valid(self):
        is_valid, errors = CPLValidator.validate_dict(self.valid_req_dict)
        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")

    def test_validation_invalid_op(self):
        invalid_dict = self.valid_req_dict.copy()
        invalid_dict["operation"] = "INVALID_OP"
        is_valid, errors = CPLValidator.validate_dict(invalid_dict)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid operation" in err for err in errors))

    def test_validation_missing_spec(self):
        invalid_dict = self.valid_req_dict.copy()
        del invalid_dict["spec"]
        is_valid, errors = CPLValidator.validate_dict(invalid_dict)
        self.assertFalse(is_valid)
        self.assertIn("Missing required field: 'spec'", errors)

    def test_negotiation(self):
        req = CPLRequest.from_dict(self.valid_req_dict)
        
        # Manifest for model that can fulfill request
        model_ok = ModelManifest(
            model_id="super-llm-1.0",
            capabilities={"operations": ["ANALYZE", "SYNTHESIZE"], "domains": ["legal", "analysis"]},
            constraints={"context_window": 100000}
        )
        res_ok = CPLNegotiator.negotiate(req, model_ok)
        self.assertTrue(res_ok.can_fulfill)
        self.assertGreaterEqual(res_ok.score, 0.8)

        # Manifest for model that CANNOT fulfill request (does not support ANALYZE)
        model_fail = ModelManifest(
            model_id="weak-llm-1.0",
            capabilities={"operations": ["SYNTHESIZE"]},
            constraints={"context_window": 50000}
        )
        res_fail = CPLNegotiator.negotiate(req, model_fail)
        self.assertFalse(res_fail.can_fulfill)
        self.assertLess(res_fail.score, 0.6)

    def test_contract_verification(self):
        req = CPLRequest.from_dict(self.valid_req_dict)
        
        # Compliant response
        text_ok = "ISSUE: Liability issues.\nRULE: Common Law rules.\nANALYSIS: Section 4 unlimited liability is analyzed.\nCONCLUSION: Fail compliance."
        resp_ok = CPLResponse(content=text_ok, model_id="test", cpl_version="1.0.0")
        res_verify_ok = CPLContractVerifier.verify(req, resp_ok)
        self.assertTrue(res_verify_ok.passed)
        self.assertTrue(res_verify_ok.results["contains_citations"])
        self.assertTrue(res_verify_ok.results["required_sections"])

        # Non-compliant response (missing conclusion section and citations)
        text_fail = "Issue: Liability issues. Rule: Common Law rules. Analysis: Section 4 is analyzed."
        resp_fail = CPLResponse(content=text_fail, model_id="test", cpl_version="1.0.0")
        res_verify_fail = CPLContractVerifier.verify(req, resp_fail)
        self.assertFalse(res_verify_fail.passed)

    def test_legal_domain_rules(self):
        req_dict = copy.deepcopy(self.valid_req_dict)
        req_dict["domain_extension"] = "CPL-Legal"
        req = CPLRequest.from_dict(req_dict)
        
        # Validate legal request parameters
        is_legal_valid, legal_errors = CPLLegalValidator.validate_legal_request(req)
        self.assertTrue(is_legal_valid, f"Legal request validation failed: {legal_errors}")

        # Invalid: missing jurisdiction
        del req_dict["spec"]["jurisdiction"]
        req_invalid = CPLRequest.from_dict(req_dict)
        is_legal_valid, legal_errors = CPLLegalValidator.validate_legal_request(req_invalid)
        self.assertFalse(is_legal_valid)
        self.assertTrue(any("jurisdiction" in err for err in legal_errors))

    def test_prompt_compilation(self):
        req = CPLRequest.from_dict(self.valid_req_dict)
        compiled = CPLPromptCompiler.compile(req)
        self.assertIn("PRIMARY_OPERATION: ANALYZE", compiled)
        self.assertIn("max_context_tokens: 10000", compiled)
        self.assertIn("contains_citations", compiled)

if __name__ == '__main__':
    unittest.main()
