import pandas as pd
from synthetic_generator.validator import DatasetValidator

def test_validator_numeric_and_correlation():
    df_ref = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10]
    })
    df_synth = pd.DataFrame({
        "a": [1.1, 2.1, 2.9, 4.2, 4.8],
        "b": [5, 5, 5, 5, 5]
    })
    
    validator = DatasetValidator()
    results = validator.validate(df_ref, df_synth)
    
    assert "a" in results["columns"]
    assert results["columns"]["a"]["type"] == "numeric"
    assert "ks_statistic" in results["columns"]["a"]
    
    assert results["correlation"]["mean_absolute_correlation_error"] > 0.5
