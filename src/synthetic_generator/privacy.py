from .schema import PrivacyWarning
import pandas as pd
from typing import List

class PrivacyAnalyzer:
    def __init__(self):
        self.identifier_heuristics = [
            "id", "user_id", "customer_id", "email", "phone", "name", "address",
            "ssn", "ip_address", "uuid", "guid"
        ]
        
    def analyze(self, df: pd.DataFrame) -> List[PrivacyWarning]:
        """Analyzes a DataFrame for potential privacy identifiers using heuristics."""
        warnings = []
        num_rows = len(df)
        
        if num_rows == 0:
            return warnings
            
        for col in df.columns:
            series = df[col]
            col_lower = str(col).lower()
            
            is_identifier_name = any(h == col_lower or h in col_lower.split('_') for h in self.identifier_heuristics)
            
            if pd.api.types.is_numeric_dtype(series) and not is_identifier_name:
                 warnings.append(PrivacyWarning(
                    column_name=str(col),
                    warning_level="SAFE",
                    reason="Numeric column not matching identifier heuristic."
                ))
                 continue
                
            num_unique = series.nunique()
            uniqueness_ratio = num_unique / num_rows if num_rows > 0 else 0
            
            if is_identifier_name:
                warnings.append(PrivacyWarning(
                    column_name=str(col),
                    warning_level="WARNING",
                    reason=f"Column name matches identifier heuristic. Uniqueness ratio: {uniqueness_ratio:.2f}"
                ))
            elif uniqueness_ratio > 0.8 and pd.api.types.is_string_dtype(series):
                warnings.append(PrivacyWarning(
                    column_name=str(col),
                    warning_level="HIGH-CARDINALITY",
                    reason=f"High cardinality categorical column ({uniqueness_ratio:.0%} unique values). Potential identifier."
                ))
            else:
                 warnings.append(PrivacyWarning(
                    column_name=str(col),
                    warning_level="SAFE",
                    reason="Did not flag identifier heuristics."
                ))
                 
        return warnings
