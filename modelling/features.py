import os
import ast
from typing import List
import pandas as pd
from pandas import DataFrame
import random
import ast


def feature_analysis(path: str = 'extracted_features.csv'):
        """Basic feature analysis for a CSV at `path`.

        Prints head, dtypes, null counts and a few summaries.
        """
        complete_path = os.path.join("data", path)
        if not os.path.exists(complete_path):
            raise FileNotFoundError(f"Feature file not found: {complete_path}")
        
        data = pd.read_csv(complete_path)
        print(data.head(3))
        print("Features dtypes:", data.dtypes)
        print("Missing values per feature:\n", data.isnull().sum())
        print("Number of unique values per feature:\n", data.nunique())
        print("Statistical summary of numerical features:\n", data.describe())
        print("Duplicated rows count:", data.duplicated().sum())
        print("Total rows and columns:", data.shape)

        exploded = data['category'].apply(ast.literal_eval).explode()
        print("Category distribution:\n", exploded.value_counts())




def feature_extraction(source_path: str = 'Facebook _Supreme Court_Cases.csv',
                           out_path: str = 'extracted_features.csv'):
        """Extracts features and writes `out_path`.

        - Normalizes categories and produces one-hot label columns.
        - Saves cleaned category lists to `data/categories.txt` and `data/llm_categories.txt`.
        """

        combined_path =os.path.join("data", source_path)
        if not os.path.exists(combined_path):
            raise FileNotFoundError(f"Source CSV not found: {combined_path}")

        data = pd.read_csv(combined_path)

        dataframe_feature_extraction(data, out_path=out_path)

def dataframe_feature_extraction(data: pd.DataFrame,
                           out_path: str = 'extracted_features.csv'):
        """Extracts features and writes `out_path`.

        - Normalizes categories and produces one-hot label columns.
        - Saves cleaned category lists to `data/categories.txt` and `data/llm_categories.txt`.
        """
        combined_out_path = os.path.join("data", out_path)

        case = data['Case name'].fillna('') + "|" + data['summary'].fillna('')
        summary_issue = data.get('summary / issue')
        llm_category = data.get('FB category')
        category = data.get('category')
        full_abstract = data.get('full abstract ')

        # Build and save cleaned category lists
        _ = normalize_category_labels(llm_category, path=os.path.join('data', 'llm_categories.txt'))
        cleaned_category = normalize_category_labels(category, path=os.path.join('data', 'categories.txt'))

        labels_df, categories_series = generate_labels(category, cleaned_category)

        # Combine features and expanded label columns
        extracted_data = pd.DataFrame({
            "case":case,
            "summary_issue":summary_issue,
            "llm_category":llm_category,
            "category":categories_series,
            "full_abstract":full_abstract,
            "labels":labels_df
        })

        extracted_data.to_csv(combined_out_path, index=False)


def normalize_category_labels(data: pd.Series, path: str = 'data/cleaned_categories.txt') -> List[str]:
        """Normalize categories from a Series and save unique tokens to `path`.

        Returns list of cleaned category tokens in preserved order.
        """
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
            elif cat_str in ("Undefined", "misc","Bullying & Harassment", "Regulated Goods", "Nudity & sexual activity"):
                categories.append("other")
            else:
                categories.append(cat_str.lower())

        # preserve order and remove duplicates
        unique: List[str] = []
        for c in categories:
            if c not in unique:
                unique.append(c)

        # save cleaned categories to a text file (one per line)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            for cat in unique:
                f.write(cat + '\n')
        return unique

def generate_labels(data: pd.Series, cleaned_category: list) -> tuple[pd.Series, pd.Series]:
    """
    Generate one-hot labels and cleaned categories for each row.

    Returns:
        labels_series: pd.Series of lists (one-hot encoded)
        categories_series: pd.Series of lists (cleaned category parts)
    """
    labels = []
    categories = []
    print("data distribution:", data.value_counts())
    for item in data:
        if pd.isna(item):
            parts = []
        elif str(item).strip() in ("Undefined", "misc","Bullying & Harassment", "Regulated Goods", "Nudity & sexual activity"):
            parts = ["other"]
        else:
            parts = [p.strip().lower() for p in str(item).split('/')]
        
        categories.append(parts)  # store cleaned categories
        row = [1 if cat in parts else 0 for cat in cleaned_category]
        labels.append(row)  # store one-hot labels
    
    # Convert to Series with dtype=object to store lists
    labels_series = pd.Series(labels, index=data.index, dtype=object)
    categories_series = pd.Series(categories, index=data.index, dtype=object)
    print("Generated one-hot labels and cleaned categories.")
    print("Sample labels:", labels_series.head(3))
    print("Sample categories:", categories_series.head(3))
    return labels_series, categories_series

def robust_augment(text, perturbation=0.2):

    """
    Aggressively modifies text by deleting AND swapping words.
    perturbation=0.2 means roughly 20% of the text will be altered.
    """
    words = text.split()
    n_words = len(words)
    
    # Don't mess with very short texts (loss of meaning)
    if n_words < 5:
        return text
    
    # 1. DELETE: Remove random words (simulates missing info)
    # We keep (1 - perturbation) percent of words
    n_keep = max(1, int(n_words * (1 - perturbation)))
    keep_indices = set(random.sample(range(n_words), n_keep))
    new_words = [word for i, word in enumerate(words) if i in keep_indices]
    
    # 2. SWAP: Randomly swap two words (simulates structural noise)
    # We do this a few times based on text length
    n_swaps = max(1, int(len(new_words) * 0.1)) # Swap 10% of remaining words
    for _ in range(n_swaps):
        idx1, idx2 = random.sample(range(len(new_words)), 2)
        new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]
        
    return " ".join(new_words)

def data_augmentation(data: DataFrame, labels: pd.Series) -> tuple[DataFrame, pd.Series]:
    new_rows = []
    for index, row in data.iterrows():
        # 1. Keep the Original (Ground Truth)
        new_rows.append(row)
    
        # 2. Create the "Noisy" Twin
        row_aug = row.copy()
    
        row_aug['full_abstract'] = robust_augment(row['full_abstract'], perturbation=0.15)
        row_aug['summary_issue'] = robust_augment(row['summary_issue'], perturbation=0.10)
    
        new_rows.append(row_aug)

    # Create final Expanded Dataset
    df_expanded = pd.DataFrame(new_rows).reset_index(drop=True)

    print(f"Original Size: {len(data)}")
    print(f"New Size:      {len(df_expanded)}")

    # Check an example
    print("\n--- Example Change ---")
    print(f"Original: {data.iloc[0]['summary_issue']}")
    print(f"Augmented: {df_expanded.iloc[1]['summary_issue']}")
    return df_expanded, pd.concat([labels, labels])

if __name__ == "__main__":
        print("Performing feature extraction ...")
        feature_extraction()
        print("Performing feature analysis on extracted_features ...")
        feature_analysis('extracted_features.csv')
        print("Performing data augmentation ...")
        data_augmentation('data/extracted_features.csv')
        print("Performing feature analysis on augmented data ...")
        feature_analysis('extracted_features_augmented.csv')
        print("All tasks completed.")
        