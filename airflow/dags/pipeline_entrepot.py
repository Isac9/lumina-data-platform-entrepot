"""
DAG Airflow : pipeline quotidien de l'entrepôt Lumina Énergie.

    extraire_crm ─────────┐
    extraire_portefeuille ├──> dbt_seed ──> dbt_run ──> dbt_test
    extraire_erp ─────────┘
"""

from datetime import datetime, timedelta

from airflow.datasets import Dataset
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

import outils_extraction as ox

DBT = "cd /opt/dbt/lumina_dwh && /home/airflow/dbt_venv/bin/dbt"

# "Signal" envoyé quand les tables finales sont prêtes et testées.
# D'autres pipelines (ex. : le reporting du projet 2) peuvent l'attendre.
MARTS_PRETS = Dataset("lumina://dwh/marts")


@dag(
    dag_id="pipeline_entrepot_lumina",
    description="ELT quotidien : CRM + Portefeuille + ERP -> entrepôt PostgreSQL",
    schedule="0 5 * * *",  # tous les jours à 5h00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["lumina", "elt", "dwh"],
)
def pipeline_entrepot_lumina():

    @task
    def extraire_crm():
        return ox.charger_crm()

    @task
    def extraire_portefeuille():
        return ox.charger_portefeuille()

    @task
    def extraire_erp():
        return ox.charger_erp()

    dbt_seed = BashOperator(task_id="dbt_seed", bash_command=f"{DBT} seed")
    dbt_run = BashOperator(task_id="dbt_run", bash_command=f"{DBT} run")
    dbt_test = BashOperator(task_id="dbt_test", bash_command=f"{DBT} test", outlets=[MARTS_PRETS])

    [extraire_crm(), extraire_portefeuille(), extraire_erp()] >> dbt_seed >> dbt_run >> dbt_test


pipeline_entrepot_lumina()
