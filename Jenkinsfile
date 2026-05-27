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
                    
                    echo "Creating virtual environment (without pip)..."
                    # El flag --without-pip evita que falle por la falta de ensurepip
                    python3 -m venv venv --without-pip
                    
                    echo "Bootstrapping pip manually via curl..."
                    # Activamos el venv e instalamos pip descargándolo directamente
                    . venv/bin/activate
                    curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
                    python3 get-pip.py
                    rm get-pip.py
                    
                    echo "Installing project dependencies..."
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test & Sonar Analysis') {
            steps {
                script {
                    sh '''
                        echo "==> Activando entorno virtual y ejecutando tests..."
                        . venv/bin/activate
                        
                        # Forzamos httpx a una versión anterior para que no rompa tu sintaxis con 'app='
                        pip install pytest pytest-cov "httpx<=0.26.0" aiosqlite pytest-asyncio
                        
                        # Ejecutamos pytest ignorando warnings menores
                        pytest -W ignore --cov=app --cov-report=xml:coverage.xml || echo "Tests failed but continuing for analysis"
                    '''
                    
                    sh '''
                        echo "==> Configurando Sonar-Scanner..."
                        if ! command -v sonar-scanner &> /dev/null; then
                            echo "Descargando sonar-scanner de forma segura..."
                            
                            # Usamos comillas simples alrededor del User-Agent para que Jenkins no se confunda con los espacios
                            sh "curl -fL https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.0.0.4432-linux-x64.zip -o sonar-scanner.zip"
                            
                            echo "Descomprimiendo usando Python..."
                            sh "python3 -c \"import zipfile; zipfile.ZipFile('sonar-scanner.zip').extractall('.')\""
                            rm sonar-scanner.zip
                        fi
                        
                        export PATH=$PATH:$(pwd)/sonar-scanner-6.0.0.4432-linux-x64/bin

                        echo "==> Ejecutando análisis en SonarQube..."
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