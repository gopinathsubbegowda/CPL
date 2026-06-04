from typing import List, Dict, Any, Tuple
from cpl.core import CPLRequest, Constraint, ConstraintPriority

class ModelManifest:
    def __init__(self, model_id: str, capabilities: Dict[str, Any], constraints: Dict[str, Any]):
        self.model_id = model_id
        # Capabilities dictionary: e.g., {"operations": ["ANALYZE", ...], "domains": ["legal", ...]}
        self.capabilities = capabilities
        # Constraints dictionary: e.g., {"context_window": 1000000, "structured_output": True}
        self.constraints = constraints

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "capabilities": self.capabilities,
            "constraints": self.constraints
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ModelManifest':
        return cls(
            model_id=d.get("model_id", "unknown"),
            capabilities=d.get("capabilities", {}),
            constraints=d.get("constraints", {})
        )

class NegotiationResult:
    def __init__(self, can_fulfill: bool, score: float, reasons: List[str], missing_optional: List[str]):
        self.can_fulfill = can_fulfill
        self.score = score  # 0.0 to 1.0 compatibility score
        self.reasons = reasons  # Explanations for failures or gaps
        self.missing_optional = missing_optional

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_fulfill": self.can_fulfill,
            "score": self.score,
            "reasons": self.reasons,
            "missing_optional": self.missing_optional
        }

class CPLNegotiator:
    @staticmethod
    def negotiate(request: CPLRequest, model: ModelManifest) -> NegotiationResult:
        reasons = []
        missing_optional = []
        total_points = 10.0
        earned_points = 10.0
        can_fulfill = True

        # 1. Operation Support (Critical)
        supported_ops = model.capabilities.get("operations", [])
        req_op = request.operation.value
        if req_op not in supported_ops:
            reasons.append(f"Model {model.model_id} does not support operation '{req_op}'")
            earned_points -= 5.0
            can_fulfill = False
        else:
            earned_points += 1.0

        # 2. Domain Support (Important)
        supported_domains = model.capabilities.get("domains")  # None = key absent = no restriction
        req_domains = request.context.domains
        for domain in req_domains:
            if supported_domains is not None and domain not in supported_domains:
                reasons.append(f"Model {model.model_id} does not explicitly list domain '{domain}' support")
                earned_points -= 2.0
                # Don't fail the request completely if domain isn't explicitly listed, unless strict
                # Let's count it as a soft warning/score deduction

        # 3. Constraints Validation
        for constraint in request.constraints:
            c_type = constraint.type
            c_val = constraint.value
            c_pri = constraint.priority

            # Check context window
            if c_type == "max_context_tokens":
                limit = model.constraints.get("context_window", 0)
                try:
                    requested = int(c_val)
                except (TypeError, ValueError):
                    reasons.append(f"Constraint '{c_type}' has non-numeric value: {c_val!r}")
                else:
                    if limit and requested > limit:
                        msg = f"Request requires {c_val} tokens, but model only supports {limit}"
                        if c_pri == ConstraintPriority.MUST:
                            can_fulfill = False
                            reasons.append(f"CRITICAL: {msg}")
                            earned_points -= 4.0
                        else:
                            missing_optional.append(msg)
                            earned_points -= 1.0

            # Check structured output requirement
            elif c_type == "structured_output":
                supports_structured = model.capabilities.get("structured_output", False)
                if c_val and not supports_structured:
                    msg = "Structured output required but not native to model"
                    if c_pri == ConstraintPriority.MUST:
                        can_fulfill = False
                        reasons.append(f"CRITICAL: {msg}")
                        earned_points -= 3.0
                    else:
                        missing_optional.append(msg)
                        earned_points -= 1.0

            # Check reasoning depth/type
            elif c_type == "reasoning_depth":
                depth = model.capabilities.get("reasoning", {}).get("chain_of_thought", {}).get("max_depth", 0)
                try:
                    requested_depth = int(c_val)
                except (TypeError, ValueError):
                    reasons.append(f"Constraint '{c_type}' has non-numeric value: {c_val!r}")
                else:
                    if depth and requested_depth > depth:
                        msg = f"Requested reasoning depth {c_val} exceeds model limit of {depth}"
                        if c_pri == ConstraintPriority.MUST:
                            can_fulfill = False
                            reasons.append(f"CRITICAL: {msg}")
                            earned_points -= 2.0
                        else:
                            missing_optional.append(msg)
                            earned_points -= 0.5

        # Calculate score (min 0.0, max 1.0)
        final_score = max(0.0, min(1.0, earned_points / total_points))

        return NegotiationResult(
            can_fulfill=can_fulfill,
            score=round(final_score, 2),
            reasons=reasons,
            missing_optional=missing_optional
        )
