from typing import Dict, Any, List
from .schema import DatasetSchema, PrivacyWarning

class ReportGenerator:
    def __init__(self):
        pass

    def generate_report(self, schema: DatasetSchema, validation_results: Dict[str, Any]) -> str:
        """Generates a Markdown report from schema and validation results."""
        report = []
        report.append("# Synthetic Data Quality Report\n")
        
        report.append("> [!IMPORTANT]")
        report.append("> This synthetic dataset was generated using statistical sampling and should not be interpreted as a privacy guarantee.\n")
        
        report.append("Numeric Distribution")
        report.append("--------------------")
        
        has_numeric = False
        report.append(f"{'Column':<20}{'KS':<8}{'Mean Error':<14}{'Median Error':<12}")
        for col_name, val_res in validation_results.get("columns", {}).items():
            if val_res.get("type") == "numeric":
                has_numeric = True
                ks = f"{val_res.get('ks_statistic', 0):.4f}"
                mean_err = f"{val_res.get('mean_diff', 0):.4f}"
                med_err = f"{val_res.get('median_diff', 0):.4f}"
                report.append(f"{col_name:<20}{ks:<8}{mean_err:<14}{med_err:<12}")
        
        if not has_numeric:
            report.append("No numeric columns present.")
        
        report.append("\nCorrelation")
        report.append("-----------")
        corr_res = validation_results.get("correlation", {})
        if "mean_absolute_correlation_error" in corr_res:
            report.append(f"Mean Absolute Correlation Error: {corr_res['mean_absolute_correlation_error']:.2f}\n")
        else:
             report.append("Not enough numeric columns to compute correlation error.\n")
             
        report.append("Privacy")
        report.append("--------")
        has_warnings = False
        if schema.privacy_warnings:
            for w in schema.privacy_warnings:
                if w.warning_level != "SAFE":
                    has_warnings = True
                    report.append(f"Potential identifier: {w.column_name} ({w.warning_level})")
        if not has_warnings:
            report.append("No privacy warnings detected.")
            
        report.append("\nOverall Quality Score")
        report.append("---------------------")
        qs = validation_results.get("quality_score", {})
        report.append(f"{qs.get('overall', 0):.1f} / 100\n")
        report.append("*(Note: This is a project-defined composite score, not an industry standard)*\n")
        
        report.append("## Limitations")
        report.append("- V1 assumes independence between columns during generation.")
        report.append("- Extreme outliers in continuous data may not be perfectly replicated.")
        report.append("- Heuristic privacy warnings do not guarantee anonymization.")
        
        return "\n".join(report)
