import mlflow
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from utils import load_data

# データの読み込み
X, y = load_data("data")  # 適切なデータ読み込み関数を使用
X = X[["feature0", "feature1", "feature2", "feature3", "feature4", "feature5"]]

# GridSearchCVの設定
param_grid = {"alpha": np.logspace(-3, 1, 100)}
model = RidgeClassifier()
scorer = make_scorer(f1_score, average="macro")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
grid_search = GridSearchCV(model, param_grid, scoring=scorer, cv=cv, verbose=1)

# MLflowの設定
mlflow.set_experiment("breath_checker_development")

# 親Runの開始
with mlflow.start_run(run_name="ridge_classifier_tuning") as parent_run:

    # GridSearchCVの実行
    grid_search.fit(X, y)

    # 結果の記録
    for i, params in enumerate(grid_search.cv_results_["params"]):
        with mlflow.start_run(nested=True, run_name=f"params_{i}") as child_run:
            mlflow.log_params(params)
            mlflow.log_metric("f1_score", grid_search.cv_results_["mean_test_score"][i])

    # 最良モデルの保存
    best_model = grid_search.best_estimator_
    mlflow.sklearn.log_model(best_model, "best_model")
    mlflow.log_params(grid_search.best_params_)
    mlflow.log_metric("best_f1_score", grid_search.best_score_)
    mlflow.log_artifact(__file__)
