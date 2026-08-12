import argparse
import pandas as pd
from .analyzer import DatasetAnalyzer
from .generator import SyntheticGenerator
from .validator import DatasetValidator
from .privacy import PrivacyAnalyzer
from .report import ReportGenerator

def analyze_cmd(args):
    df = pd.read_csv(args.input)
    analyzer = DatasetAnalyzer()
    privacy = PrivacyAnalyzer()
    
    schema = analyzer.analyze(df)
    schema.privacy_warnings = privacy.analyze(df)
    
    print(f"Analyzed dataset with {schema.num_rows} rows and {schema.num_columns} columns.")
    # Here we would normally serialize schema if requested

def generate_cmd(args):
    df = pd.read_csv(args.input)
    analyzer = DatasetAnalyzer()
    schema = analyzer.analyze(df)
    
    generator = SyntheticGenerator(seed=args.seed)
    synth_df = generator.generate(schema, num_rows=args.rows)
    
    synth_df.to_csv(args.output, index=False)
    print(f"Generated {args.rows} synthetic rows to {args.output}")

def validate_cmd(args):
    df_ref = pd.read_csv(args.input)
    df_synth = pd.read_csv(args.synthetic)
    
    validator = DatasetValidator()
    results = validator.validate(df_ref, df_synth)
    
    qs = results.get('quality_score', {})
    print(f"Validation complete.")
    print(f"Overall Quality Score: {qs.get('overall', 0):.2f}")

def report_cmd(args):
    df_ref = pd.read_csv(args.input)
    df_synth = pd.read_csv(args.synthetic)
    
    analyzer = DatasetAnalyzer()
    privacy = PrivacyAnalyzer()
    schema = analyzer.analyze(df_ref)
    schema.privacy_warnings = privacy.analyze(df_ref)
    
    validator = DatasetValidator()
    results = validator.validate(df_ref, df_synth)
    
    report_gen = ReportGenerator()
    report = report_gen.generate_report(schema, results)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

def main():
    parser = argparse.ArgumentParser(description="Synthetic Data Quality Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("input", help="Reference dataset CSV")
    analyze_parser.add_argument("--output", help="Output schema JSON file")
    
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("input", help="Reference dataset CSV")
    generate_parser.add_argument("--rows", type=int, required=True, help="Number of rows to generate")
    generate_parser.add_argument("--output", required=True, help="Output synthetic CSV")
    generate_parser.add_argument("--seed", type=int, help="Random seed")
    
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("input", help="Reference dataset CSV")
    validate_parser.add_argument("synthetic", help="Synthetic dataset CSV")
    
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("input", help="Reference dataset CSV")
    report_parser.add_argument("synthetic", help="Synthetic dataset CSV")
    report_parser.add_argument("--output", help="Output Markdown report file")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        analyze_cmd(args)
    elif args.command == "generate":
        generate_cmd(args)
    elif args.command == "validate":
        validate_cmd(args)
    elif args.command == "report":
        report_cmd(args)

if __name__ == "__main__":
    main()
