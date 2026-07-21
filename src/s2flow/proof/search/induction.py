"""Dependency tracking for an induction-by-reductions program."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class InductionNode:
    statement: str
    verified: bool = False
    dependencies: list[str] = field(default_factory=list)

def verify_induction_plan(nodes: list[InductionNode]) -> dict[str, object]:
    """Check for missing dependencies and cycles in a finite proof plan."""
    by_name={node.statement: node for node in nodes}
    missing=sorted({dep for node in nodes for dep in node.dependencies if dep not in by_name})
    visiting=set(); visited=set(); cycles=[]
    def visit(name, path):
        if name in visiting:
            cycles.append(path[path.index(name):] + [name]); return
        if name in visited or name not in by_name: return
        visiting.add(name)
        for dep in by_name[name].dependencies: visit(dep, path+[dep])
        visiting.remove(name); visited.add(name)
    for name in by_name: visit(name,[name])
    return {"valid": not missing and not cycles, "missing_dependencies": missing, "cycles": cycles, "all_verified": all(node.verified for node in nodes)}
