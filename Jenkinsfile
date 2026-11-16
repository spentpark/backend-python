pipeline {
    agent any

    parameters {
        booleanParam(name: 'DEPLOY_ENABLED', defaultValue: true,
            description: 'Activa o desactiva el despliegue en el servidor Docker de 192.168.1.82.')
        string(name: 'DEPLOY_HOST', defaultValue: '192.168.1.82',
            description: 'IP o host del servidor Docker donde se despliega la aplicación.')
        string(name: 'SSH_CREDENTIALS_ID', defaultValue: 'docker-server-ssh',
            description: 'Credencial Jenkins "SSH Username with private key" con acceso al servidor Docker.')
        string(name: 'DEPLOY_DIR', defaultValue: '/home/spentpark/gitDeploy/gitreact',
            description: 'Carpeta del servidor donde se despliega el stack (contiene backend-python/ y frontend-react19/). Solo se usa para localizar la carpeta: el compose se publica desde el proyecto.')
        string(name: 'COMPOSE_FILE', defaultValue: 'docker-compose.yml',
            description: 'Nombre con el que se publica en el servidor el docker-compose.yml DEL PROYECTO (fuente de verdad del despliegue). No se lee el compose de la máquina.')
        string(name: 'COMPOSE_SERVICE', defaultValue: 'backend-python',
            description: 'Nombre del servicio del backend dentro de docker-compose.yml.')
        string(name: 'CONTAINER_NAME', defaultValue: 'backend-python',
            description: 'Nombre del contenedor que se detiene/levanta.')
        string(name: 'APP_PORT', defaultValue: '7000',
            description: 'Puerto publicado por el contenedor, usado para verificar que la aplicación arrancó.')
        string(name: 'PROBE_PATH', defaultValue: '/',
            description: 'Ruta HTTP de verificación (cualquier respuesta 2xx/3xx/401/403 cuenta como aplicación arriba).')
    }

    environment {
        // Nexus Config
        NEXUS_VERSION       = "nexus3"
        NEXUS_PROTOCOL      = "http"
        NEXUS_URL           = "192.168.1.82:8081"
        NEXUS_REPOSITORY    = "python-nexus-repo" // Asegúrate de crear un repo tipo 'pypi' en Nexus
        NEXUS_CREDENTIAL_ID = "nexus"

        // Sonar Config
        SONAR_HOST_URL = "http://192.168.1.82:9000"
        SONAR_TOKEN    = credentials('sonar-token')  //"squ_d235b7481cb93a1dc142c52f5a79fe0325e1ee31"

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
                    rm -rf venv build dist *.egg-info .pytest_cache coverage.xml htmlcov reports
                    
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

                        pip install pytest pytest-cov "httpx>=0.28.1" aiosqlite pytest-asyncio

                        # Genera el reporte JUnit XML que Jenkins publica en la vista del build
                        mkdir -p reports

                        pytest -W ignore \
                            --cov=app \
                            --cov-report=xml:coverage.xml \
                            --cov-report=html:htmlcov \
                            --junitxml=reports/junit.xml \
                            || echo "Tests failed but continuing for analysis"
                    '''

                    sh '''
                        echo "==> Verificando sonar-scanner..."
                        SONAR_DIR="$(pwd)/sonar-scanner"

                        if [ ! -f "${SONAR_DIR}/bin/sonar-scanner" ]; then
                            echo "Descargando sonar-scanner..."
                            curl -fL "https://repo1.maven.org/maven2/org/sonarsource/scanner/cli/sonar-scanner-cli/6.0.0.4432/sonar-scanner-cli-6.0.0.4432.zip" \
                                -o sonar-scanner.zip
                            python3 -c "import zipfile; zipfile.ZipFile('sonar-scanner.zip').extractall('sonar-scanner-extracted')"
                            rm sonar-scanner.zip
                            mv sonar-scanner-extracted/sonar-scanner-* "${SONAR_DIR}"
                        fi

                        echo "==> Aplicando permisos..."
                        chmod -R +x "${SONAR_DIR}/bin/"
                        chmod -R +x "${SONAR_DIR}/jre/bin/" 2>/dev/null || true

                        export PATH=$PATH:${SONAR_DIR}/bin

                        echo "==> Ejecutando análisis en SonarQube..."
                        sonar-scanner \
                        -Dsonar.projectKey=backend-python \
                        -Dsonar.sources=app \
                        -Dsonar.tests=tests \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.python.xunit.reportPath=reports/junit.xml \
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

        stage('Deploy backend en servidor Docker (192.168.1.82)') {
            when {
                expression { return params.DEPLOY_ENABLED == null || params.DEPLOY_ENABLED }
            }
            steps {
                withCredentials([sshUserPrivateKey(
                        credentialsId: params.SSH_CREDENTIALS_ID ?: 'docker-server-ssh',
                        keyFileVariable: 'SSH_KEY_FILE',
                        usernameVariable: 'SSH_USERNAME')]) {
                    withEnv([
                        "DEPLOY_HOST=${params.DEPLOY_HOST ?: '192.168.1.82'}",
                        "DEPLOY_DIR=${params.DEPLOY_DIR ?: '/home/spentpark/gitDeploy/gitreact'}",
                        "COMPOSE_FILE=${params.COMPOSE_FILE ?: 'docker-compose.yml'}",
                        "COMPOSE_SERVICE=${params.COMPOSE_SERVICE ?: 'backend-python'}",
                        "CONTAINER_NAME=${params.CONTAINER_NAME ?: 'backend-python'}",
                        "APP_PORT=${params.APP_PORT ?: '7000'}",
                        "PROBE_PATH=${params.PROBE_PATH ?: '/'}"
                    ]) {
                        sh '''set -eu

# ---------------------------------------------------------------------------
# Despliegue del backend por SSH en el servidor Docker remoto (192.168.1.82).
#
# La FUENTE DE VERDAD del compose es el docker-compose.yml DEL PROYECTO: el
# pipeline lo publica en DEPLOY_DIR y despliega con él. El docker-compose.yml
# que exista en la máquina NO se lee ni se usa para desplegar.
#
#  1. Comprueba SSH, Docker y Docker Compose en el servidor.
#  2. Localiza DEPLOY_DIR (parámetro o labels del contenedor) y valida el
#     docker-compose.yml del proyecto.
#  3. Sincroniza el código en ${DEPLOY_DIR}/backend-python y publica el
#     docker-compose.yml del proyecto como ${DEPLOY_DIR}/${COMPOSE_FILE}.
#  4. Construye la imagen en el servidor (ANTES de detener nada: si la
#     compilación falla, la versión anterior sigue corriendo).
#  5. Detiene el contenedor si estaba corriendo y levanta la nueva imagen;
#     si estaba abajo lo levanta desde cero. Verifica imagen y health check.
# ---------------------------------------------------------------------------

: "${DEPLOY_HOST:?DEPLOY_HOST no definido}"
: "${SSH_KEY_FILE:?SSH_KEY_FILE no definido}"
: "${SSH_USERNAME:?SSH_USERNAME no definido}"
: "${COMPOSE_SERVICE:?COMPOSE_SERVICE no definido}"
: "${CONTAINER_NAME:?CONTAINER_NAME no definido}"
: "${APP_PORT:?APP_PORT no definido}"
: "${PROBE_PATH:?PROBE_PATH no definido}"
: "${DEPLOY_DIR:=}"
: "${COMPOSE_FILE:=docker-compose.yml}"

# Compose del repositorio: única fuente de verdad del despliegue.
PROJECT_COMPOSE="docker-compose.yml"

WORKSPACE="${WORKSPACE:-$(pwd)}"
REMOTE_REPO_NAME="backend-python"

SSH_OPTS="-i ${SSH_KEY_FILE} -o BatchMode=yes -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=4"
SSH_TARGET="${SSH_USERNAME}@${DEPLOY_HOST}"

echo "================================================================"
echo " 1/5 Verificando servidor ${SSH_TARGET}"
echo "================================================================"

ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s" <<'REMOTE_SSH'
set -eu
echo "  - Servidor: $(hostname)"
docker --version
if docker compose version >/dev/null 2>&1; then
    echo "  - Docker Compose v2 disponible (comando: docker compose)"
else
    docker-compose --version
    echo "  - Docker Compose v1 disponible (comando: docker-compose)"
fi
REMOTE_SSH

echo "================================================================"
echo " 2/5 Localizando DEPLOY_DIR y validando el compose del proyecto"
echo "================================================================"

# Las labels de Docker se usan solo para localizar la CARPETA del despliegue
# (DEPLOY_DIR). El compose de la máquina NO se lee ni se reutiliza: el pipeline
# despliega siempre con el docker-compose.yml del proyecto.
CONFIG_FILES="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${CONTAINER_NAME}" <<'REMOTE_LABELS'
docker inspect -f '{{index .Config.Labels "com.docker.compose.project.config_files"}}' "$1" 2>/dev/null || true
REMOTE_LABELS
)"

COMPOSE_WORKDIR="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${CONTAINER_NAME}" <<'REMOTE_WORKDIR'
docker inspect -f '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$1" 2>/dev/null || true
REMOTE_WORKDIR
)"

case "${CONFIG_FILES}" in
    "<no value>"|"null"|"") CONFIG_FILES="" ;;
esac
case "${COMPOSE_WORKDIR}" in
    "<no value>"|"null"|"") COMPOSE_WORKDIR="" ;;
esac

if [ -n "${DEPLOY_DIR}" ]; then
    echo "  - DEPLOY_DIR indicado por parámetro: ${DEPLOY_DIR}"
elif [ -n "${CONFIG_FILES}" ]; then
    FIRST_COMPOSE="$(printf '%s' "${CONFIG_FILES}" | cut -d, -f1)"
    DEPLOY_DIR="$(dirname "${FIRST_COMPOSE}")"
    echo "  - DEPLOY_DIR detectado desde labels Docker: ${DEPLOY_DIR}"
elif [ -n "${COMPOSE_WORKDIR}" ]; then
    DEPLOY_DIR="${COMPOSE_WORKDIR}"
    echo "  - DEPLOY_DIR detectado desde working_dir Docker: ${DEPLOY_DIR}"
else
    echo "ERROR: no se pudo detectar la carpeta de despliegue en el servidor." >&2
    echo "       El contenedor ${CONTAINER_NAME} no existe o no fue creado con docker compose." >&2
    echo "       Relanza el job indicando el parámetro DEPLOY_DIR (ej: /home/spentpark/gitDeploy/gitreact)." >&2
    exit 1
fi

# COMPOSE_FILE ya no se detecta desde la máquina: es el nombre con el que se
# publica el compose del proyecto en DEPLOY_DIR.
case "${COMPOSE_FILE}" in
    */*) echo "ERROR: COMPOSE_FILE debe ser un nombre de archivo, no una ruta: ${COMPOSE_FILE}" >&2; exit 1 ;;
esac

if [ ! -f "${WORKSPACE}/${PROJECT_COMPOSE}" ]; then
    echo "ERROR: el proyecto no contiene ${PROJECT_COMPOSE}: no hay compose que desplegar." >&2
    echo "       El pipeline ya no usa el docker-compose de la máquina." >&2
    exit 1
fi
PROJECT_COMPOSE_HASH="$(sha256sum "${WORKSPACE}/${PROJECT_COMPOSE}" | cut -d' ' -f1)"
echo "  - Compose del proyecto: ${PROJECT_COMPOSE} (sha256 ${PROJECT_COMPOSE_HASH})"

# Validaciones de seguridad: DEPLOY_DIR se usa para borrar/crear el contexto
# de build, así que nunca debe quedar vacío, ser "/" ni contener "..".
case "${DEPLOY_DIR}" in
    "/") echo "ERROR: DEPLOY_DIR no puede ser /" >&2; exit 1 ;;
    *..*) echo "ERROR: DEPLOY_DIR no puede contener '..': ${DEPLOY_DIR}" >&2; exit 1 ;;
    *[!A-Za-z0-9._/-]*) echo "ERROR: DEPLOY_DIR tiene caracteres no permitidos: ${DEPLOY_DIR}" >&2; exit 1 ;;
    /*) ;;
    *) echo "ERROR: DEPLOY_DIR debe ser una ruta absoluta: ${DEPLOY_DIR}" >&2; exit 1 ;;
esac

case "${CONTAINER_NAME}" in
    ""|*[!A-Za-z0-9._-]*) echo "ERROR: CONTAINER_NAME inválido: ${CONTAINER_NAME}" >&2; exit 1 ;;
esac
case "${COMPOSE_SERVICE}" in
    ""|*[!A-Za-z0-9._-]*) echo "ERROR: COMPOSE_SERVICE inválido: ${COMPOSE_SERVICE}" >&2; exit 1 ;;
esac
case "${COMPOSE_FILE}" in
    ""|*[!A-Za-z0-9._-]*) echo "ERROR: COMPOSE_FILE inválido: ${COMPOSE_FILE}" >&2; exit 1 ;;
esac
case "${APP_PORT}" in
    ""|*[!0-9]*) echo "ERROR: APP_PORT inválido: ${APP_PORT}" >&2; exit 1 ;;
esac
case "${PROBE_PATH}" in
    /*) ;;
    *) echo "ERROR: PROBE_PATH debe empezar con /: ${PROBE_PATH}" >&2; exit 1 ;;
esac
case "${PROBE_PATH}" in
    *[!A-Za-z0-9._/?=-]*) echo "ERROR: PROBE_PATH tiene caracteres no permitidos: ${PROBE_PATH}" >&2; exit 1 ;;
esac

REMOTE_REPO="${DEPLOY_DIR}/${REMOTE_REPO_NAME}"
REMOTE_TMP="${DEPLOY_DIR}/.${REMOTE_REPO_NAME}.tmp"

echo "  - Contexto de build: ${REMOTE_REPO}"
echo "  - Servicio compose: ${COMPOSE_SERVICE} (contenedor ${CONTAINER_NAME})"
echo "  - Compose a usar: ${DEPLOY_DIR}/${COMPOSE_FILE} (publicado desde el proyecto)"

echo "================================================================"
echo " 3/5 Sincronizando código a ${SSH_TARGET}:${REMOTE_REPO}"
echo "================================================================"

# El Dockerfile recompila en el servidor, así que se excluyen los artefactos
# locales (venv, dist, cobertura, cachés…) y los secretos del agente.
TAR_EXCLUDES=""
for EXCL in ./venv ./.venv ./build ./dist ./*.egg-info ./.pytest_cache ./.coverage ./coverage.xml ./htmlcov ./reports ./.git ./.env ./.scannerwork ./sonar-scanner; do
    TAR_EXCLUDES="${TAR_EXCLUDES} --exclude=${EXCL}"
done

tar czf - -C "${WORKSPACE}" ${TAR_EXCLUDES} . | ssh ${SSH_OPTS} "${SSH_TARGET}" "set -e; mkdir -p '${DEPLOY_DIR}'; rm -rf '${REMOTE_TMP}'; mkdir -p '${REMOTE_TMP}'; tar xzf - -C '${REMOTE_TMP}'; rm -rf '${REMOTE_REPO}'; mv '${REMOTE_TMP}' '${REMOTE_REPO}'; echo '  - Código sincronizado correctamente'"

# Publicación del compose DEL PROYECTO: desde aquí el despliegue usa este
# archivo y deja de depender del docker-compose.yml de la máquina.
echo "  - Publicando ${PROJECT_COMPOSE} del proyecto en ${DEPLOY_DIR}/${COMPOSE_FILE}..."
REMOTE_COMPOSE_HASH="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "set -e; cp -f '${REMOTE_REPO}/${PROJECT_COMPOSE}' '${DEPLOY_DIR}/${COMPOSE_FILE}'; sha256sum '${DEPLOY_DIR}/${COMPOSE_FILE}' | cut -d' ' -f1")"
if [ "${REMOTE_COMPOSE_HASH}" != "${PROJECT_COMPOSE_HASH}" ]; then
    echo "ERROR: el compose publicado en el servidor no coincide con el del proyecto." >&2
    echo "       local=${PROJECT_COMPOSE_HASH} remoto=${REMOTE_COMPOSE_HASH}" >&2
    exit 1
fi
echo "  - Compose del proyecto publicado (sha256 ${REMOTE_COMPOSE_HASH} verificado)"

echo "================================================================"
echo " 4/5 Validando compose y construyendo imagen (servicio ${COMPOSE_SERVICE})"
echo "================================================================"

# Se valida el compose después de sincronizar para que el contexto de build
# exista. Imagen declarada en el servicio (la que se comprobará en el
# contenedor) y modo de construcción.
SERVICE_META="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${DEPLOY_DIR} ${COMPOSE_FILE} ${COMPOSE_SERVICE}" <<'REMOTE_PREFLIGHT'
set -eu
compose_dir="$1"; compose_file="$2"; service="$3"
cd "${compose_dir}"
if [ ! -f "${compose_file}" ]; then
    echo "ERROR: no existe ${compose_dir}/${compose_file} en el servidor." >&2
    exit 1
fi
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi
services="$($DC -f "${compose_file}" config --services)"
echo "  - Servicios definidos: $(echo ${services})"
echo "${services}" | grep -qx "${service}" || {
    echo "ERROR: el servicio '${service}' no está definido en ${compose_dir}/${compose_file}." >&2
    exit 1
}
service_config="$($DC -f "${compose_file}" config "${service}")"
if echo "${service_config}" | grep -qE '^[[:space:]]+build:'; then
    echo "HAS_BUILD=1"
else
    echo "HAS_BUILD=0"
fi
image="$(echo "${service_config}" | sed -n 's/^[[:space:]]*image:[[:space:]]*//p' | head -n 1)"
echo "COMPOSE_IMAGE=${image}"
REMOTE_PREFLIGHT
)"
echo "${SERVICE_META}"
HAS_BUILD="$(echo "${SERVICE_META}" | sed -n 's/^HAS_BUILD=//p')"
COMPOSE_IMAGE="$(echo "${SERVICE_META}" | sed -n 's/^COMPOSE_IMAGE=//p')"

if [ "${HAS_BUILD}" != "1" ]; then
    echo "ERROR: el servicio '${COMPOSE_SERVICE}' no define 'build:' en ${COMPOSE_FILE}." >&2
    exit 1
fi
case "${COMPOSE_IMAGE}" in
    "") echo "ERROR: el servicio '${COMPOSE_SERVICE}' no define 'image:' en ${COMPOSE_FILE}." >&2; exit 1 ;;
    *[!A-Za-z0-9._/:@-]*) echo "ERROR: nombre de imagen inválido: '${COMPOSE_IMAGE}'" >&2; exit 1 ;;
esac

# La imagen se construye con el compose DEL PROYECTO: así se aplican sus
# `build:`/`environment:` y el contenedor que se levanta es exactamente el que
# describe el repositorio. Se construye ANTES de detener nada: si falla, la
# versión anterior sigue corriendo.
ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${DEPLOY_DIR} ${COMPOSE_FILE} ${COMPOSE_SERVICE}" <<'REMOTE_BUILD'
set -eu
compose_dir="$1"; compose_file="$2"; service="$3"
cd "${compose_dir}"
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi
$DC -f "${compose_file}" build "${service}"
echo "  - Imagen construida correctamente (docker compose build)"
REMOTE_BUILD

BUILT_IMAGE_ID="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${COMPOSE_IMAGE}" <<'REMOTE_IMAGE_ID'
set -eu
docker image inspect -f '{{.Id}}' "$1"
REMOTE_IMAGE_ID
)"
echo "  - ID de la imagen construida: ${BUILT_IMAGE_ID} (${COMPOSE_IMAGE})"

echo "================================================================"
echo " 5/5 Deteniendo (si aplica) y levantando ${CONTAINER_NAME}"
echo "================================================================"

# Los contenedores del proyecto compose `gitreact` creados con el compose que
# vivía en la máquina usan nombres de servicio antiguos (`backend`/`frontend`).
# Compose no los reconocería como el servicio actual y fallaría al crear el
# contenedor por nombre duplicado: en ese caso se elimina solo ESTE contenedor
# (los demás servicios del stack se dejan intactos).
ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${DEPLOY_DIR} ${COMPOSE_FILE} ${COMPOSE_SERVICE} ${CONTAINER_NAME}" <<'REMOTE_DEPLOY'
set -eu
compose_dir="$1"; compose_file="$2"; service="$3"; container="$4"
cd "${compose_dir}"
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

if [ "$(docker inspect -f "{{.State.Running}}" "${container}" 2>/dev/null || true)" = "true" ]; then
    echo "  - El contenedor ${container} ESTABA EN EJECUCIÓN: se recrea con la nueva imagen."
    WAS_RUNNING="si"
else
    echo "  - El contenedor ${container} NO estaba corriendo (o no existe): se levanta desde cero."
    WAS_RUNNING="no"
fi

EXISTING_SERVICE="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "${container}" 2>/dev/null || true)"
case "${EXISTING_SERVICE}" in
    "<no value>"|"null"|"") EXISTING_SERVICE="" ;;
esac
if [ -n "${EXISTING_SERVICE}" ] && [ "${EXISTING_SERVICE}" != "${service}" ]; then
    echo "  - El contenedor ${container} pertenece al servicio anterior '${EXISTING_SERVICE}': se elimina para recrearlo como '${service}'."
    docker rm -f "${container}" >/dev/null
fi

echo "  - Levantando ${service} con la imagen recién construida..."
$DC -f "${compose_file}" up -d --force-recreate "${service}"

sleep 2
status="$(docker inspect -f "{{.State.Status}}" "${container}" 2>/dev/null || echo desconocido)"
echo "  - Contenedor ${container}: estado=${status} (corría antes: ${WAS_RUNNING})"
REMOTE_DEPLOY

CONTAINER_IMAGE_ID="$(ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${CONTAINER_NAME}" <<'REMOTE_CONTAINER_IMAGE'
set -eu
docker inspect -f '{{.Image}}' "$1"
REMOTE_CONTAINER_IMAGE
)"

# Si construimos una imagen concreta, el contenedor debe estar corriendo ESA
# imagen (si no, el compose publicado no está apuntando a la imagen construida).
if [ -n "${BUILT_IMAGE_ID}" ] && [ -n "${CONTAINER_IMAGE_ID}" ] && [ "${BUILT_IMAGE_ID}" != "${CONTAINER_IMAGE_ID}" ]; then
    echo "ERROR: el contenedor ${CONTAINER_NAME} no está usando la imagen recién construida." >&2
    echo "       Imagen construida:     ${BUILT_IMAGE_ID}" >&2
    echo "       Imagen del contenedor: ${CONTAINER_IMAGE_ID}" >&2
    exit 1
fi

echo "  - Esperando respuesta HTTP en el puerto ${APP_PORT}${PROBE_PATH}..."
ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${CONTAINER_NAME} ${APP_PORT} ${PROBE_PATH}" <<'REMOTE_HEALTH'
set -eu
container="$1"; port="$2"; path="$3"
attempt=0
while [ "${attempt}" -lt 30 ]; do
    attempt=$((attempt + 1))
    code="$(docker exec "${container}" python -c '
import sys
import urllib.error
import urllib.request

try:
    with urllib.request.urlopen(sys.argv[1], timeout=5) as response:
        print(response.status)
except urllib.error.HTTPError as error:
    print(error.code)
except Exception:
    print(0)
' "http://127.0.0.1:${port}${path}" 2>/dev/null || true)"
    case "${code:-0}" in
        2??|3??|401|403)
            echo "  - La aplicación respondió HTTP ${code} (intento ${attempt})."
            exit 0
            ;;
    esac
    sleep 5
done
echo "ERROR: la aplicación no respondió en el puerto ${port}${path} tras 150 segundos." >&2
echo "---- Últimas 100 líneas del contenedor ${container} ----" >&2
docker logs --tail 100 "${container}" >&2 || true
exit 1
REMOTE_HEALTH

ssh ${SSH_OPTS} "${SSH_TARGET}" "sh -s -- ${CONTAINER_NAME}" <<'REMOTE_CLEANUP'
set -eu
container="$1"
docker image prune -f >/dev/null 2>&1 || true
docker ps --filter "name=${container}" --format "  - {{.Names}} | {{.Image}} | {{.Status}} | {{.Ports}}"
REMOTE_CLEANUP

echo "================================================================"
echo " Despliegue completado: http://${DEPLOY_HOST}:${APP_PORT}"
echo "================================================================"
'''
                    }
                }
            }
        }

        /*
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
        */
    }

    post {
        always {
            // Publica el reporte de tests unitarios en la vista del build (JUnit)
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'coverage.xml,reports/junit.xml,htmlcov/**', allowEmptyArchive: true

            // En Docker no hace falta borrar el venv porque el contenedor se destruye
            cleanWs()
            echo "Pipeline finished"
        }

        failure {
            echo "Si el fallo fue en el despliegue, revisa el contenedor: ssh <usuario>@${params.DEPLOY_HOST ?: '192.168.1.82'} docker logs --tail 200 ${params.CONTAINER_NAME ?: 'backend-python'}"
        }
    }
}
