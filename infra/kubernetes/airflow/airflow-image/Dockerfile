FROM apache/airflow:2.10.5-python3.12
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt .

# install pip packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set environment variables for Airflow (https://airflow.apache.org/docs/apache-airflow/2.10.5/configurations-ref.html#webserver)
ENV AIRFLOW__CORE__TEST_CONNECTION=Enabled
ENV AIRFLOW__WEBSERVER__DAG_ORIENTATION=TB
ENV AIRFLOW__WEBSERVER__EXPOSE_STACKTRACE=True
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__WEBSERVER__DEFAULT_WRAP=True