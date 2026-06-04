from enum import Enum
from typing import List, Dict, Any, Optional

class Operation(str, Enum):
    ANALYZE = "ANALYZE"
    SYNTHESIZE = "SYNTHESIZE"
    TRANSFORM = "TRANSFORM"
    VERIFY = "VERIFY"

class ConstraintPriority(str, Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"

class Constraint:
    def __init__(self, type_name: str, value: Any, priority: ConstraintPriority = ConstraintPriority.MUST, negotiable: bool = False):
        self.type = type_name
        self.value = value
        self.priority = ConstraintPriority(priority)
        self.negotiable = negotiable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "value": self.value,
            "priority": self.priority.value,
            "negotiable": self.negotiable
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Constraint':
        return cls(
            type_name=d.get("type", ""),
            value=d.get("value", None),
            priority=ConstraintPriority(d.get("priority", "MUST")),
            negotiable=d.get("negotiable", False)
        )

class Context:
    def __init__(self, domains: List[str], temporal_bounds: Optional[str] = None, source_quality: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None):
        self.domains = domains
        self.temporal_bounds = temporal_bounds
        self.source_quality = source_quality
        self.parameters = parameters or {}

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "domains": self.domains
        }
        if self.temporal_bounds:
            d["temporal_bounds"] = self.temporal_bounds
        if self.source_quality:
            d["source_quality"] = self.source_quality
        if self.parameters:
            d["parameters"] = self.parameters
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Context':
        return cls(
            domains=d.get("domains", []),
            temporal_bounds=d.get("temporal_bounds"),
            source_quality=d.get("source_quality"),
            parameters=d.get("parameters", {})
        )

class Contract:
    def __init__(self, preconditions: Optional[Dict[str, Any]] = None, postconditions: Optional[Dict[str, Any]] = None, invariants: Optional[Dict[str, Any]] = None):
        self.preconditions = preconditions or {}
        self.postconditions = postconditions or {}
        self.invariants = invariants or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "invariants": self.invariants
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Contract':
        return cls(
            preconditions=d.get("preconditions", {}),
            postconditions=d.get("postconditions", {}),
            invariants=d.get("invariants", {})
        )

class CPLRequest:
    def __init__(self, operation: Operation, spec: Dict[str, Any], context: Context, constraints: List[Constraint], contract: Optional[Contract] = None, cpl_version: str = "1.0.0", domain_extension: Optional[str] = None):
        self.cpl_version = cpl_version
        self.domain_extension = domain_extension
        self.operation = Operation(operation)
        self.spec = spec
        self.context = context
        self.constraints = constraints
        self.contract = contract or Contract()

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "cpl_version": self.cpl_version,
            "operation": self.operation.value,
            "spec": self.spec,
            "context": self.context.to_dict(),
            "constraints": [c.to_dict() for c in self.constraints],
            "contract": self.contract.to_dict()
        }
        if self.domain_extension:
            d["domain_extension"] = self.domain_extension
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CPLRequest':
        return cls(
            operation=Operation(d.get("operation", "ANALYZE")),
            spec=d.get("spec", {}),
            context=Context.from_dict(d.get("context", {})),
            constraints=[Constraint.from_dict(c) for c in d.get("constraints", [])],
            contract=Contract.from_dict(d.get("contract", {})),
            cpl_version=d.get("cpl_version", "1.0.0"),
            domain_extension=d.get("domain_extension")
        )

class CPLResponse:
    def __init__(self, content: Any, model_id: str, cpl_version: str, execution_trace: Optional[Dict[str, Any]] = None, raw_output: Optional[str] = None):
        self.content = content
        self.model_id = model_id
        self.cpl_version = cpl_version
        self.execution_trace = execution_trace or {}
        self.raw_output = raw_output

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model_id": self.model_id,
            "cpl_version": self.cpl_version,
            "execution_trace": self.execution_trace,
            "raw_output": self.raw_output
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CPLResponse':
        return cls(
            content=d.get("content"),
            model_id=d.get("model_id", "unknown"),
            cpl_version=d.get("cpl_version", "1.0.0"),
            execution_trace=d.get("execution_trace", {}),
            raw_output=d.get("raw_output")
        )
