from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class PrivacyWarning:
    column_name: str
    warning_level: str  # e.g., "SAFE", "WARNING", "HIGH-CARDINALITY"
    reason: str

@dataclass
class ColumnSchema:
    column_name: str
    inferred_type: str  # "numeric", "categorical", "boolean", "datetime", "unsupported"
    nullable: bool
    num_unique: int
    missing_count: int
    missing_percentage: float
    
    # Numeric specifics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    median: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    is_discrete: bool = False
    histogram_counts: Optional[List[int]] = None
    histogram_bins: Optional[List[float]] = None
    quantiles: Dict[str, float] = field(default_factory=dict)
    
    # Categorical/Boolean specifics
    category_frequencies: Dict[Any, float] = field(default_factory=dict)
    
    # 10x Impact Upgrades
    is_primary_key: bool = False
    kde_samples: Optional[List[float]] = None
    semantic_type: Optional[str] = None
    decimals: int = 4

@dataclass
class DatasetSchema:
    num_rows: int
    num_columns: int
    columns: Dict[str, ColumnSchema]
    privacy_warnings: List[PrivacyWarning] = field(default_factory=list)
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    
    # 10x Impact Upgrades
    conditional_by_column: Optional[str] = None
    conditional_schemas: Optional[Dict[str, 'DatasetSchema']] = None
    dp_epsilon: Optional[float] = None
