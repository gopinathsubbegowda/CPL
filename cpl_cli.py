#!/usr/bin/env python3
import sys
import json
import argparse
from cpl.core import CPLRequest
from cpl.validator import CPLValidator
from cpl.negotiator import CPLNegotiator, ModelManifest
from cpl.contract import CPLContractVerifier
from cpl.models import GeminiModel
from cpl.extensions.legal import CPLLegalValidator

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        sys.exit(1)

def run_validate(args):
    data = load_json(args.file)
    is_valid, errors = CPLValidator.validate_dict(data)
    
    if not is_valid:
        print("❌ CPL Specification Schema Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
        
    print("✅ CPL Specification Schema is VALID.")
    
    # Check domain extension validation if applicable
    req = CPLRequest.from_dict(data)
    if req.domain_extension == "CPL-Legal" or "legal" in req.context.domains:
        is_legal_valid, legal_errors = CPLLegalValidator.validate_legal_request(req)
        if not is_legal_valid:
            print("⚠️ CPL-Legal Domain Extension validation errors:")
            for err in legal_errors:
                print(f"  - {err}")
        else:
            print("✅ CPL-Legal Domain properties are VALID.")

def run_negotiate(args):
    req_data = load_json(args.file)
    manifest_data = load_json(args.manifest)
    
    req = CPLRequest.from_dict(req_data)
    model = ModelManifest.from_dict(manifest_data)
    
    result = CPLNegotiator.negotiate(req, model)
    print(f"=== Capability Negotiation Results for Model: {model.model_id} ===")
    print(f"Score compatibility: {result.score * 100}%")
    print(f"Can fulfill constraints: {'✅ YES' if result.can_fulfill else '❌ NO'}")
    
    if result.reasons:
        print("\nGaps/Errors Identified:")
        for reason in result.reasons:
            print(f"  - {reason}")
            
    if result.missing_optional:
        print("\nOptional Constraints Not Met:")
        for missing in result.missing_optional:
            print(f"  - {missing}")

def run_execute(args):
    data = load_json(args.file)
    is_valid, errors = CPLValidator.validate_dict(data)
    if not is_valid:
        print("❌ CPL Specification Schema Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    req = CPLRequest.from_dict(data)
    model_id = args.model or "gemini-2.5-flash"
    model = GeminiModel(model_id=model_id, api_key=args.key)
    
    print(f"🚀 Executing CPL Request on model '{model_id}'...")
    response = model.execute(req)
    
    print("\n--- Model Output Content ---")
    if isinstance(response.content, dict):
        print(json.dumps(response.content, indent=2))
    else:
        print(response.content)
        
    print("\n--- Contract Compliance Verification ---")
    verify_res = CPLContractVerifier.verify(req, response)
    print(f"Status: {'✅ PASSED' if verify_res.passed else '❌ FAILED'}")
    print("\nVerification Checklist:")
    for check, passed in verify_res.results.items():
        symbol = "✅" if passed else "❌"
        print(f"  {symbol} {check}: {verify_res.details.get(check, '')}")
        
    # Check domain extension validation in output if applicable
    if req.domain_extension == "CPL-Legal" or "legal" in req.context.domains:
        is_legal_valid, legal_errors = CPLLegalValidator.verify_legal_response(response)
        print("\nCPL-Legal Domain Compliance Checklist:")
        if not is_legal_valid:
            for err in legal_errors:
                print(f"  ❌ {err}")
        else:
            print("  ✅ IRAC format structure matches standard.")
            print("  ✅ Authority citations present.")

def main():
    parser = argparse.ArgumentParser(description="Common Prompt Language (CPL) CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Validate command
    parser_val = subparsers.add_parser("validate", help="Validate a CPL specification JSON file")
    parser_val.add_argument("file", help="Path to CPL JSON file")
    parser_val.set_defaults(func=run_validate)
    
    # Negotiate command
    parser_neg = subparsers.add_parser("negotiate", help="Negotiate CPL request capabilities against a model manifest")
    parser_neg.add_argument("file", help="Path to CPL JSON file")
    parser_neg.add_argument("manifest", help="Path to model manifest JSON file")
    parser_neg.set_defaults(func=run_negotiate)
    
    # Run command
    parser_run = subparsers.add_parser("run", help="Execute CPL request and verify contract compliance")
    parser_run.add_argument("file", help="Path to CPL JSON file")
    parser_run.add_argument("--model", help="Gemini model ID to run")
    parser_run.add_argument("--key", help="Gemini API key")
    parser_run.set_defaults(func=run_execute)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
