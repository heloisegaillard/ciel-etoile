import pandas as pd
import joblib
import mlflow
import mlflow.xgboost
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

# Chargement des trois fichiers de vols
df1 = pd.read_csv("data/raw/2016_10.csv", low_memory=False)
df2 = pd.read_csv("data/raw/2016_11.csv", low_memory=False)
df3 = pd.read_csv("data/raw/2016_12.csv", low_memory=False)
df = pd.concat([df1, df2, df3])

# Colonnes à supprimer
colonnes_a_supprimer = [
    'YEAR', 'QUARTER', 'CARRIER', 'ORIGIN_CITY_MARKET_ID', 'ORIGIN_CITY_NAME',
    'DEST_AIRPORT_SEQ_ID', 'DEST_CITY_NAME', 'ORIGIN_STATE_NM', 'FL_DATE',
    'DAY_OF_MONTH', 'DAY_OF_WEEK', 'DEP_DELAY', 'DEP_DELAY_NEW', 'DEP_DEL15',
    'DEP_DELAY_GROUP', 'ARR_TIME', 'ARR_DELAY', 'ORIGIN_AIRPORT_SEQ_ID',
    'DIVERTED', 'DEP_TIME', 'CANCELLED', 'DEST_STATE_ABR', 'ARR_DEL15',
    'ACTUAL_ELAPSED_TIME', 'ARR_DELAY_GROUP', 'WHEELS_ON', 'WHEELS_OFF',
    'AIR_TIME', 'DISTANCE_GROUP'
]

nan_percentage = df.isna().mean() * 100
columns_to_drop = nan_percentage[nan_percentage > 50].index
total_columns_to_drop = list(set(columns_to_drop).union(set(colonnes_a_supprimer)))
df_cleaned = df.drop(columns=total_columns_to_drop, errors='ignore')

cols_to_convert = [
    'DEST_AIRPORT_ID', 'DEST_CITY_MARKET_ID', 'DEST', 'DEST_STATE_NM',
    'DEP_TIME_BLK', 'ARR_TIME_BLK', 'ORIGIN_WAC', 'TAIL_NUM', 'FL_NUM',
    'UNIQUE_CARRIER', 'ORIGIN_AIRPORT_ID', 'ORIGIN_STATE_ABR', 'ORIGIN'
]
df_cleaned[cols_to_convert] = df_cleaned[cols_to_convert].astype(str)
df_cleaned = df_cleaned.drop_duplicates().dropna()

df_cleaned = df_cleaned[df_cleaned['UNIQUE_CARRIER'] != '10397']
le = LabelEncoder()
df_cleaned['UNIQUE_CARRIER_ENCODED'] = le.fit_transform(df_cleaned['UNIQUE_CARRIER'])
df_cleaned['ARR_DELAY_ENCODED'] = df_cleaned['ARR_DELAY_NEW'].apply(
    lambda x: 1 if x != 0 else 0
)

df_sampled = df_cleaned.sample(frac=0.1, random_state=42)
numeric_features = df_sampled.select_dtypes(include=['float64', 'int64'])
y = df_sampled['ARR_DELAY_ENCODED']
X = numeric_features.drop(columns=['ARR_DELAY_NEW', 'ARR_DELAY_ENCODED'])
X = X.fillna(X.mean())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Hyperparamètres
params = {
    "n_estimators": 300,
    "max_depth": 7,
    "learning_rate": 0.02,
    "min_child_weight": 1.5,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "gamma": 0.1,
    "reg_lambda": 1,
    "reg_alpha": 0.5,
    "scale_pos_weight": 1,
    "random_state": 42,
}

# Entraînement avec tracking MLflow
mlflow.set_experiment("aeroplan-retards")

with mlflow.start_run():
    model = XGBClassifier(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Calcul des métriques
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")

    # Enregistrement des hyperparamètres et métriques dans MLflow
    mlflow.log_params(params)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("f1_score", f1)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)

    # Enregistrement du modèle dans MLflow
    mlflow.xgboost.log_model(model, "xgboost_model")

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"F1-score  : {f1:.4f}")
    print(f"Précision : {precision:.4f}")
    print(f"Rappel    : {recall:.4f}")

# Sauvegarde locale du modèle et des features pour l'API
joblib.dump(model, "models/xgboost_model.pkl")
joblib.dump(list(X.columns), "models/feature_names.pkl")

print("Modèle sauvegardé dans models/xgboost_model.pkl")
