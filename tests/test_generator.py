import pandas as pd
from synthetic_generator.analyzer import DatasetAnalyzer
from synthetic_generator.generator import SyntheticGenerator

def test_deterministic_generation():
    df = pd.DataFrame({
        "val": [1, 2, 3, 4, 5],
        "cat": ["A", "B", "A", "B", "C"]
    })
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    gen1 = SyntheticGenerator(seed=42)
    df1 = gen1.generate(schema, 10)
    
    gen2 = SyntheticGenerator(seed=42)
    df2 = gen2.generate(schema, 10)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_numeric_range_enforcement():
    df = pd.DataFrame({"val": [10, 20, 20]})
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    schema.columns["val"].std_dev = 1000.0
    
    gen = SyntheticGenerator(seed=42)
    df_synth = gen.generate(schema, 100)
    
    assert df_synth["val"].max() <= 20
    assert df_synth["val"].min() >= 10
