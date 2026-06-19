# Academic Critical Evaluation — Smart Shelf Life Prediction Pipeline

This report assesses the methodological rigor, statistical validity, and academic peer-review readiness of the **Smart Shelf Life Prediction Model** pipeline. 

---

## 1. Methodological Critique: Data Leakage and Validation Rigor

### The Issue
In academic research, the integrity of the train/test split is paramount. Currently, the dataset splitting in [src/train.py](file:///c:/Users/julth/repo/Smart-Shelf-Life-Prediction-Model/src/train.py#L166-L174) divides the data based on indices of a flat DataFrame:

```python
train_df = df.iloc[:train_size].reset_index(drop=True)
val_df   = df.iloc[train_size:].reset_index(drop=True)
```

Because `preprocessed_data.csv` is sorted chronologically by day indices, and because multiple images are generated for the same sample (fruit) on any given day, a random shuffle or slice leads to **severe data leakage**. Images of the *same mango sample* under identical conditions on the same day appear in both the training set and the validation set. 
Consequently, the validation metrics (MAE: ~1.6 days) are artificially optimistic, as the model is evaluated on images nearly identical to those it has trained on. This is a critical error that would lead to immediate rejection during peer review.

### The Mitigation: Group-Based Splitting
To solve this, split the dataset by **unique mango fruit IDs** (groups) rather than by individual rows. A single mango’s entire degradation history must be kept entirely inside either the train set or the validation set.

#### Implementation Blueprint (`GroupKFold` / Group splitting):
```python
import pandas as pd
from sklearn.model_selection import GroupKFold

# 1. Extract the Sample ID (e.g. 'aad1', 'cbnd3') from the Image Path
# Path example: .\data\mango\ambient-environment\non-destructive\day-1\aad1img1d1.png
def extract_sample_id(image_path):
    # Extracts the prefix + sample index (e.g., 'aad1', 'cbnd3')
    filename = image_path.split('\\')[-1]
    # Match letters followed by digits (e.g. aand3 or cbd2) before "img"
    import re
    match = re.match(r'^([a-zA-Z]+\d+)', filename)
    return match.group(1) if match else 'unknown'

df = pd.read_csv('preprocessed_data.csv')
df['Sample_ID'] = df['Image Path'].apply(extract_sample_id)

# 2. Perform GroupKFold Split
gkf = GroupKFold(n_splits=5)
groups = df['Sample_ID']

for fold, (train_idx, val_idx) in enumerate(gkf.split(df, groups=groups)):
    train_df = df.iloc[train_idx].reset_index(drop=True)
    val_df   = df.iloc[val_idx].reset_index(drop=True)
    print(f"Fold {fold} | Train samples: {len(train_df)} | Val samples: {len(val_df)}")
    break # Train on the first fold
```

---

## 2. Hypothesis Testing: Ablation Studies

Peer-reviewed journals require proof that a multimodal network actually out-performs unimodal baselines. This is achieved via an **ablation study**. 

We recommend implementing and reporting comparative results across three models:

1.  **Baseline 1: Visual-Only Model**
    *   *Architecture*: Train only `ImageBackbone` + a single linear regression projection head.
    *   *Evaluation*: Measures how much shelf life can be predicted solely from skin color changes.
2.  **Baseline 2: Tabular-Only Model**
    *   *Architecture*: Train only the `TabularFeatureEncoder` + `TabularBranch` + regression head.
    *   *Evaluation*: Measures the predictive power of ambient temperature, humidity, and environment category.
3.  **Proposed Model: Multimodal Fusion**
    *   *Architecture*: The current complete model fusing image and tabular embeddings.

### Recommended Academic Reporting Matrix:

| Model Version | Parameters Trained | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) | R² Coefficient |
| :--- | :--- | :---: | :---: | :---: |
| **Tabular-Only Baseline** | ~14k | *TBD* | *TBD* | *TBD* |
| **Image-Only Baseline** | ~330k | *TBD* | *TBD* | *TBD* |
| **Multimodal Fusion (Ours)** | **~416k** | **`1.62`** | **`1.86`** | *TBD* |

---

## 3. Statistical Validity: K-Fold Cross-Validation

Reporting metrics from a single random train/val split is methodologically weak due to variance. 
*   **Standard**: Use **5-Fold Group Cross-Validation**.
*   **Report**: Report the validation metrics as $\text{mean} \pm \text{standard deviation}$ (e.g., $\text{MAE} = 1.62 \pm 0.14 \text{ days}$). This demonstrates statistical reliability and robustness to different samples.

---

## 4. Limitations & Future Directions (Academic Discussion Section)

A strong research paper must critique its own boundaries. In your thesis or publication, include the following limitations:

### A. Ambient "Snapshot" Assumption vs. Cumulative Heat Units
*   **Limitation**: The model takes a single sensor reading (e.g., $25^\circ\text{C}$, $65\%$ humidity) at the instant of the photo. However, post-harvest ripening rates depend on **respiratory heat history** (cumulative degree-days). A mango stored at $30^\circ\text{C}$ for five days and then measured at $20^\circ\text{C}$ will degrade much faster than one kept at $20^\circ\text{C}$ consistently.
*   **Academic Workaround**: Future iterations should use a sliding-window time-series input (e.g., LSTM or GRU) to ingest the preceding 48–72 hours of storage temperature history.

### B. Cultivar Generalization
*   **Limitation**: Biochemical trajectories (starting pH, Brix) and peel color changes are highly cultivar-specific. For example:
    *   *Tommy Atkins* and *Kent* show strong yellow-red color breaks.
    *   *Keitt* can remain green even when fully ripe.
    A model trained on one variety will miscalculate the shelf life of another.
*   **Academic Workaround**: Introduce a categorical one-hot or learned embedding vector for `cultivar` as a tabular input feature.

### C. Lighting and Sensor Drift
*   **Limitation**: The image backbone is highly sensitive to lighting changes, shadows, and camera white balance.
*   **Academic Workaround**: Recommend standardized image capture using a custom color calibration card (e.g., Macbeth chart) in the frame, allowing automated white-balance correction during preprocessing.

---

## Conclusion: Academic Rating

*   **Code Architecture**: **Highly Commendable**. The modular separation of `image_backbone.py`, `tabular_branch.py`, and `fusion_model.py` is clean, readable, and highly publishable.
*   **Methodological Soundness**: **Needs Improvement**. The random row-based splitting and lack of baseline comparators (ablation studies) are major academic weaknesses.
*   **Real-World/Research Viability**: Fusing image analysis with ambient factors is a viable, active field of research. Once group splits and ablation studies are implemented, this pipeline is **fully ready** to serve as the core methodology for an academic thesis or peer-reviewed publication.
