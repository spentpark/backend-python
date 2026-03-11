pipeline {
    agent any

    tools {
        nodejs 'node'
    }

    environment {
        NEXUS_VERSION       = "nexus3"
        NEXUS_PROTOCOL      = "http"
        NEXUS_URL           = "172.17.0.1:8081"
        NEXUS_REPOSITORY    = "npm-nexus-repo"
        NEXUS_CREDENTIAL_ID = "nexus"

        SONAR_HOST_URL = "http://172.17.0.1:9000"
        SONAR_TOKEN    = "squ_d27dacd45a6c18772d7e941fd44e1617cf5c4c38"

        APP_VERSION   = ""
        ARTIFACT_FILE = ""
    }

    stages {

        stage('Clean Install') {
            steps {
                sh '''
                    echo "Node version:"
                    node -v

                    echo "NPM version:"
                    npm -v

                    echo "Cleaning workspace..."
                    rm -rf node_modules coverage *.tgz

                    echo "Installing dependencies..."
                    npm install
                '''
            }
        }

        stage('Build + Test + Coverage + SonarQube') {
            steps {
                sh '''
                    echo "Running tests with coverage..."
                    npm run test:ci

                    echo "Installing sonar-scanner..."
                    npm install -g sonar-scanner

                    echo "Running SonarQube analysis..."
                    sonar-scanner \
                      -Dsonar.projectKey=mi-app-node \
                      -Dsonar.projectName=mi-app-node \
                      -Dsonar.sources=. \
                      -Dsonar.tests=. \
                      -Dsonar.test.inclusions=**/*.test.js \
                      -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info \
                      -Dsonar.host.url=$SONAR_HOST_URL \
                      -Dsonar.token=$SONAR_TOKEN
                '''
            }
        }

        /**
         * IMPORTANTE: version bump ANTES de package
         */
        stage('Version bump') {
            steps {
                script {
                    sh '''
                        BASE_VERSION=$(node -p "require('./package.json').version")
                        NEW_VERSION=${BASE_VERSION}-${BUILD_NUMBER}

                        echo "New version: $NEW_VERSION"

                        npm version $NEW_VERSION --no-git-tag-version
                    '''

                    env.APP_VERSION = sh(
                        script: "node -p \"require('./package.json').version\"",
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Package') {
            steps {
                script {

                    sh '''
                        echo "Packaging application..."
                        rm -f *.tgz
                        npm pack

                        echo "Generated package:"
                        ls -lh *.tgz
                    '''

                    env.ARTIFACT_FILE = sh(
                        script: "ls *.tgz | head -n 1",
                        returnStdout: true
                    ).trim()

                    echo "Application version: ${env.APP_VERSION}"
                    echo "Artifact file: ${env.ARTIFACT_FILE}"
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
                            echo "Configuring Nexus registry..."

                            npm config set registry http://$NEXUS_URL/repository/$NEXUS_REPOSITORY/

                            echo "//${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/:_auth=$(echo -n $NEXUS_USER:$NEXUS_PASS | base64)" > ~/.npmrc
                            echo "//${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/:email=jenkins@example.com" >> ~/.npmrc

                            echo "Publishing package version: $APP_VERSION"

                            npm publish \
                              --tag dev \
                              --registry http://$NEXUS_URL/repository/$NEXUS_REPOSITORY/
                        '''
                    }

                    echo "Published artifact: ${env.ARTIFACT_FILE}"
                }
            }
        }

        stage('Check coverage') {
            steps {
                sh '''
                    echo "Coverage files:"
                    ls -lh coverage/ || true
                '''
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
        echo "Pipeline finished"
    }

}
}