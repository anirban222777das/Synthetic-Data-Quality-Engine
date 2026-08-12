# Limitations

While this tool generates high-quality synthetic data for tabular datasets, the classical statistical approach inherently carries several limitations.

## 1. Complex Dependencies
While the Iman-Conover Gaussian Copula preserves linear rank-order correlations (Spearman's rank correlation), it is incapable of modeling non-linear, higher-order dependencies or complex conditional logic. 
For example, if `pregnancy_status == True` is strictly dependent on `gender == Female`, a Gaussian Copula may still occasionally generate a male with a true pregnancy status because the linear correlation matrix does not enforce absolute deterministic rules. 

## 2. Small Sample Sizes
Empirical sampling strategies (used for categorical, discrete, and highly skewed data) rely heavily on the Law of Large Numbers. If a reference dataset is very small (e.g., < 100 rows), the generated synthetic dataset will almost exactly replicate the input data, providing very little generative variance and posing a high privacy risk.

## 3. High-Cardinality Categorical Columns
Categorical columns with thousands of unique values (like Zip Codes, UUIDs, or free-text names) are not synthesized elegantly. The system utilizes weighted random choice based on observed frequency, meaning it will only ever output strings it has seen before. It will not generate "new" unique identifiers, and if a category only appeared once in the reference data, generating it again inherently risks leaking information about the original dataset.

## 4. Free-text and Unstructured Data
This tool is strictly designed for structured, tabular data. It cannot generate synthetic sentences, paragraphs, or NLP text embeddings. Any unstructured text column is treated as a high-cardinality categorical column, which will likely fail privacy heuristics and yield poor statistical utility.
