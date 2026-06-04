import re
from typing import Dict, Any, List, Tuple
from cpl.core import CPLRequest, CPLResponse

class CPLLegalValidator:
    @staticmethod
    def validate_legal_request(request: CPLRequest) -> Tuple[bool, List[str]]:
        errors = []
        spec = request.spec

        # 1. Verification of Legal Domain properties
        if request.domain_extension != "CPL-Legal" and "legal" not in request.context.domains:
            errors.append("Request is not explicitly declared as a CPL-Legal extension or legal domain")

        # 2. Jurisdiction is a first-class required property
        if "jurisdiction" not in spec:
            errors.append("CPL-Legal error: Missing required property 'jurisdiction' (e.g., 'US-Federal', 'IN-SupremeCourt')")
        elif not isinstance(spec["jurisdiction"], str):
            errors.append("CPL-Legal error: 'jurisdiction' must be a string")

        # 3. Document type checking
        if "document_type" not in spec:
            errors.append("CPL-Legal error: Missing required property 'document_type' (must be Contract, Statute, or Precedent)")
        else:
            doc_type = spec["document_type"]
            valid_types = ["Contract", "Statute", "Precedent", "LegalBrief", "RegulatoryGuideline"]
            if doc_type not in valid_types:
                errors.append(f"CPL-Legal error: Invalid 'document_type' '{doc_type}'. Must be one of: {valid_types}")

        # 4. Authority / Citation verification
        if "authorities" not in spec:
            errors.append("CPL-Legal error: Missing required property 'authorities' (list of citations or references to ground the analysis)")
        elif not isinstance(spec["authorities"], list):
            errors.append("CPL-Legal error: 'authorities' must be a list")
        elif len(spec["authorities"]) == 0:
            errors.append("CPL-Legal error: 'authorities' must contain at least one legal citation or reference")

        return len(errors) == 0, errors

    @staticmethod
    def verify_legal_response(response: CPLResponse) -> Tuple[bool, List[str]]:
        errors = []
        content = response.content
        
        # Determine text content
        text_content = ""
        if isinstance(content, dict):
            import json
            text_content = json.dumps(content)
        else:
            text_content = str(content)

        # 1. Enforcement of IRAC (Issue, Rule, Analysis, Conclusion) structure
        irac_terms = ["issue", "rule", "analysis", "conclusion"]
        missing_irac = []
        for term in irac_terms:
            if not re.search(r'\b' + re.escape(term) + r'\b', text_content, re.IGNORECASE):
                missing_irac.append(term.capitalize())
        
        if missing_irac:
            errors.append(f"CPL-Legal Verification Fail: Response does not follow the IRAC structure. Missing sections: {', '.join(missing_irac)}")

        # 2. Strict authority reference check in response text
        # Checks if there are citations like "Section X", "Article Y", or case names "v."
        citation_found = False
        citation_patterns = [
            r'(?i)\b(?:section|sec|art|article)\b\s*\d+',
            r'(?i)\b(?:v\.|versus)\b',
            r'\[\d+\]',
            r'\[[A-Za-z\s]+,\s*\d{4}\]'
        ]
        for pattern in citation_patterns:
            if re.search(pattern, text_content):
                citation_found = True
                break

        if not citation_found:
            errors.append("CPL-Legal Verification Fail: Response lacks authority citations (e.g. 'Section X' or case law references)")

        return len(errors) == 0, errors
