import matplotlib.pyplot as plt
import mlflow
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold

from utils import load_data

# Stratified K-Foldの設定
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
X, y = load_data("data")  # データが格納されているフォルダのパスを指定
X = X[["feature0", "feature1", "feature2", "feature3", "feature4", "feature5"]]

# MLflowの実験を開始
mlflow.set_experiment(experiment_name="breath_checker_development")
with mlflow.start_run(run_name="ridge_classifier"):
    # タグの設定
    mlflow.set_tags(
        {
            "framework": "scikit-learn",
            "model_type": "RidgeClassifier",
            "experiment_type": "classification",
        }
    )
    confusion_matrix_for_artifact = np.zeros((np.unique(y).size, np.unique(y).size))
    f1_scores = []
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y[train_index], y[test_index]

        # RidgeClassifierの学習
        model = RidgeClassifier()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # f1_scoreと混同行列の計算
        f1_scores.append(f1_score(y_test, y_pred, average="macro"))
        confusion_matrix_for_artifact += confusion_matrix(y_test, y_pred)

    # MLflowにメトリクスを記録
    mlflow.log_metric("f1_score", np.mean(f1_scores))

    # paramsの保存
    mlflow.log_params({"alpha": model.alpha})

    disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix_for_artifact)
    fig, ax = plt.subplots()
    disp.plot(ax=ax)
    plt.title("Confusion Matrix")
    plt.savefig("confusion_matrix.png")

    # modelの保存
    final_model = RidgeClassifier()
    final_model.fit(X, y)
    mlflow.sklearn.log_model(final_model, "model")

    # artifactの保存
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.log_artifact(__file__)
