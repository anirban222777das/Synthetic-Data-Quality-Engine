# Validation Metrics

The `validator.py` module quantitatively assesses the fidelity of the synthetic data against the original reference dataset using a suite of statistical tests.

## Numeric Distribution Error

This is a composite diagnostic metric designed to evaluate the shift in fundamental statistical moments. For a given numeric column, the error is computed as the mean of the normalized absolute differences between:

1. Reference Mean and Synthetic Mean
2. Reference Median and Synthetic Median
3. Reference Standard Deviation and Synthetic Standard Deviation
4. Reference Quantiles (Q1, Q2, Q3) and Synthetic Quantiles

A lower `numeric_distribution_error` indicates that the central tendency and spread of the generated data closely mirror the original dataset.

## Kolmogorov-Smirnov (KS) Statistic

For numeric data, the system calculates the two-sample KS statistic (`scipy.stats.ks_2samp`). This measures the maximum distance between the empirical cumulative distribution functions (ECDF) of the reference and synthetic data.

*Interpretation*: The KS statistic ranges from 0 to 1, where 0 implies the distributions are identical. While p-values are returned by the API, they are omitted from the high-level quality score because KS p-values become overly sensitive at large sample sizes, falsely rejecting highly similar distributions.

## Correlation Preservation Error

To evaluate whether multivariate dependencies survived the generation process, the validator computes the Spearman rank correlation matrix for both the reference and synthetic datasets. 

The `mean_absolute_correlation_error` is the average absolute difference between the off-diagonal elements of the two correlation matrices.

## Composite Quality Score

The final `quality_score` (0-100) is a project-defined diagnostic metric—*it is not an industry standard*. It is designed to give an immediate, intuitive read on the overall synthesis quality.

The score is a weighted composite:
- **Distribution Similarity (40%)**: Derived from the KS statistics across all numeric columns.
- **Distribution Error (40%)**: Derived from the composite numeric shift errors (mean, median, standard deviation).
- **Correlation Preservation (20%)**: Derived from the mean absolute correlation error.

> [!NOTE]
> The Quality Score is heavily weighted toward preserving univariate marginal distributions. A high score guarantees that individual columns look statistically correct, but users must manually inspect the correlation error to ensure complex inter-column relationships are maintained.
