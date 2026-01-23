import ast
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

def evaluate_model(model, X_test, y_test):
    """Evaluates the model on test data and prints accuracy and classification report."""
    
    print("Evaluating model...")
    y_test = y_test.apply(ast.literal_eval).tolist()
    y_test_encoded = np.array(y_test, dtype=int)
    
    print("Shape of y_test after conversion to list:", y_test_encoded.shape)
    y_preda = model.predict(X_test)
    #y_prob_matrix = np.array([prob[:, 1] for prob in y_preda]).T
    y_pred = (y_preda >= 0.25).astype(int)
    print("Predictions:", type(y_pred[0]))
    print("True Labels:", type(y_test[0]))
    accuracy = accuracy_score(y_test_encoded, y_pred,)
    report = classification_report(y_test_encoded, y_pred)

    print(f"Accuracy: {accuracy:.4f}")
    print("Classification Report:\n", report)

    return accuracy,report
