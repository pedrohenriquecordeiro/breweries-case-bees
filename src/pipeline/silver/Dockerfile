# Apache Spark 3.5.5, compilado com Scala 2.12.18 e rodando no OpenJDK 17.0.14.
FROM apache/spark:3.5.5

USER root

RUN apt-get update && \
    apt-get install -y wget && \
    apt-get install -y tree && \
    pip install --no-cache-dir py4j==0.10.9.7 google-cloud-storage==3.1.0 delta-spark==3.3.0

# JARs obrigatórios
RUN wget -P /opt/spark/jars/ https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar
RUN wget -P /opt/spark/jars/ https://search.maven.org/remotecontent?filepath=org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.8.1/iceberg-spark-runtime-3.5_2.12-1.8.1.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.1.0/delta-spark_2.12-3.1.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/io/delta/delta-storage/3.1.0/delta-storage-3.1.0.jar


ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

WORKDIR /app

COPY main.py .

RUN tree .

CMD ["python3", "main.py"]
