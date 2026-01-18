from modelling.train import train_model
from modelling.evaluate import evaluate_model
from modelling.features import data_augmentation,feature_analysis,feature_extraction, dataframe_feature_extraction
import os
import pandas as pd
from sklearn.model_selection import train_test_split,cross_val_score
import argparse


def pipeline(path: str = 'extracted_features.csv', use_augmentation: bool = False):
    """Main pipeline function to execute feature extraction, model training, and evaluation."""
    print("Starting the machine learning pipeline...")

    # Step 1: Feature Extraction
    if not os.path.exists(f"data/{path}"):
        print("Performing feature extraction ...")
        feature_extraction()
        print("Feature extraction completed.")

        print("Performing feature analysis ...")
        feature_analysis()
        print("Feature analysis completed.")
    
    # Step 2: Data Preparation
    data = pd.read_csv(f'data/{path}')

    train_data = data[['case', 'summary_issue', 'full_abstract']]
    test_data = data['labels']

    print("Y distribution:", test_data.value_counts())

    X_train, X_test, y_train, y_test = train_test_split(train_data, test_data, test_size=0.2, random_state=42, shuffle=True,stratify=test_data)
    
    if use_augmentation:
        print("Performing data augmentation on training set ...")
        X_train, y_train = data_augmentation(X_train, y_train)
        print("Data augmentation completed.")
   
    X_train = X_train['case'] + " " + X_train['summary_issue'] + " " + X_train['full_abstract']
    X_test = X_test['case'] + " " + X_test['summary_issue'] + " " + X_test['full_abstract']

    print("=Label distribution in training set=\n", pd.Series(y_train).apply(eval).value_counts())
    print("=Label distribution in test set=\n", pd.Series(y_test).apply(eval).value_counts())
    print("Sample of text data:\n", X_train.iloc[10])

    # Step 3: Model Training
    print("Performing model training ...")

    model = train_model(X_train, y_train, path='logistic_regression_model.pth')
    scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

    print(f"True Accuracy: {scores.mean():.2f} (+/- {scores.std():.2f})")
    print("Model training completed.")

    # Step 4: Model Evaluation
    print("Performing model evaluation ...")
    evaluate_model(model, X_test, y_test)

    print("Pipeline completed successfully.")


def model_pipeline(data: pd.DataFrame, **kwargs):
    """Main pipeline function to execute feature extraction, model training, and evaluation."""
    print("Starting the machine learning pipeline...")

    # Step 1: Feature Extraction
    print("Performing feature extraction ...")
    dataframe_feature_extraction(data=data, out_path=kwargs.get('out_path'))
    print("Feature extraction completed.")

    print("Performing feature analysis ...")
    feature_analysis(path=kwargs.get('out_path'))
    print("Feature analysis completed.")
    
    # Step 2: Data Preparation
    data = pd.read_csv(f"data/{kwargs.get('out_path')}")
    train_data = data[['case', 'summary_issue', 'full_abstract']]
    test_data = data['labels']

    print("Y distribution:", test_data.value_counts())

    X_train, X_test, y_train, y_test = train_test_split(train_data, test_data, test_size=0.2, random_state=42, shuffle=True,stratify=test_data)
    
    if kwargs.get('use_augmentation', False):
        print("Performing data augmentation on training set ...")
        X_train, y_train = data_augmentation(X_train, y_train)
        print("Data augmentation completed.")
   
    X_train = X_train['case'] + " " + X_train['summary_issue'] + " " + X_train['full_abstract']
    X_test = X_test['case'] + " " + X_test['summary_issue'] + " " + X_test['full_abstract']

    print("=Label distribution in training set=\n", pd.Series(y_train).apply(eval).value_counts())
    print("=Label distribution in test set=\n", pd.Series(y_test).apply(eval).value_counts())
    print("Sample of text data:\n", X_train.iloc[10])

    # Step 3: Model Training
    print("Performing model training ...")

    model = train_model(X_train, y_train, path=kwargs.get('model_path', 'logistic_regression_model.pth'), **kwargs)
    scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

    print(f"True Accuracy: {scores.mean():.2f} (+/- {scores.std():.2f})")
    print("Model training completed.")

    # Step 4: Model Evaluation
    print("Performing model evaluation ...")
    accuracy, report = evaluate_model(model, X_test, y_test)

    print("Pipeline completed successfully.")
    return accuracy, report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Machine Learning Pipeline for Content Moderation")
    parser.add_argument('--path', type=str, default='extracted_features.csv', help='Path to the feature CSV file')
    parser.add_argument('--use-augmentation', action='store_true', help='Use data augmentation during training')
    args = parser.parse_args()  
    pipeline(path=args.path, use_augmentation=args.use_augmentation)