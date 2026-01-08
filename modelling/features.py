import pandas as pd


def feature_analysis(path: str):
    data = pd.read_csv(path)
    print(data.head(3))
    print("Features dtypes:" , data.dtypes)
    print("Features info:", data.info())
    print("Missing values per feature:\n", data.isnull().sum())
    print("Number of unique values per feature:\n", data.nunique())
    print("Statistical summary of numerical features:\n", data.describe())
    print("Duplicated rows count:", data.duplicated().sum())
    print(data.columns.tolist())



def feature_extraction():
    data = pd.read_csv('data/Facebook _Supreme Court_Cases.csv')
  
    case = data['Case name'] + "|" + data["summary"]
    summary_issue = data["summary / issue"]
    llm_category = data["FB category"]
    category = data["category"]
    full_abstract = data["full abstract "]
    _ = normalize_category_labels(llm_category,path= "data/llm_categories.txt")
    cleaned_category = normalize_category_labels(category,path= "data/categories.txt")

    labels = generate_labels(category, cleaned_category)

    extracted_data = pd.DataFrame({
        'case': case,
        'summary_issue': summary_issue,
        'llm_category': llm_category,
        'category': category,
        'full_abstract': full_abstract,
        'labels': labels
    })

    extracted_data.to_csv('data/extracted_features.csv', index=False)

def normalize_category_labels(data,path='data/cleaned_categories.txt'):
    categories = []
    distribution = data.value_counts()
    print("Category distribution:\n", distribution)
    for category in distribution.index:
        if pd.isna(category):
            continue
        cat_str = str(category).strip()
        if cat_str == "Violence / Incitement":
            categories.append("violence and incitement")
        elif '/' in cat_str:
            parts = [p.strip().lower() for p in cat_str.split('/') if p.strip()]
            categories.extend(parts)
        elif cat_str == "Undefined" or cat_str == "misc":
            categories.append("other")
        else:
            categories.append(cat_str.lower())
    
    # preserve order and remove duplicates
    seen = set()
    unique = []
    for c in categories:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    print("Cleaned categories:\n", unique)

    # save cleaned categories to a text file (one per line)
    with open(path, 'w', encoding='utf-8') as f:
            for cat in unique:
                f.write(cat + '\n')
    return unique

def generate_labels(data, cleaned_category):
    labels = []
    for item in data:
        if pd.isna(item):
            parts = []
        else:
            parts = [p.strip().lower() for p in str(item).split('/')]
        row = [1 if cat in parts else 0 for cat in cleaned_category]
        labels.append(row)
    return pd.Series(labels, index=data.index)

if __name__ == "__main__":
    print("Performing feature extraction ...")
    feature_extraction()
    print("Performing feature analysis ...")
    feature_analysis('data/extracted_features.csv')