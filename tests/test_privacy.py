import pandas as pd
from synthetic_generator.privacy import PrivacyAnalyzer

def test_identifier_heuristics():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3, 4],
        "user_email": ["a@b.com", "c@d.com", "e@f.com", "g@h.com"],
        "age": [20, 25, 30, 35],
        "high_cardinality_cat": ["A", "B", "C", "D"]
    })
    
    analyzer = PrivacyAnalyzer()
    warnings = analyzer.analyze(df)
    
    warn_dict = {w.column_name: w for w in warnings}
    
    assert warn_dict["customer_id"].warning_level == "WARNING"
    assert "identifier heuristic" in warn_dict["customer_id"].reason
    
    assert warn_dict["user_email"].warning_level == "WARNING"
    assert warn_dict["age"].warning_level == "SAFE"
    assert warn_dict["high_cardinality_cat"].warning_level == "HIGH-CARDINALITY"
