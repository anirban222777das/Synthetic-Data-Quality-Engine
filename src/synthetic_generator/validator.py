import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from typing import Dict, Any

class DatasetValidator:
    def __init__(self):
        pass

    def validate(self, df_ref: pd.DataFrame, df_synth: pd.DataFrame) -> Dict[str, Any]:
        """Compares reference dataset with synthetic dataset."""
        results = {
            "columns": {},
            "correlation": {}
        }
        
        for col in df_ref.columns:
            if col not in df_synth.columns:
                continue
                
            ref_series = df_ref[col].dropna()
            synth_series = df_synth[col].dropna()
            
            if pd.api.types.is_bool_dtype(ref_series):
                 results["columns"][col] = self._validate_categorical(ref_series, synth_series)
            elif pd.api.types.is_numeric_dtype(ref_series):
                 results["columns"][col] = self._validate_numeric(ref_series, synth_series)
            elif pd.api.types.is_string_dtype(ref_series) or pd.api.types.is_categorical_dtype(ref_series):
                 results["columns"][col] = self._validate_categorical(ref_series, synth_series)
                 
        results["correlation"] = self._validate_correlation(df_ref, df_synth)
        results["quality_score"] = self._calculate_quality_score(results)
        
        return results
        
    def _validate_numeric(self, ref_series: pd.Series, synth_series: pd.Series) -> Dict[str, Any]:
        if ref_series.empty or synth_series.empty:
            return {"type": "numeric", "status": "empty"}
            
        ks_stat, p_value = ks_2samp(ref_series, synth_series)
        
        mean_ref, mean_synth = ref_series.mean(), synth_series.mean()
        median_ref, median_synth = ref_series.median(), synth_series.median()
        std_ref, std_synth = (ref_series.std(), synth_series.std()) if len(ref_series)>1 and len(synth_series)>1 else (0, 0)
        
        q_ref = ref_series.quantile([0.25, 0.5, 0.75]).values
        q_synth = synth_series.quantile([0.25, 0.5, 0.75]).values
        q_diff = np.mean(np.abs(q_ref - q_synth))
        
        norm_mean = abs(mean_ref - mean_synth) / max(abs(mean_ref), 1e-5)
        norm_median = abs(median_ref - median_synth) / max(abs(median_ref), 1e-5)
        norm_std = abs(std_ref - std_synth) / max(abs(std_ref), 1e-5)
        norm_q = q_diff / max(np.mean(np.abs(q_ref)), 1e-5)
        
        numeric_dist_err = float(np.mean([norm_mean, norm_median, norm_std, norm_q]))
        
        return {
            "type": "numeric",
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(p_value),
            "mean_diff": float(abs(mean_ref - mean_synth)),
            "median_diff": float(abs(median_ref - median_synth)),
            "std_diff": float(abs(std_ref - std_synth)),
            "quantile_diff": float(q_diff),
            "numeric_distribution_error": numeric_dist_err,
            "range_ref": (float(ref_series.min()), float(ref_series.max())),
            "range_synth": (float(synth_series.min()), float(synth_series.max()))
        }
        
    def _validate_categorical(self, ref_series: pd.Series, synth_series: pd.Series) -> Dict[str, Any]:
        if ref_series.empty or synth_series.empty:
            return {"type": "categorical", "status": "empty"}
            
        ref_counts = ref_series.value_counts(normalize=True)
        synth_counts = synth_series.value_counts(normalize=True)
        
        all_categories = set(ref_counts.index).union(set(synth_counts.index))
        ref_freqs = np.array([ref_counts.get(c, 0.0) for c in all_categories])
        synth_freqs = np.array([synth_counts.get(c, 0.0) for c in all_categories])
        
        freq_diff = np.mean(np.abs(ref_freqs - synth_freqs))
        
        return {
            "type": "categorical",
            "mean_freq_diff": float(freq_diff)
        }
        
    def _validate_correlation(self, df_ref: pd.DataFrame, df_synth: pd.DataFrame) -> Dict[str, Any]:
        numeric_cols_ref = df_ref.select_dtypes(include=[np.number]).columns
        numeric_cols_synth = df_synth.select_dtypes(include=[np.number]).columns
        common_cols = list(set(numeric_cols_ref).intersection(set(numeric_cols_synth)))
        
        if len(common_cols) < 2:
            return {"status": "Not enough numeric columns"}
            
        corr_ref = df_ref[common_cols].corr().fillna(0).values
        corr_synth = df_synth[common_cols].corr().fillna(0).values
        
        diff = np.abs(corr_ref - corr_synth)
        mean_abs_corr_error = np.mean(diff)
        
        return {
            "mean_absolute_correlation_error": float(mean_abs_corr_error)
        }

    def _calculate_quality_score(self, results: Dict[str, Any]) -> Dict[str, float]:
        numeric_ks_scores = []
        numeric_dist_errors = []
        for col, res in results["columns"].items():
            if res.get("type") == "numeric" and "ks_statistic" in res:
                numeric_ks_scores.append(1.0 - res["ks_statistic"])
                numeric_dist_errors.append(res.get("numeric_distribution_error", 0))
                
        dist_sim = float(np.mean(numeric_ks_scores)) if numeric_ks_scores else 1.0
        avg_dist_err = float(np.mean(numeric_dist_errors)) if numeric_dist_errors else 0.0
        
        corr_err = results.get("correlation", {}).get("mean_absolute_correlation_error", 0.0)
        corr_preservation = max(0.0, 1.0 - corr_err)
        
        dist_err_score = max(0.0, 1.0 - avg_dist_err)
        overall = ((dist_sim * 0.4) + (dist_err_score * 0.4) + (corr_preservation * 0.2)) * 100.0
        
        return {
            "distribution_similarity": dist_sim,
            "correlation_preservation": corr_preservation,
            "average_numeric_distribution_error": avg_dist_err,
            "overall": overall
        }
