from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import pandas as pd
import io
import json

from .analyzer import DatasetAnalyzer
from .privacy import PrivacyAnalyzer
from .generator import SyntheticGenerator
from .validator import DatasetValidator

app = FastAPI(title="Synthetic Data Quality API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/generate")
async def generate_synthetic_data(
    file: UploadFile = File(...),
    rows: int = Form(100),
    seed: int = Form(42),
    epsilon: float = Form(None),
    conditional_by: str = Form(None),
    smart_pii: bool = Form(False),
    auto_clean: bool = Form(False)
):
    try:
        content = await file.read()
        df_ref = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    if df_ref.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty")

    try:
        # 1. Analyze
        analyzer = DatasetAnalyzer()
        privacy = PrivacyAnalyzer()
        schema = analyzer.analyze(df_ref, conditional_by=conditional_by, epsilon=epsilon, auto_clean_outliers=auto_clean, smart_pii=smart_pii)
        schema.privacy_warnings = privacy.analyze(df_ref)
        
        # 2. Generate
        generator = SyntheticGenerator(seed=seed)
        df_synth = generator.generate(schema, num_rows=rows)
        
        # 3. Validate
        validator = DatasetValidator()
        validation_results = validator.validate(df_ref, df_synth)
        
        # Format results for the frontend
        privacy_alerts = [
            {"column": w.column_name, "level": w.warning_level, "reason": w.reason}
            for w in schema.privacy_warnings if w.warning_level != "SAFE"
        ]
        
        numeric_dist = []
        for col_name, val_res in validation_results.get("columns", {}).items():
            if val_res.get("type") == "numeric":
                numeric_dist.append({
                    "column": col_name,
                    "ks": val_res.get("ks_statistic", 0),
                    "mean_error": val_res.get("mean_diff", 0),
                    "median_error": val_res.get("median_diff", 0)
                })
                
        qs = validation_results.get("quality_score", {})
        corr_res = validation_results.get("correlation", {})
        
        # Build schema profile for UI
        schema_profile = []
        for col_name, col_schema in schema.columns.items():
            schema_profile.append({
                "column": col_name,
                "type": col_schema.inferred_type,
                "missing_pct": col_schema.missing_percentage,
                "unique": col_schema.num_unique,
                "min": col_schema.min_value if col_schema.min_value is not None else "N/A",
                "max": col_schema.max_value if col_schema.max_value is not None else "N/A",
                "mean": col_schema.mean if col_schema.mean is not None else "N/A",
                "is_primary_key": getattr(col_schema, 'is_primary_key', False),
                "semantic_type": getattr(col_schema, 'semantic_type', None)
            })
            
        report = {
            "dataset": {
                "rows": schema.num_rows,
                "columns": schema.num_columns
            },
            "quality_score": qs.get("overall", 0),
            "correlation_error": corr_res.get("mean_absolute_correlation_error"),
            "privacy_alerts": privacy_alerts,
            "numeric_distribution": numeric_dist,
            "schema_profile": schema_profile
        }
        
        # Convert synthetic dataframe to CSV string
        synth_csv = df_synth.to_csv(index=False)
        
        return {
            "report": report,
            "synthetic_csv": synth_csv
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")
