import pandas as pd
import numpy as np
import scipy.stats as stats
from faker import Faker
from typing import Optional
from .schema import DatasetSchema

class SyntheticGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        
    def generate(self, schema: DatasetSchema, num_rows: int) -> pd.DataFrame:
        """Generates synthetic data based on the provided DatasetSchema."""
        if self.seed is not None:
            np.random.seed(self.seed)
            
        if getattr(schema, 'conditional_schemas', None) is not None:
            group_col = schema.conditional_by_column
            # We assume group_col is categorical or boolean for conditioning
            group_values = self._generate_categorical(schema.columns[group_col], num_rows)
            dfs = []
            for group_val in pd.Series(group_values).dropna().unique():
                count = int(np.sum(group_values == group_val))
                if count > 0:
                    str_val = str(group_val)
                    if str_val in schema.conditional_schemas:
                        sub_df = self.generate(schema.conditional_schemas[str_val], count)
                        sub_df[group_col] = group_val
                        dfs.append(sub_df)
            
            # Handle NaN groups if any
            nan_count = int(np.sum(pd.isna(group_values)))
            if nan_count > 0:
                # If there are missing conditional values, we generate them without condition using root schema (recursively without conditionals)
                schema_no_cond = DatasetSchema(**{k:v for k,v in schema.__dict__.items() if k != 'conditional_schemas'})
                sub_df = self.generate(schema_no_cond, nan_count)
                sub_df[group_col] = np.nan
                dfs.append(sub_df)
                
            if dfs:
                final_df = pd.concat(dfs).sample(frac=1).reset_index(drop=True)
                return final_df
            
        synthetic_data = {}
        
        for col_name, col_schema in schema.columns.items():
            if getattr(col_schema, 'is_primary_key', False):
                if col_schema.inferred_type == "numeric":
                    synthetic_data[col_name] = np.arange(1, num_rows + 1).astype(float)
                else:
                    synthetic_data[col_name] = np.array([f"ID-{i}" for i in range(1, num_rows + 1)])
                continue
                
            if col_schema.inferred_type == "numeric":
                synthetic_data[col_name] = self._generate_numeric(col_schema, num_rows)
            elif col_schema.inferred_type == "categorical":
                synthetic_data[col_name] = self._generate_categorical(col_schema, num_rows)
            elif col_schema.inferred_type == "boolean":
                synthetic_data[col_name] = self._generate_boolean(col_schema, num_rows)
            else:
                print(f"Warning: Column {col_name} has unsupported type {col_schema.inferred_type}. Filled with NaNs.")
                synthetic_data[col_name] = np.full(num_rows, np.nan)
                
        if getattr(schema, 'correlation_matrix', None) is not None:
            numeric_cols = [col for col, sch in schema.columns.items() if sch.inferred_type == "numeric"]
            if len(numeric_cols) > 1:
                corr_matrix = np.zeros((len(numeric_cols), len(numeric_cols)))
                for i, col1 in enumerate(numeric_cols):
                    for j, col2 in enumerate(numeric_cols):
                        corr_matrix[i, j] = schema.correlation_matrix.get(col1, {}).get(col2, 0.0)
                        
                corr_matrix = (corr_matrix + corr_matrix.T) / 2
                np.fill_diagonal(corr_matrix, 1.0)
                
                try:
                    mean = np.zeros(len(numeric_cols))
                    mv_norm = np.random.multivariate_normal(mean, corr_matrix, size=num_rows)
                    
                    for i, col in enumerate(numeric_cols):
                        vals = np.array(synthetic_data[col], dtype=float)
                        valid_idx = ~np.isnan(vals)
                        if np.any(valid_idx):
                            target_ranks = np.argsort(np.argsort(mv_norm[valid_idx, i]))
                            sorted_vals = np.sort(vals[valid_idx])
                            vals[valid_idx] = sorted_vals[target_ranks]
                            synthetic_data[col] = vals
                except Exception as e:
                    print(f"Warning: Gaussian Copula failed ({e}). Falling back to independent margins.")
                    
        df_synth = pd.DataFrame(synthetic_data)
        
        for col_name, col_schema in schema.columns.items():
            if col_schema.inferred_type == "numeric" and not getattr(col_schema, 'is_primary_key', False):
                decimals = getattr(col_schema, 'decimals', 4)
                if decimals == 0:
                    df_synth[col_name] = df_synth[col_name].round(0).astype('Int64')
                else:
                    df_synth[col_name] = df_synth[col_name].round(decimals)
                    
        return df_synth[list(schema.columns.keys())]
        
    def _generate_numeric(self, col_schema, num_rows: int) -> np.ndarray:
        if col_schema.mean is None or col_schema.std_dev is None:
            return np.full(num_rows, np.nan)
            
        if col_schema.std_dev == 0:
            return np.full(num_rows, col_schema.mean)
            
        # Strategy selection
        if getattr(col_schema, 'kde_samples', None) is not None and len(col_schema.kde_samples) > 10:
            # KDE Sampling for Multimodal/Complex distributions
            kde = stats.gaussian_kde(col_schema.kde_samples)
            values = kde.resample(num_rows)[0]
            if col_schema.min_value is not None and col_schema.max_value is not None:
                values = np.clip(values, col_schema.min_value, col_schema.max_value)
        elif getattr(col_schema, 'is_discrete', False) and col_schema.histogram_counts is not None:
            # Empirical sampling for discrete data
            bins = col_schema.histogram_bins[:-1]
            counts = col_schema.histogram_counts
            probs = np.array(counts) / sum(counts)
            values = np.random.choice(bins, size=num_rows, p=probs)
        elif getattr(col_schema, 'skewness', 0) is not None and abs(col_schema.skewness) > 1.0 and col_schema.histogram_counts is not None:
            # Empirical sampling for highly skewed distributions
            counts = col_schema.histogram_counts
            bins = col_schema.histogram_bins
            probs = np.array(counts) / sum(counts)
            bin_indices = np.random.choice(len(counts), size=num_rows, p=probs)
            
            left_edges = np.array(bins)[bin_indices]
            right_edges = np.array(bins)[bin_indices + 1]
            values = np.random.uniform(left_edges, right_edges)
        elif getattr(col_schema, 'skewness', 0) is not None and abs(col_schema.skewness) < 0.5:
            # Normal-like distribution
            if col_schema.min_value is not None and col_schema.max_value is not None:
                a = (col_schema.min_value - col_schema.mean) / col_schema.std_dev
                b = (col_schema.max_value - col_schema.mean) / col_schema.std_dev
                values = stats.truncnorm.rvs(a, b, loc=col_schema.mean, scale=col_schema.std_dev, size=num_rows)
            else:
                values = np.random.normal(loc=col_schema.mean, scale=col_schema.std_dev, size=num_rows)
        else:
            # Fallback uniform-like or moderately skewed
            if col_schema.min_value is not None and col_schema.max_value is not None:
                values = np.random.uniform(col_schema.min_value, col_schema.max_value, size=num_rows)
            else:
                values = np.random.normal(loc=col_schema.mean, scale=col_schema.std_dev, size=num_rows)
        
        # Enforce discrete type if needed
        if getattr(col_schema, 'is_discrete', False):
            values = np.round(values)
            
        # Add NaNs preserving the exact ratio deterministically
        if col_schema.missing_percentage > 0:
            num_missing = int((col_schema.missing_percentage / 100) * num_rows)
            indices = np.random.choice(num_rows, num_missing, replace=False)
            values = values.astype(float)
            values[indices] = np.nan
            
        return values

    def _generate_categorical(self, col_schema, num_rows: int) -> np.ndarray:
        if getattr(col_schema, 'semantic_type', None):
            fake = Faker()
            if self.seed is not None:
                Faker.seed(self.seed + hash(col_schema.column_name) % 10000)
                
            st = col_schema.semantic_type
            if st == "email":
                values = np.array([fake.email() for _ in range(num_rows)])
            elif st == "first_name":
                values = np.array([fake.first_name() for _ in range(num_rows)])
            elif st == "last_name":
                values = np.array([fake.last_name() for _ in range(num_rows)])
            elif st == "name":
                values = np.array([fake.name() for _ in range(num_rows)])
            elif st == "phone_number":
                values = np.array([fake.phone_number() for _ in range(num_rows)])
            elif st == "address":
                values = np.array([fake.address().replace('\n', ', ') for _ in range(num_rows)])
            elif st == "city":
                values = np.array([fake.city() for _ in range(num_rows)])
            elif st == "zipcode":
                values = np.array([fake.zipcode() for _ in range(num_rows)])
            elif st == "country":
                values = np.array([fake.country() for _ in range(num_rows)])
            elif st == "company":
                values = np.array([fake.company() for _ in range(num_rows)])
            else:
                values = np.array([fake.word() for _ in range(num_rows)])
        else:
            if not col_schema.category_frequencies:
                return np.full(num_rows, np.nan, dtype=object)
                
            categories = list(col_schema.category_frequencies.keys())
            probabilities = list(col_schema.category_frequencies.values())
            
            total_prob = sum(probabilities)
            if total_prob > 0:
                probabilities = [p / total_prob for p in probabilities]
            else:
                return np.full(num_rows, np.nan, dtype=object)
                
            values = np.random.choice(categories, size=num_rows, p=probabilities)
        
        if col_schema.missing_percentage > 0:
            num_missing = int((col_schema.missing_percentage / 100) * num_rows)
            indices = np.random.choice(num_rows, num_missing, replace=False)
            values = values.astype(object)
            values[indices] = np.nan
            
        return values
        
    def _generate_boolean(self, col_schema, num_rows: int) -> np.ndarray:
        if not col_schema.category_frequencies:
             return np.full(num_rows, np.nan, dtype=object)
             
        categories = list(col_schema.category_frequencies.keys())
        probabilities = list(col_schema.category_frequencies.values())
        
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
        else:
            return np.full(num_rows, np.nan, dtype=object)
            
        values = np.random.choice(categories, size=num_rows, p=probabilities)
        
        if col_schema.missing_percentage > 0:
            num_missing = int((col_schema.missing_percentage / 100) * num_rows)
            indices = np.random.choice(num_rows, num_missing, replace=False)
            values = values.astype(object)
            values[indices] = np.nan
            
        return values
