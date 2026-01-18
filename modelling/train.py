import ast
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model(X_train, y_train,path='logistic_regression_model.pth', **kwargs):
    """Trains a RandomForestClassifier model and saves it to the specified path."""
    print("Training model...")

    print("Length of training data:", len(X_train))

    y_train = y_train.apply(ast.literal_eval).tolist()

    y_train = np.array(y_train, dtype=int)

    print("Shape of y_train after conversion to list:", y_train.shape)
    # Run this right before model.fit(X_train, y_train)
    print("First row of y_train:", y_train[0])
    print("Type of y_train:", type(y_train))
    print("Shape of y_train:", y_train.shape)
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=30)),
        ('clf', RandomForestClassifier(
        n_estimators=kwargs.get('n_estimators', 200),
        random_state=kwargs.get('random_state', 42),
        max_depth=kwargs.get('max_depth', 10),
        class_weight=kwargs.get('class_weight', 'balanced')
    ))
    ])

    model.fit(X_train, y_train)

    print("Model training completed.")

    joblib.dump(model, path)
    print(f"Model saved to '{path}'")

    return model
