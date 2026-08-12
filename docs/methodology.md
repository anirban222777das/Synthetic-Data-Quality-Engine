# Methodology

The `synthetic-data-quality` generation engine relies on classical statistical methods to profile and generate data. It intentionally avoids Neural Networks, LLMs, and GANs to ensure transparency, extreme speed, and mathematical predictability.

## Data Type Inference

When data is ingested, the engine automatically profiles and classifies every column:
- **Primary Keys**: Columns that contain ID markers (e.g. `uuid`, `id`) and have 100% uniqueness are classified as Primary Keys. The generator replaces them with synthetic sequential counters (`ID-1`, `ID-2`).
- **Semantic PII (Faker)**: Columns like `email`, `first_name`, or `address` are flagged. During generation, they are bypassed by the statistical sampler and instead handed to the `Faker` library, which generates highly realistic, semantically accurate fake identities.
- **Discrete vs Continuous Numerics**: Numeric data is tested for uniqueness. If a numeric column has very few unique values, or is strictly integer-based with no decimals, its exact mathematical precision is preserved.
- **Categorical / Text**: Any remaining textual or boolean columns are sampled based on their normalized frequency distributions.

## Numeric Generation (Gaussian Copulas)

To ensure that statistical correlations (e.g., Age vs Income) are preserved, the engine utilizes a **Gaussian Copula**.

- **Marginal Profiling**: The independent marginal distribution (Mean and Standard Deviation) is computed for every continuous numeric column. 
- **Correlation Matrix**: A Pearson correlation matrix is calculated between all numeric variables.
- **Multivariate Normal Sampling**: During synthesis, a standard multivariate normal distribution is generated using the Cholesky decomposition of the correlation matrix. This guarantees the synthetic rows share the exact same correlation as the original data.
- **Inverse Transform**: The correlated normal samples are inverted back into the marginal distributions of the original columns.

## Auto-Outlier Mitigation (IQR)

Real-world datasets often contain massive outliers that can artificially skew the mean and standard deviation, causing the Gaussian copulas to generate unrealistic data boundaries.
If `auto_clean_outliers` is enabled, the analyzer enforces **Interquartile Range (IQR) capping**:
- It calculates Q1 (25th percentile) and Q3 (75th percentile).
- The acceptable numeric bounds are locked at `[Q1 - 1.5 * IQR, Q3 + 1.5 * IQR]`.
- Synthesized numbers that exceed these bounds are mathematically clipped, ensuring stable, realistic bell curves in the synthetic output.

## Conditional Sub-schemas

For complex datasets where distributions vary wildly depending on a categorical label (e.g., the `Income` of a "Manager" is fundamentally different from a "Cashier"), the analyzer splits the data logically.
- The engine identifies the categorical column with the highest mathematical correlation to the target numeric columns.
- It groups the entire dataset by this label and creates independent sub-schemas for every group.
- It generates the synthetic data proportionally, merging the independent sub-schemas back together to ensure hyper-localized accuracy.
