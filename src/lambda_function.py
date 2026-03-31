import json
import boto3
import io
import os
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Función para obtener parámetros 
def get_parameters (param_name):
    ssm = boto3.client("ssm")
    param = ssm.get_parameter(Name=param_name)
    values = json.loads(param["Parameter"]["Value"])
    return values

# Cargar parámetros
parameters = get_parameters ("/datalake/dev/source/github/dr5hn/cities")

# Parámetros para almacenamiento en S3
bucket_name = os.environ['BUCKET_BRONZE']
environment = os.environ['ENV']
company= parameters["company"]
source= parameters["source"]
dataset="cities"

def lambda_handler(event, context):
    try:
        logger.info("Iniciando Lambda dataset=%s environment=%s", dataset, environment)
        #Obtener fecha de carga
        now = datetime.utcnow()
        ingest_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        # URL del CSV
        url = parameters["url"]

        # Leer CSV usando la primera fila como cabecera
        df = pd.read_csv(url)
        logger.info("CSV leído exitosamente desde %s", url)

        if df.empty:
            logger.warning("El archivo CSV está vacío")
        else:
            logger.info("Cantidad de registros recibidos: %s", len(df))

        # Agregar metadatos al CSV
        df["ingest_timestamp"] = ingest_timestamp
        df["load_type"] = "snapshot"
        df["dataset"]= dataset
        logger.info("Metadatos agregados correctamente")


        # Construir ruta y nombre de archivo
        bucket_fullname  = f"{bucket_name}-{environment}"
        path = (
            f"dmn=general/"
            f"dataset={dataset}/"
            f"src={source}/"
            f"ext={company}/"
            f"ingest_date={year}-{month}-{day}/"
        )

        logger.info("Nombre el bucket: %s", bucket_fullname)

        # Generando nombre de archivo
        filename = f"{dataset}.parquet"
        key = path + filename

        # Convertir columnas a string
        df = df.astype(str)
        logger.info("Columnas convertidas a string exitosamente")

        # Escribir CSV en buffer de memoria
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine='pyarrow', index = False)
        buffer.seek(0)

        # Subir a S3
        logger.info("Subiendo archivo a S3 bucket=%s key=%s", bucket_fullname, key)
        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucket_fullname, Key=key, Body=buffer.getvalue())
        logger.info("Archivo subido exitosamente a S3")
        logger.info("Versionado 1 realizado con terraform")

        # Retornar confirmación
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Archivo guardado exitosamente en: {bucket_fullname}/{key}'
            })
        }
    except Exception as e:
        logger.exception("Error durante la ejecución de la Lambda")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }