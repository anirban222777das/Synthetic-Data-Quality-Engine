import pandas as pd
import numpy as np
from typing import Dict, Any
from .schema import DatasetSchema, ColumnSchema

class DatasetAnalyzer:
    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame, conditional_by: str = None, epsilon: float = None, auto_clean_outliers: bool = False, smart_pii: bool = False) -> DatasetSchema:
        """Analyzes a pandas DataFrame and produces a DatasetSchema."""
        self.epsilon = epsilon
        self.auto_clean_outliers = auto_clean_outliers
        self.smart_pii = smart_pii
        
        if conditional_by and conditional_by in df.columns:
            return self._analyze_conditional(df, conditional_by)
            
        num_rows = len(df)
        num_columns = len(df.columns)
        columns_schema = {}

        for col_name in df.columns:
            series = df[col_name]
            columns_schema[col_name] = self._analyze_column(col_name, series, num_rows)
            
        numeric_df = df.select_dtypes(include=[np.number])
        correlation_matrix = None
        if len(numeric_df.columns) > 1:
            try:
                corr = numeric_df.corr(method="spearman").fillna(0)
                correlation_matrix = corr.to_dict()
            except Exception:
                pass
                
        return DatasetSchema(
            num_rows=num_rows,
            num_columns=num_columns,
            columns=columns_schema,
            correlation_matrix=correlation_matrix,
            dp_epsilon=self.epsilon
        )

    def _analyze_conditional(self, df: pd.DataFrame, conditional_by: str) -> DatasetSchema:
        root_schema = self.analyze(df, conditional_by=None, epsilon=self.epsilon, auto_clean_outliers=self.auto_clean_outliers, smart_pii=self.smart_pii)
        root_schema.conditional_by_column = conditional_by
        root_schema.conditional_schemas = {}
        
        for group_val, group_df in df.groupby(conditional_by):
            # Pass options down, but do not recurse conditional_by
            sub_schema = self.analyze(group_df, conditional_by=None, epsilon=self.epsilon, auto_clean_outliers=self.auto_clean_outliers, smart_pii=self.smart_pii)
            root_schema.conditional_schemas[str(group_val)] = sub_schema
            
        return root_schema

    def _analyze_column(self, col_name: str, series: pd.Series, total_rows: int) -> ColumnSchema:
        missing_count = int(series.isna().sum())
        missing_percentage = (missing_count / total_rows) * 100 if total_rows > 0 else 0.0
        
        valid_series = series.dropna()
        num_unique = int(valid_series.nunique())
        
        inferred_type = self._infer_type(valid_series)
        
        schema = ColumnSchema(
            column_name=col_name,
            inferred_type=inferred_type,
            nullable=missing_count > 0,
            num_unique=num_unique,
            missing_count=missing_count,
            missing_percentage=missing_percentage
        )
        
        is_id_name = any(x in col_name.lower() for x in ["id", "uuid", "key", "index", "hash"])
        if num_unique == total_rows - missing_count and num_unique > 0 and is_id_name:
            schema.is_primary_key = True
        
        if inferred_type == "numeric" and not valid_series.empty:
            schema.mean = float(valid_series.mean())
            schema.std_dev = float(valid_series.std()) if len(valid_series) > 1 else 0.0
            schema.median = float(valid_series.median())
            
            schema.q1 = float(valid_series.quantile(0.25))
            schema.q3 = float(valid_series.quantile(0.75))
            schema.iqr = schema.q3 - schema.q1
            schema.skewness = float(valid_series.skew()) if len(valid_series) > 2 else 0.0
            
            if getattr(self, "auto_clean_outliers", False):
                lower_bound = schema.q1 - 1.5 * schema.iqr
                upper_bound = schema.q3 + 1.5 * schema.iqr
                schema.min_value = float(max(valid_series.min(), lower_bound))
                schema.max_value = float(min(valid_series.max(), upper_bound))
            else:
                schema.min_value = float(valid_series.min())
                schema.max_value = float(valid_series.max())
                
            is_integer_type = pd.api.types.is_integer_dtype(valid_series)
            all_integers = is_integer_type or np.all(np.mod(valid_series, 1) == 0)
            
            if all_integers:
                schema.decimals = 0
            else:
                def count_decimals(val):
                    if pd.isna(val): return 0
                    s = str(val).rstrip('0')
                    if '.' in s: return len(s.split('.')[1])
                    return 0
                max_decimals = valid_series.head(100).apply(count_decimals).max()
                schema.decimals = int(max_decimals) if max_decimals <= 4 else 4
                
            if all_integers and (num_unique < 20 or num_unique / max(1, len(valid_series)) < 0.05):
                 schema.is_discrete = True
                 
            if len(valid_series) > 1:
                counts, bins = np.histogram(valid_series, bins='auto')
                schema.histogram_counts = [int(c) for c in counts]
                schema.histogram_bins = [float(b) for b in bins]

            schema.quantiles = {
                "25%": schema.q1,
                "50%": schema.median,
                "75%": schema.q3
            }
            
            # Save raw samples for KDE if no strict privacy budget is enforced, and it's not a PK
            if getattr(self, "epsilon", None) is None and not schema.is_primary_key and not schema.is_discrete:
                schema.kde_samples = valid_series.sample(n=min(1000, len(valid_series)), replace=False).astype(float).tolist()
                
            # Apply Differential Privacy (Laplace Mechanism) to numeric moments
            if getattr(self, "epsilon", None) is not None:
                sensitivity = (schema.max_value - schema.min_value) / max(1, len(valid_series))
                scale = sensitivity / self.epsilon
                schema.mean += np.random.laplace(0, scale)
                schema.std_dev += np.random.laplace(0, scale)
                if schema.histogram_counts:
                    # Count sensitivity is 1
                    count_scale = 1.0 / self.epsilon
                    schema.histogram_counts = [max(0, int(c + np.random.laplace(0, count_scale))) for c in schema.histogram_counts]
        
        elif inferred_type in ("categorical", "boolean") and not valid_series.empty:
            counts = valid_series.value_counts(normalize=False)
            
            if getattr(self, "epsilon", None) is not None:
                count_scale = 1.0 / self.epsilon
                counts = counts.apply(lambda x: max(0, x + np.random.laplace(0, count_scale)))
                
            total_count = counts.sum()
            if total_count > 0:
                schema.category_frequencies = (counts / total_count).to_dict()
            else:
                schema.category_frequencies = valid_series.value_counts(normalize=True).to_dict()
                
            if getattr(self, "smart_pii", False) and inferred_type == "categorical":
                col_lower = col_name.lower()
                if any(x in col_lower for x in ["email", "e-mail"]):
                    schema.semantic_type = "email"
                elif any(x in col_lower for x in ["first_name", "fname"]):
                    schema.semantic_type = "first_name"
                elif any(x in col_lower for x in ["last_name", "lname"]):
                    schema.semantic_type = "last_name"
                elif any(x in col_lower for x in ["name"]):
                    schema.semantic_type = "name"
                elif any(x in col_lower for x in ["phone", "mobile", "cell"]):
                    schema.semantic_type = "phone_number"
                elif any(x in col_lower for x in ["address", "street"]):
                    schema.semantic_type = "address"
                elif any(x in col_lower for x in ["city", "town"]):
                    schema.semantic_type = "city"
                elif any(x in col_lower for x in ["zip", "postal"]):
                    schema.semantic_type = "zipcode"
                elif any(x in col_lower for x in ["country"]):
                    schema.semantic_type = "country"
                elif any(x in col_lower for x in ["company", "organization", "employer"]):
                    schema.semantic_type = "company"
            
        return schema

    def _infer_type(self, series: pd.Series) -> str:
        if series.empty:
            return "unsupported"
            
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_bool_dtype(series):
                return "boolean"
            return "numeric"
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_categorical_dtype(series) or pd.api.types.is_object_dtype(series):
            return "categorical"
        
        return "unsupported"
