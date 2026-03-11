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
                    pip install pytest pytest-cov sonar-scanner build twine
                '''
            }
        }

        stage('Test + Coverage + SonarQube') {
            steps {
                sh '''
                    . venv/bin/activate
                    echo "Running tests with coverage..."
                    # Genera coverage.xml para SonarQube
                    pytest --cov=app tests/ --cov-report=xml:coverage.xml --cov-report=term

                    echo "Running SonarQube analysis..."
                    # Usamos el scanner de sistema o el instalado por pip
                    sonar-scanner \
                      -Dsonar.projectKey=mi-app-python \
                      -Dsonar.projectName=mi-app-python \
                      -Dsonar.sources=app \
                      -Dsonar.tests=tests \
                      -Dsonar.python.coverage.reportPaths=coverage.xml \
                      -Dsonar.host.url=$SONAR_HOST_URL \
                      -Dsonar.token=$SONAR_TOKEN
                '''
            }
        }

        stage('Version bump') {
            steps {
                script {
                    // En Python solemos manejar la versión en un archivo VERSION o dentro de setup.py/pyproject.toml
                    // Aquí simulamos el bump usando el BUILD_NUMBER de Jenkins
                    sh '''
                        echo "1.0.${BUILD_NUMBER}" > VERSION
                    '''
                    env.APP_VERSION = readFile('VERSION').trim()
                    echo "New version: ${env.APP_VERSION}"
                }
            }
        }

        stage('Package') {
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        echo "Packaging application (Wheel)..."
                        # Requiere un archivo básico setup.py o pyproject.toml en la raíz
                        python3 -m build
                    '''
                    
                    env.ARTIFACT_FILE = sh(
                        script: "ls dist/*.whl | head -n 1",
                        returnStdout: true
                    ).trim()

                    echo "Artifact generated: ${env.ARTIFACT_FILE}"
                }
            }
        }

        stage('Publish to Nexus') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: "${NEXUS_CREDENTIAL_ID}",
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASS'
                        )
                    ]) {
                        sh '''
                            . venv/bin/activate
                            echo "Publishing to Nexus PyPI repository..."
                            
                            # Twine es la herramienta estándar para subir paquetes Python
                            export TWINE_USERNAME=$NEXUS_USER
                            export TWINE_PASSWORD=$NEXUS_PASS
                            
                            python3 -m twine upload \
                              --repository-url http://$NEXUS_URL/repository/$NEXUS_REPOSITORY/ \
                              dist/*
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS - Version published: ${env.APP_VERSION}"
        }
        failure {
            echo "Pipeline FAILED"
        }
        always {
            // Limpiar el venv para no ocupar espacio en el agent
            sh 'rm -rf venv'
            echo "Pipeline finished"
        }
    }
}