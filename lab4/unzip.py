import zipfile

with zipfile.ZipFile("./Divvy_Trips_2019_Q4.csv.zip") as zip:
    zip.extractall("./jobs")
