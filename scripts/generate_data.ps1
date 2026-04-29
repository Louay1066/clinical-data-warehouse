$SyntheaUrl = "https://github.com/synthetichealth/synthea/releases/download/v3.2.0/synthea-with-dependencies.jar"
$SyntheaJar = "synthea-with-dependencies.jar"
$OutputDir = "..\data\raw"

if (-Not (Test-Path -Path $SyntheaJar)) {
    Write-Host "Downloading Synthea v3.2.0..."
    curl.exe -L $SyntheaUrl -o $SyntheaJar
    Write-Host "Download complete."
} else {
    Write-Host "Synthea jar already exists."
}

Write-Host "Running Synthea to generate 100 patient records..."
# 100 patients to keep it fast for testing, but still plenty of data.
java -jar $SyntheaJar -p 100 -s 12345 --exporter.baseDirectory=$OutputDir --exporter.csv.export=true --exporter.fhir.export=false

Write-Host "Data generation complete. Check the $OutputDir\csv folder."
