from typing import List, Dict, Any, Tuple
from cpl.core import CPLRequest, Operation, ConstraintPriority

class CPLValidator:
    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        # Check basic keys
        if "operation" not in data:
            errors.append("Missing required field: 'operation'")
        else:
            try:
                Operation(data["operation"])
            except ValueError:
                errors.append(f"Invalid operation: '{data['operation']}'. Must be one of: {[op.value for op in Operation]}")
        
        if "spec" not in data:
            errors.append("Missing required field: 'spec'")
        elif not isinstance(data["spec"], dict):
            errors.append("Field 'spec' must be a dictionary")
            
        if "context" not in data:
            errors.append("Missing required field: 'context'")
        elif not isinstance(data["context"], dict):
            errors.append("Field 'context' must be a dictionary")
        else:
            context = data["context"]
            if "domains" not in context:
                errors.append("Context missing required field: 'domains'")
            elif not isinstance(context["domains"], list):
                errors.append("Context 'domains' must be a list of strings")

        if "constraints" not in data:
            errors.append("Missing required field: 'constraints'")
        elif not isinstance(data["constraints"], list):
            errors.append("Field 'constraints' must be a list")
        else:
            for i, conn in enumerate(data["constraints"]):
                if not isinstance(conn, dict):
                    errors.append(f"Constraint at index {i} must be a dictionary")
                    continue
                if "type" not in conn:
                    errors.append(f"Constraint at index {i} missing required field: 'type'")
                if "value" not in conn:
                    errors.append(f"Constraint at index {i} missing required field: 'value'")
                if "priority" in conn:
                    try:
                        ConstraintPriority(conn["priority"])
                    except ValueError:
                        errors.append(f"Constraint at index {i} has invalid priority '{conn['priority']}'. Must be one of: {[p.value for p in ConstraintPriority]}")

        if "contract" in data and not isinstance(data["contract"], dict):
            errors.append("Field 'contract' must be a dictionary")

        return len(errors) == 0, errors

    @staticmethod
    def validate_request(request: CPLRequest) -> Tuple[bool, List[str]]:
        try:
            return CPLValidator.validate_dict(request.to_dict())
        except Exception as e:
            return False, [f"Validation exception: {str(e)}"]
