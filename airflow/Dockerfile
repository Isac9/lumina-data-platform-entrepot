FROM apache/airflow:2.10.5-python3.11

# dbt est installé dans son propre environnement Python (venv)
# pour ne pas entrer en conflit avec les bibliothèques d'Airflow.
RUN python -m venv /home/airflow/dbt_venv && PIP_USER=false /home/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-core==1.9.4 dbt-postgres==1.9.0
