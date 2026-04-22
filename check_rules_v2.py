import sys
from kg.graph_store import InMemoryGraphStore
from eligibility.engine import EligibilityEngine

try:
    g = InMemoryGraphStore()
    print(f"Graph Store type: {type(g)}")
    print(f"Has load: {hasattr(g, 'load')}")
    
    if hasattr(g, 'load'):
        g.load()
        e = EligibilityEngine(g)
        print(f"Total rulesets: {len(e.rulesets)}")
        
        # Look for a scheme that should have structured rules
        found_structured = 0
        for rs in e.rulesets:
            has_structured = any(r.field in ['age', 'gender', 'state', 'category'] for r in rs.rules)
            if has_structured:
                found_structured += 1
                if found_structured <= 5:
                    print(f"Scheme: {rs.scheme_name}")
                    for r in rs.rules:
                        print(f"  - {r}")
                    print("-" * 20)
        
        print(f"Schemes with structured rules: {found_structured} / {len(e.rulesets)}")
    else:
        print("ERROR: InMemoryGraphStore has no 'load' method. Available attributes:")
        print(dir(g))

except Exception as ex:
    print(f"An error occurred: {ex}")
    import traceback
    traceback.print_exc()
