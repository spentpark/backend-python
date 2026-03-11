pipeline {
    agent any

    environment {
        // Nexus Config
        NEXUS_VERSION       = "nexus3"
        NEXUS_PROTOCOL      = "http"
        NEXUS_URL           = "172.17.0.1:8081"
        NEXUS_REPOSITORY    = "python-nexus-repo" // Asegúrate de crear un repo tipo 'pypi' en Nexus
        NEXUS_CREDENTIAL_ID = "nexus"

        // Sonar Config
        SONAR_HOST_URL = "http://172.17.0.1:9000"
        SONAR_TOKEN    = "squ_d27dacd45a6c18772d7e941fd44e1617cf5c4c38"

        APP_VERSION   = ""
        ARTIFACT_FILE = ""
        PATH = "/usr/bin:$PATH"
    }

    stages {
        stage('Clean Install') {
            steps {
                sh '''
                    echo "Python version:"
                    python3 --version

                    echo "Cleaning workspace..."
                    rm -rf venv build dist *.egg-info .pytest_cache coverage.xml htmlcov

                    echo "Creating virtual environment and installing dependencies..."
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov build twine
                '''
            }
        }

        stage('Test & Sonar Analysis') {
            steps {
                script {
                    sh '''
                        # Ejecutar tests y generar reporte de cobertura
                        pytest --cov=app --cov-report=xml:coverage.xml || echo "Tests failed but continuing for analysis"
                    '''
                    
                    // Si no tienes el sonar-scanner instalado en la imagen, 
                    // lo ideal es usar el cliente de python o descargar el binario.
                    // Aquí asumimos que usas la imagen oficial de sonar-scanner o lo descargas:
                    sh '''
                        # Descarga rápida del sonar-scanner si no existe
                        if ! command -v sonar-scanner &> /dev/null; then
                            apt-get update && apt-get install -y wget unzip
                            wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                            unzip sonar-scanner-cli-5.0.1.3006-linux.zip
                            export PATH=$PATH:$(pwd)/sonar-scanner-5.0.1.3006-linux/bin
                        fi

                        sonar-scanner \
                          -Dsonar.projectKey=backend-python \
                          -Dsonar.sources=app \
                          -Dsonar.tests=tests \
                          -Dsonar.python.coverage.reportPaths=coverage.xml \
                          -Dsonar.host.url=${SONAR_HOST_URL} \
                          -Dsonar.token=${SONAR_TOKEN}
                    '''
                }
            }
        }

        stage('Package (Wheel)') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install build
                    echo "1.0.${BUILD_NUMBER}"
                    python3 -m build
                '''
            }
        }

        stage('Publish to Nexus') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${NEXUS_CREDENTIAL_ID}", usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        . venv/bin/activate
                        pip install twine
                        export TWINE_USERNAME=$USER
                        export TWINE_PASSWORD=$PASS
                        # --repository-url debe apuntar al repo PyPI de Nexus
                        python3 -m twine upload \
                          --repository-url http://${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/ \
                          dist/* --non-interactive
                    '''
                }
            }
        }
    }

    post {
        always {
            // En Docker no hace falta borrar el venv porque el contenedor se destruye
            cleanWs()
            echo "Pipeline finished"
        }
    }
}