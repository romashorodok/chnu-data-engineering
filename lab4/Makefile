run:
	docker exec -it spark-master spark-submit /opt/bitnami/spark/jobs/process.py

upload:
	docker exec -it minio-mc bash -c "mc alias set minio http://minio:9000 minioadmin minioadmin && mc mb minio/dataset || true && mc mb minio/out || true && mc anonymous set public minio/dataset && mc anonymous set public minio/out && mc put Divvy_Trips_2019_Q4.csv minio/dataset && /bin/bash"
