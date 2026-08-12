# Privacy and Security Considerations

Generating synthetic data inherently obscures the exact rows of the original reference dataset. To ensure enterprise-grade security, this repository implements strict mathematical boundaries and Differential Privacy.

## Differential Privacy (Laplace Mechanism)

The engine provides an optional **Differential Privacy** toggle (`smart_pii=True` / `epsilon=1.0`), which mathematically bounds privacy loss using the Laplace Mechanism.

When enabled:
- **Noise Injection**: Carefully calibrated Laplacian noise is injected directly into the statistical parameters (mean, std) extracted during the analysis phase. 
- **Reconstruction Resistance**: The generated synthetic distributions remain statistically valid at a macro level, but it becomes mathematically impossible for an attacker to reverse-engineer whether a specific individual's data was present in the original dataset.

## Primary Key Protection

The analyzer performs heuristic checks to prevent the replication or statistical modeling of high-risk unique identifiers:
- **Detection**: Columns matching identifier patterns (`id`, `uuid`, `customer_id`) that possess 100% uniqueness are flagged as `is_primary_key`.
- **Anonymization**: Instead of generating empirical text based on real IDs, the generator replaces them entirely with safe, sequential synthetic IDs (`ID-1`, `ID-2`).

## Semantic PII Substitution (Faker)

Columns that contain highly sensitive Personal Identifiable Information (PII) such as:
- `email`, `phone`, `ssn`
- `first_name`, `last_name`, `address`

Are strictly bypassed by the standard statistical categorical sampler. Instead, the engine hands these columns to the `Faker` library, which generates hyper-realistic, yet 100% mathematically fake identities. This guarantees that real emails or phone numbers are never accidentally memorized or re-emitted in the synthetic output.

## Outlier Capping (IQR)

In classical empirical sampling, extreme outliers (e.g., a CEO salary of $50,000,000 among average salaries of $60,000) can cause the exact outlier to be generated, immediately exposing that individual.
- **Auto-Cleaning**: The engine utilizes the Interquartile Range (IQR) to establish upper and lower bounds. 
- **Clipping**: The continuous numerical generation is constrained strictly within these non-outlier bounds, completely severing extreme individual outliers from the synthetic output.
