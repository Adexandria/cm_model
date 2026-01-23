import os
import sys
import ast
import random
from typing import List
import pandas as pd
from pandas import DataFrame
import spacy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import FIELDS

# Load spaCy model
nlp = spacy.load("en_core_web_sm")
NEGATIONS = {"no", "not", "never", "n't"}

# Define text columns to preprocess
TEXT_COLUMNS = ["case", "summary_issue", "full_abstract"]

# -------------------------
# Preprocessing function
# -------------------------
def preprocessing(text: str) -> str:
    """
    Lemmatize text, remove stopwords but keep negations, attach NOT_ to negated words.
    """
    doc = nlp(text.lower())
    tokens = []
    negate = False

    for token in doc:
        if token.text in NEGATIONS:
            negate = True
            continue

        if token.is_punct or token.is_space or not token.is_alpha:
            continue

        lemma = token.lemma_

        if negate:
            lemma = f"NOT_{lemma}"
            negate = False

        if token.is_stop:
            continue

        tokens.append(lemma)

    return " ".join(tokens)

# -------------------------
# Feature extraction
# -------------------------
def feature_extraction(source_path: str = 'Facebook _Supreme Court_Cases.csv',
                       out_path: str = 'extracted_features.csv'):
    """Extract features from source CSV and save to out_path."""
    combined_path = os.path.join("data", source_path)
    if not os.path.exists(combined_path):
        raise FileNotFoundError(f"Source CSV not found: {combined_path}")

    data = pd.read_csv(combined_path)
    dataframe_feature_extraction(data, out_path=out_path)

# -------------------------
# Dataframe feature extraction
# -------------------------
def dataframe_feature_extraction(data: pd.DataFrame,
                                 out_path: str = 'extracted_features.csv'):
    """
    Extract features, normalize categories, one-hot encode labels, 
    preprocess text columns, and save the final CSV.
    """
    combined_out_path = os.path.join("data", out_path)

    # Combine case_name + summary as one 'case' column
    case = data[FIELDS["case_name"]].fillna('') + "|" + data[FIELDS["summary"]].fillna('')
    summary_issue = data.get(FIELDS["summary_issue"])
    llm_category = data.get(FIELDS["FB_category"])
    category = data.get(FIELDS["category"])
    full_abstract = data.get(FIELDS["full_abstract"])

    # Normalize categories and save cleaned lists
    _ = normalize_category_labels(llm_category, path=os.path.join('data', 'llm_categories.txt'))
    cleaned_category = normalize_category_labels(category, path=os.path.join('data', 'categories.txt'))

    # Generate one-hot labels and cleaned categories
    labels_df, categories_series = generate_labels(category, cleaned_category)

    # Combine features
    extracted_data = pd.DataFrame({
        "case": case,
        "summary_issue": summary_issue,
        "llm_category": llm_category,
        "category": categories_series,
        "full_abstract": full_abstract,
        "labels": labels_df
    })

    # -------------------------
    # Apply preprocessing to text columns
    # -------------------------
    for col in TEXT_COLUMNS:
        if col in extracted_data.columns:
            extracted_data[col] = extracted_data[col].fillna("").astype(str).apply(preprocessing)

    # Save final CSV
    os.makedirs(os.path.dirname(combined_out_path), exist_ok=True)
    extracted_data.to_csv(combined_out_path, index=False)
    print(f"Extracted features saved to {combined_out_path}")

# -------------------------
# Normalize category labels
# -------------------------
def normalize_category_labels(data: pd.Series, path: str = 'data/cleaned_categories.txt') -> List[str]:
    """Normalize categories and save unique tokens to a text file."""
    categories: List[str] = []
    distribution = data.value_counts(dropna=False)
    for category in distribution.index:
        if pd.isna(category):
            continue
        cat_str = str(category).strip()
        if cat_str == "Violence / Incitement":
            categories.append("violence and incitement")
        elif '/' in cat_str:
            parts = [p.strip().lower() for p in cat_str.split('/') if p.strip()]
            categories.extend(parts)
        elif cat_str in ("Undefined", "misc", "Bullying & Harassment", "Regulated Goods", "Nudity & sexual activity"):
            categories.append("other")
        else:
            categories.append(cat_str.lower())

    # Preserve order and remove duplicates
    unique: List[str] = []
    for c in categories:
        if c not in unique:
            unique.append(c)

    # Save cleaned categories
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for cat in unique:
            f.write(cat + '\n')
    return unique

# -------------------------
# Generate one-hot labels
# -------------------------
def generate_labels(data: pd.Series, cleaned_category: list) -> tuple[pd.Series, pd.Series]:
    """
    Returns:
        labels_series: pd.Series of one-hot encoded lists
        categories_series: pd.Series of cleaned category lists
    """
    labels = []
    categories = []
    for item in data:
        if pd.isna(item):
            parts = []
        elif str(item).strip() in ("Undefined", "misc","Bullying & Harassment", "Regulated Goods", "Nudity & sexual activity"):
            parts = ["other"]
        else:
            parts = [p.strip().lower() for p in str(item).split('/')]

        categories.append(parts)
        row = [1 if cat in parts else 0 for cat in cleaned_category]
        labels.append(row)

    labels_series = pd.Series(labels, index=data.index, dtype=object)
    categories_series = pd.Series(categories, index=data.index, dtype=object)
    return labels_series, categories_series

# -------------------------
# Robust text augmentation
# -------------------------
def robust_augment(text, perturbation=0.2):
    """Randomly deletes and swaps words to simulate noisy text."""
    text = str(text)
    words = text.split()
    n_words = len(words)

    if n_words < 5:
        return text

    # DELETE
    n_keep = max(1, int(n_words * (1 - perturbation)))
    keep_indices = set(random.sample(range(n_words), n_keep))
    new_words = [word for i, word in enumerate(words) if i in keep_indices]

    # SWAP
    n_swaps = max(1, int(len(new_words) * 0.1))
    for _ in range(n_swaps):
        idx1, idx2 = random.sample(range(len(new_words)), 2)
        new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]

    return " ".join(new_words)

def data_augmentation(data: pd.DataFrame, labels: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """
    Create augmented dataset by adding noisy text copies.
    Ensures labels stay aligned with the interleaved augmented rows.
    """
    new_rows = []
    new_labels = []

    # Use zip to iterate X and y together to prevent index mismatch
    # iterrows() gives (index, row), we ignore the index with _
    for (_, row), label in zip(data.iterrows(), labels):
        
        # 1. Original Sample
        new_rows.append(row)
        new_labels.append(label)

        # 2. Augmented Sample
        row_aug = row.copy()
        
        # Apply specific perturbations to specific columns
        try:
            row_aug['full_abstract'] = robust_augment(row['full_abstract'], perturbation=0.15)
            row_aug['summary_issue'] = robust_augment(row['summary_issue'], perturbation=0.10)
            
            new_rows.append(row_aug)
            new_labels.append(label) # DUPLICATE the label for the augmented row
        except Exception as e:
            # If augmentation fails (e.g. empty string), we don't add the row,
            # and we DON'T add the label. This keeps alignment safe.
            print(f"Augmentation failed for a row: {e}")
            continue

    # Reconstruct DataFrame and Series
    df_expanded = pd.DataFrame(new_rows).reset_index(drop=True)
    labels_expanded = pd.Series(new_labels).reset_index(drop=True)

    print(f"Original Size: {len(data)} | Augmented Size: {len(df_expanded)}")
    return df_expanded, labels_expanded

# -------------------------
# Feature analysis
# -------------------------
def feature_analysis(path: str = 'extracted_features.csv'):
    """Print basic info and distribution of categories."""
    complete_path = os.path.join("data", path)
    if not os.path.exists(complete_path):
        raise FileNotFoundError(f"Feature file not found: {complete_path}")

    data = pd.read_csv(complete_path)
    print(data.head(3))
    print("dtypes:", data.dtypes)
    print("Missing values:\n", data.isnull().sum())
    print("Unique values per column:\n", data.nunique())
    print("Numerical summary:\n", data.describe())
    print("Duplicated rows:", data.duplicated().sum())
    print("Total shape:", data.shape)

    if 'category' in data.columns:
        exploded = data['category'].apply(ast.literal_eval).explode()
        print("Category distribution:\n", exploded.value_counts())

# -------------------------
# Main workflow
# -------------------------
if __name__ == "__main__":
    print("Performing feature extraction ...")
    feature_extraction()

    print("Analyzing extracted features ...")
    feature_analysis('extracted_features.csv')

    df = pd.read_csv("data/extracted_features.csv")
    labels = pd.Series(df["labels"])

    print("Performing data augmentation ...")
    df_aug, labels_aug = data_augmentation(df, labels)

    # Save augmented dataset
    df_aug.to_csv("data/extracted_features_augmented.csv", index=False)
    print("Analyzing augmented data ...")
    feature_analysis('extracted_features_augmented.csv')

    print("All tasks completed.")
