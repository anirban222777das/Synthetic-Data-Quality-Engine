import pandas as pd
import numpy as np
from synthetic_generator.analyzer import DatasetAnalyzer

def test_analyze_numeric():
    df = pd.DataFrame({
        "age": [25, 30, 35, np.nan],
        "salary": [50000, 60000, 70000, 80000]
    })
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    assert schema.num_rows == 4
    assert schema.num_columns == 2
    
    age_col = schema.columns["age"]
    assert age_col.inferred_type == "numeric"
    assert age_col.nullable is True
    assert age_col.missing_count == 1
    assert age_col.mean == 30.0
    
    salary_col = schema.columns["salary"]
    assert salary_col.inferred_type == "numeric"
    assert salary_col.nullable is False
    assert salary_col.min_value == 50000
    assert salary_col.max_value == 80000

def test_analyze_categorical():
    df = pd.DataFrame({
        "color": ["red", "blue", "red", "green"]
    })
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    color_col = schema.columns["color"]
    assert color_col.inferred_type == "categorical"
    assert color_col.num_unique == 3
    assert color_col.category_frequencies["blue"] == 0.25

def test_analyze_discrete_and_skew():
    df = pd.DataFrame({
        "discrete": [1, 2, 3, 4, 5] * 6,
        "skewed": list(range(25)) + [1000, 2000, 3000, 4000, 5000]
    })
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    assert schema.columns["discrete"].is_discrete is True
    assert schema.columns["skewed"].is_discrete is False
    assert schema.columns["skewed"].skewness > 1.0
    assert schema.columns["skewed"].q1 is not None
    assert schema.columns["skewed"].histogram_counts is not None
