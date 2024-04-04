# =================================================================================================================
# Usage:
# -----------------------------------------------------------------------------------------------------------------
usage () {
  cat <<-EOF

  Usage: $0 [command] [options]

  Commands:

  build [ -a agent ]* args
    Build the docker images for the agents and the test harness.
      You need to do this first.
      - "agent" must be one from the supported list: ${VALID_AGENTS}
      - multiple agents may be built by specifying multiple -a options
      - By default, all agents and the harness will be built

  rebuild [ -a agent ]* args
    Same as build, but adds the --no-cache option to force building from scratch

  run [ -a/b/f/m/d agent ] [-r allure [-e comparison]] [ -i <ini file> ] [ -o <output file> ] [ -n ] [ -v <AIP level> ] [ -t tags ]*
    Run the tagged tests using the specified agents for Acme, Bob, Faber and Mallory.
      Select the agents for the roles of Acme (-a), Bob (-b), Faber (-f) and Mallory (-m).
      - For all to be set to the same, use "-d" for default.
      - The value for agent must be one of: ${VALID_AGENTS}
      Use -t option(s) to indicate tests with the gives tag(s) are to be executed.
        -t options can NOT have spaces, even if the option is quoted; use a behave INI file instead (-i option)
        For not running tagged tests, specify a ~ before the tag, e.g. "-t ~@wip" runs tests that don't have the "@wip" tag
      Use -v to specify the AIP level, in case the agent needs to customize its startup configuration
        "-v 10" or "-v 20"
      Use the -i option to use the specified file as the behave.ini file for the run
      - Default is the behave.ini file in the "aries-test-harness" folder
      Use the -r option to output to allure
        (allure is the only supported option)
      Use the -e option to compare current results to Known Good Results (KGR)
        (comparison is the only supported option)
      Use the -n option to start ngrok endpoints for each agent
        (this is *required* when testing with a Mobile agent)

    Examples:
    $0 run -a acapy -b vcx -f vcx -m acapy  - Run all the tests using the specified agents per role
    $0 run -d vcx                           - Run all tests for all features using the vcx agent in all roles
    $0 run -d acapy -t @SmokeTest -t @P1    - Run the tests tagged @SmokeTest and/or @P1 (priority 1) using all ACA-Py agents
    $0 run -d acapy -b mobile -n -t @MobileTest  - Run the mobile tests using ngrok endpoints

  runset - Run the set of tests for a combination of Test Agents using the parameters in the daily, GitHub Action run "runsets".
      To see full set of options for the "runset" command, execute "./manage runset -h"

  tags - Get a list of the tags on the features tests

  tests -t <tags> [ -md ]
    Display selected test scenarios/features filtered by associated tags.
    A list of relevant tags can be given as comma seperated list (with no spaces)
    Optionaly, the output can be displayed as --markdown table

    Examples:
    $0 tests -h
    $0 tests -t AIP10,AIP20
    $0 tests -t critical -md


  dry-run [ -i <ini file> ] [ -o <output file> ] [ -t tags ]*
    Uses the Behave "dry-run" feature to get a lists of the Features, Scenarios and Tags
    that would be run based on the provided the command line arguments. Useful for seeing what tests
    a combination of "-t" (tag) arguments will cause to be run.
    Accepts all the same parameters as 'run', but ignores -a/b/f/m/d/n/r/e/v

  test [-r allure [-e comparison]] [ -i <ini file> ] [ -o <output file> ] [ -n ] [ -v <AIP level> ] [ -t tags ]*
    Run the tagged tests using the set of agents that were started with the 'start' command, using all the same parameters as 'run',
    except -a/b/f/m/d/n.

  scenarios - synonym for tests, but longer and harder to spell

  service [build|start|stop|logs|clean] service-name
    Run the given service command on the given service. Commands:
      - build: build the service (only needed for von-network).
      - start: start the service, creating the AATH docker network if necessary.
      - stop: stop the service, deleting the AATH docker network if it's now unused.
      - logs: print the scrolling logs of the service. Ctrl-C to exit.
      - clean: clean up the service containers and build files, if any.

  start [ -a/b/f/m/d agent ]* [-n]
    Initialize the test harness using the specified agents for Acme, Bob, Faber and Mallory.
      Select the agents for the roles of Acme (-a), Bob (-b), Faber (-f) and Mallory (-m).
      - For all to be set to the same, use "-d" for default.
      - The value for agent must be one of: ${VALID_AGENTS}
    Use the -n option to start ngrok endpoints for each agent
        (this is *required* when testing with a Mobile agent)

  stop - stop the test harness.

  rebuild - Rebuild the docker images.

  dockerhost - Print the ip address of the Docker Host Adapter as it is seen by containers running in docker.
EOF
exit 1
}

toLower() {
  echo $(echo ${@} | tr '[:upper:]' '[:lower:]')
}

function echoRed (){
  _msg="${@}"
  _red='\e[31m'
  _nc='\e[0m' # No Color
  echo -e "${_red}${_msg}${_nc}"
}

function initDockerBuildArgs() {
  dockerBuildArgs=""

  # HTTP proxy, prefer lower case
  if [[ "${http_proxy}" ]]; then
    dockerBuildArgs=" ${dockerBuildArgs} --build-arg http_proxy=${http_proxy}"
  else
    if [[ "${HTTP_PROXY}" ]]; then
      dockerBuildArgs=" ${dockerBuildArgs} --build-arg http_proxy=${HTTP_PROXY}"
    fi
  fi

  # HTTPS proxy, prefer lower case
  if [[ "${https_proxy}" ]]; then
    dockerBuildArgs=" ${dockerBuildArgs} --build-arg https_proxy=${https_proxy}"
  else
    if [[ "${HTTPS_PROXY}" ]]; then
      dockerBuildArgs=" ${dockerBuildArgs} --build-arg https_proxy=${HTTPS_PROXY}"
    fi
  fi

  echo ${dockerBuildArgs}
}

function initEnv() {

  if [ -f .env ]; then
    while read line; do
      if [[ ! "$line" =~ ^\# ]] && [[ "$line" =~ .*= ]]; then
        export ${line//[$'\r\n']}
      fi
    done <.env
  fi

  for arg in "$@"; do
    # Remove recognized arguments from the list after processing.
    shift
    case "$arg" in
      *=*)
        export "${arg}"
        ;;
      *)
        # If not recognized, save it for later procesing ...
        set -- "$@" "$arg"
        ;;
    esac
  done

  export LOG_LEVEL=${LOG_LEVEL:-info}
  export RUST_LOG=${RUST_LOG:-warning}
}

# setup the docker environment variables to be passed to containers
setDockerEnv() {
    # set variables that have a different name to what is being set for the container
  DOCKER_ENV="-e AGENT_NAME=${NAME}"
  if  [[ -n "$BACKCHANNEL_EXTRA_ARGS" ]]; then
    DOCKER_ENV="${DOCKER_ENV} -e EXTRA_ARGS=${BACKCHANNEL_EXTRA_ARGS}"
  fi
  if  [[ -n "$LEDGER_URL_INTERNAL" ]]; then
    DOCKER_ENV="${DOCKER_ENV} -e LEDGER_URL=${LEDGER_URL_INTERNAL}"
  fi
  if  [[ -n "$TAILS_SERVER_URL_INTERNAL" ]]; then
    DOCKER_ENV="${DOCKER_ENV} -e TAILS_SERVER_URL=${TAILS_SERVER_URL_INTERNAL}"
  fi
  if ! [ -z "$TEST_RETRY_ATTEMPTS_OVERRIDE" ]; then
    DOCKER_ENV="${DOCKER_ENV} -e TEST_RETRY_ATTEMPTS_OVERRIDE=${TEST_RETRY_ATTEMPTS_OVERRIDE}"
  fi

  # variables that have the same variable name as what is being set for the container
  declare -a GENERAL_VARIABLES=("DOCKERHOST" "NGROK_NAME" "CONTAINER_NAME" "AIP_CONFIG" "AGENT_CONFIG_FILE" "GENESIS_URL" "GENESIS_FILE")
  for var in "${GENERAL_VARIABLES[@]}"; do
    if [[ -n "${!var}" ]]; then
      DOCKER_ENV+=" -e ${var}=${!var}"
    fi
  done
}

# TODO: set up image builds so you don't need to use `./manage rebuild` to refresh remote source repo
# - image Dockerfile has an ARG for the commit hash,
# - build script grabs the HEAD commit hash from the agent's github repo

# Build images -- add more backchannels here...
# TODO: Define args to build only what's needed
buildImages() {
  args=${@}

  echo Agents to build: ${BUILD_AGENTS}

  for agent in ${BUILD_AGENTS}; do
    export BACKCHANNEL_FOLDER=$(dirname "$(find aries-backchannels -name *.${agent})" )
    echo Backchannel Folder: ${BACKCHANNEL_FOLDER}
    if [ -e "${BACKCHANNEL_FOLDER}/Dockerfile.${agent}" ]; then
      echo "Building ${agent}-agent-backchannel ..."
      local REPO_ARGS
      REPO_ARGS=
      if [[ -f "${BACKCHANNEL_FOLDER}/${agent}.repoenv" ]]; then
        source "${BACKCHANNEL_FOLDER}/${agent}.repoenv"
        if [[ -n "${REPO_URL}" ]]; then
          local REPO_COMMIT
          if [[ -z ${REPO_BRANCH} ]]; then
            REPO_BRANCH=HEAD
          fi
          REPO_COMMIT=$(git ls-remote ${REPO_URL} ${REPO_BRANCH} | cut -f1)
          REPO_ARGS="--build-arg REPO_URL=${REPO_URL} --build-arg REPO_COMMIT=${REPO_COMMIT}"
        fi
      fi

      if ! docker build \
        ${args} \
        $(initDockerBuildArgs) \
        ${REPO_ARGS} \
        -t "${agent}-agent-backchannel" \
        -f "${BACKCHANNEL_FOLDER}/Dockerfile.${agent}" "aries-backchannels/"; then
          echo "Docker image build failed."
          exit 1
      fi
    else
      echo "Unable to find Dockerfile to build agent: ${agent}"
      echo "Must be one of: ${VALID_AGENTS}"
    fi
  done

  echo "Building aries-test-harness ..."
  if ! docker build \
    ${args} \
    $(initDockerBuildArgs) \
    -t 'aries-test-harness' \
    -f 'aries-test-harness/Dockerfile.harness' 'aries-test-harness/'; then
      echo "Docker image build failed."
      exit 1
  fi
}

pingLedger(){
  ledger_url=${1}

  # ping ledger web browser for genesis txns
  local rtnCd=$(curl -s --write-out '%{http_code}' --output /dev/null ${ledger_url})
  if (( ${rtnCd} == 200 )); then
    return 0
  else
    return 1
  fi
}

waitForLedger(){
  (
    # Wait for ledger server to start or if remote wait for it to respond  ...
    local startTime=${SECONDS}
    local rtnCd=0

    # Determine the ping URL based on the ledger variables
    local pingUrl=""
    if [[ -n "${GENESIS_URL}" ]]; then
      pingUrl="${GENESIS_URL}"
    else
      pingUrl="${LEDGER_URL_HOST}/genesis"
    fi

    printf "waiting for ledger to start/respond"
    # use ledger URL from host
    while ! pingLedger "${pingUrl}"; do
      printf "."
      local duration=$(($SECONDS - $startTime))
      if (( ${duration} >= ${LEDGER_TIMEOUT} )); then
        echoRed "\nThe Indy Ledger failed to start within ${duration} seconds.\n"
        rtnCd=1
        break
      fi
      sleep 1
    done
    echo
    return ${rtnCd}
  )
}

pingTailsServer(){
  tails_server_url=${1}

  # ping tails server (ask for a non-existant registry and should return 404)
  local rtnCd=$(curl -s --write-out '%{http_code}' --output /dev/null ${tails_server_url}/404notfound)
  if (( ${rtnCd} == 404 )); then
    return 0
  else
    return 1
  fi
}

waitForTailsServer(){
  (
    # Wait for tails server to start ...
    local startTime=${SECONDS}
    local rtnCd=0
    printf "waiting for tails server to start"
    # use tails server URL from host
    while ! pingTailsServer "$TAILS_SERVER_URL_HOST"; do
      printf "."
      local duration=$(($SECONDS - $startTime))
      if (( ${duration} >= ${LEDGER_TIMEOUT} )); then
        echoRed "\nThe tails server failed to start within ${duration} seconds.\n"
        rtnCd=1
        break
      fi
      sleep 1
    done
    echo
    return ${rtnCd}
  )
}

pingUniresolver(){

  # ping uniresolver server
  local rtnCd=$(curl -s --write-out '%{http_code}' --output /dev/null http://localhost:8080/actuator/health)
  if (( ${rtnCd} == 200 )); then
    return 0
  else
    return 1
  fi
}

waitForUniresolver(){
  (
    # Wait for uniresolver to start ...
    local startTime=${SECONDS}
    local rtnCd=0
    printf "waiting for uniresolver to start"
    while ! pingUniresolver ; do
      printf "."
      local duration=$(($SECONDS - $startTime))
      if (( ${duration} >= ${LEDGER_TIMEOUT} )); then
        echoRed "\nUniversal Resolver failed to start within ${duration} seconds.\n"
        rtnCd=1
        break
      fi
      sleep 1
    done
    echo
    return ${rtnCd}
  )
}

pingRedisCluster(){
  redis_cluster_url_host=${1}
  # ping tails server (ask for a non-existant registry and should return 404)
  local rtnCd=$(curl -s --write-out '%{http_code}' --output /dev/null ${redis_cluster_url_host})
  if (( ${rtnCd} == 000 )); then
    return 0
  else
    return 1
  fi
}

waitForRedisCluster(){
  (
    # Wait for tails server to start ...
    local startTime=${SECONDS}
    local rtnCd=0
    printf "waiting for redis-cluster to start"
    # use tails server URL from host
    while ! pingRedisCluster "$REDIS_CLUSTER_URL_HOST"; do
      printf "."
      local duration=$(($SECONDS - $startTime))
      if (( ${duration} >= ${LEDGER_TIMEOUT} )); then
        echoRed "\nThe redis cluster failed to start within ${duration} seconds.\n"
        rtnCd=1
        break
      fi
      sleep 1
    done
    echo
    return ${rtnCd}
  )
}

dockerhost_url_templates() {
  # generate acapy plugin config file, writing $DOCKERHOST into URLs
  pushd ${SCRIPT_HOME}/aries-backchannels/acapy/ > /dev/null

  mkdir -p .build/acapy-main.data
  mkdir -p .build/acapy.data

  sed "s/REPLACE_WITH_DOCKERHOST/${DOCKERHOST}/g" plugin-config.template | tee > .build/plugin-config.yml

  rm -f .build/acapy-main.data/plugin-config.yml .build/acapy.data/plugin-config.yml
  cp .build/plugin-config.yml .build/acapy-main.data/plugin-config.yml
  mv .build/plugin-config.yml .build/acapy.data/plugin-config.yml

  popd > /dev/null
}

pingAgent(){
  name=${1}
  port=${2}

  # ping agent using a backchannel-exposed api
  rtnCd=$(curl -s --write-out '%{http_code}' --output /dev/null http://localhost:${port}/agent/command/status/)
  if (( ${rtnCd} == 200 )); then
    return 0
  else
    return 1
  fi
}

waitForAgent(){
  (
    name=${1}

    # Wait for agent to start ...
    local startTime=${SECONDS}
    rtnCd=0
    printf "waiting for ${name} agent to start"
    while ! pingAgent ${@}; do
      printf "."
      local duration=$(($SECONDS - $startTime))
      if (( ${duration} >= ${AGENT_TIMEOUT} )); then
        echoRed "\nThe agent failed to start within ${duration} seconds.\n"
        rtnCd=1
        break
      fi
      sleep 1
    done
    echo
    return ${rtnCd}
  )
}

startAgent() {
  local NAME=$1
  local CONTAINER_NAME=$2
  local IMAGE_NAME=$3
  local PORT_RANGE=$4
  local BACKCHANNEL_PORT=$5
  local AGENT_ENDPOINT_PORT=$6
  local AIP_CONFIG=$7
  local AGENT_NAME=$8

  local BACKCHANNEL_DIR=$(dirname "$(find aries-backchannels -name *.${AGENT_NAME})" )

  local ENV_PATH="$(find $BACKCHANNEL_DIR -name *${AGENT_NAME}.env)"
  local ENV_FILE_ARG=

  if [[ -n $ENV_PATH ]]; then
    ENV_FILE_ARG="--env-file=$ENV_PATH"
    # echo $ENV_FILE_ARG
  fi

  local DATA_VOLUME_PATH="$(find $BACKCHANNEL_DIR -wholename */${AGENT_NAME}.data)"
  local DATA_VOLUME_ARG=
  # optional data volume folder
  if [[ -n DATA_VOLUME_PATH  ]]; then
    DATA_VOLUME_ARG="-v $(pwd)/$DATA_VOLUME_PATH:/data-mount:z"
  fi

  if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    if [[ "${USE_NGROK}" = "true" ]]; then
      # Turning off the starting of each ngrok tunnel for each agent. All tunnels are started when the ngrok service starts.
      # There was an attempt to just start the service and then only start the tunnels when the agent was started, but 
      # That is not working. When we call start below, we get an error on the web_addr port in the config file. 
      # If this can be solved in the future we can re-enable this code, and make sure the ngrok service starts with the --none flag.
      # echo "Starting ngrok for ${NAME} Agent ... on port ${AGENT_ENDPOINT_PORT}"
      # # call the ngrok container to start the tunnel for the agent
      # docker exec "${NGROK_NAME}" ngrok start --config /etc/ngrok.yml "${CONTAINER_NAME}_ngrok"

      # if we are using ngrok we will have to export the CONTAINER_NAME to be used by the ngrok_wait script
      export CONTAINER_NAME="${CONTAINER_NAME}"
    fi

    echo "Starting ${NAME} Agent using ${IMAGE_NAME} ..."
    export BACKCHANNEL_EXTRA_ARGS_NAME="BACKCHANNEL_EXTRA_${AGENT_NAME//-/_}"
    export BACKCHANNEL_EXTRA_ARGS=`echo ${!BACKCHANNEL_EXTRA_ARGS_NAME}`

    # set the docker environment that needs to be passed to the test container
    setDockerEnv

    local container_id=$(docker run -dt --name "${CONTAINER_NAME}" --network aath_network --expose "${PORT_RANGE}" -p "${PORT_RANGE}:${PORT_RANGE}" ${DATA_VOLUME_ARG} ${ENV_FILE_ARG} $DOCKER_ENV "${IMAGE_NAME}" -p "${BACKCHANNEL_PORT}" -i false)

    sleep 1
    if [[ "${USE_NGROK}" = "true" ]]; then
      docker network connect aath_network "${CONTAINER_NAME}"
    elif [[ "${AGENT_NAME}" = "afgo-master" || "${AGENT_NAME}" = "afgo-interop" ]]; then
      docker network connect aath_network "${CONTAINER_NAME}"
    fi
    if [[ "${IMAGE_NAME}" = "mobile-agent-backchannel" ]]; then
      echo "Tail-ing log files for ${NAME} agent in ${container_id}"
      docker logs -f ${container_id} &
    fi
  else
    echo "${NAME} Agent already running, skipping..."
  fi
}

writeEnvProperties() {
  ACME_VERSION=$(getAgentVersion 9020)
  BOB_VERSION=$(getAgentVersion 9030)
  FABER_VERSION=$(getAgentVersion 9040)
  MALLORY_VERSION=$(getAgentVersion 9050)

  env_file="$(pwd)/aries-test-harness/allure/allure-results/environment.properties"
  declare -a env_array
  env_array+=("role.acme=$ACME_AGENT")
  env_array+=("acme.agent.version=$ACME_VERSION")
  env_array+=("role.bob=$BOB_AGENT")
  env_array+=("bob.agent.version=$BOB_VERSION")
  env_array+=("role.faber=$FABER_AGENT")
  env_array+=("faber.agent.version=$FABER_VERSION")
  env_array+=("role.mallory=$MALLORY_AGENT")
  env_array+=("mallory.agent.version=$MALLORY_VERSION")
  printf "%s\n" "${env_array[@]}" > $env_file

}

getAgentVersion(){
  port=${1}
  # get agent version using a backchannel-exposed api
  version=$(curl -s http://localhost:${port}/agent/command/version/)
  echo "$version"
  # if (( ${rtnCd} == 200 )); then
  #   echo "$version"
  # else
  #   echo "unknown"
  # fi
}

createNetwork() {
  if [[ -z `docker network ls -q --filter "name=aath_network"` ]]; then
    docker network create aath_network --subnet=174.96.0.0/16 > /dev/null
  fi
}

cleanupNetwork() {
  if [[ -z `docker ps -q --filter "network=aath_network"` && `docker network ls -q --filter "name=aath_network"` ]]; then
    docker network rm aath_network > /dev/null
  fi
}

auxiliaryService() {
  local SERVICE_NAME
  local SERVICE_COMMAND
  SERVICE_NAME=$1
  SERVICE_COMMAND=$2

  if [[ -f "./services/${SERVICE_NAME}/wrapper.sh" ]]; then
    (./services/${SERVICE_NAME}/wrapper.sh $SERVICE_COMMAND)
  else
    echo "service ${SERVICE_NAME} doesn't exist"
  fi
}

startServices() {
  # sets if services this procedure starts should be stopped automatically
  if [[ "auto" = $1 ]]; then
    export AUTO_CLEANUP=true
  else
    export AUTO_CLEANUP=false
  fi

  if [[ "all" = $1 ]]; then
    auxiliaryService orb start
    # auxiliaryService redis-cluster start
  fi

  # if we're *not* using an external VON ledger, start the local one
  if [[ -z ${LEDGER_URL_CONFIG} && -z ${GENESIS_URL} && -z ${GENESIS_FILE} ]]; then
    if [[ -z `docker ps -q --filter="name=von_webserver_1"` ]] && [[ -z $(docker ps -q --filter="name=von-webserver-1") ]]; then
      echo "starting local von-network..."
      auxiliaryService von-network start
      if [[ $AUTO_CLEANUP ]]; then
        export STARTED_LOCAL_LEDGER=true
      fi
    fi
  fi

  if ! waitForLedger; then
    echoRed "\nThe Indy Ledger is not running.\n"
    exit 1
  fi

  if [[ -z `docker ps -q --filter="name=uni-resolver-web.local"` ]]; then
      echo "starting local uniresolver..."
    auxiliaryService uniresolver start
    if [[ $AUTO_CLEANUP ]]; then
      export STARTED_LOCAL_UNIRESOLVER=true
    fi
  fi

  # if we're *not* using an external indy tails server, start the local one
  if [[ -z ${TAILS_SERVER_URL_CONFIG} ]]; then
    if [[ -z `docker ps -q --filter="name=docker_tails-server_1"` ]] && [[ -z $(docker ps -q --filter="name=docker-tails-server-1") ]]; then
      echo "starting local indy-tails-server..."
      auxiliaryService indy-tails start
      if [[ $AUTO_CLEANUP ]]; then
        export STARTED_LOCAL_TAILS=true
      fi
    fi
  fi

  if ! waitForTailsServer; then
    echoRed "\nThe Indy Tails Server is not running.\n"
    exit 1
  fi

  if ! waitForUniresolver; then
    echoRed "\nUniversal Resolver is not running.\n"
    exit 1
  fi

}

stopServices() {
  if [[ "auto" = $1 ]]; then
    if [[ ${STARTED_LOCAL_UNIRESOLVER} ]]; then
      echo "stopping local uniresolver..."
      auxiliaryService uniresolver stop
    fi

    if [[ ${STARTED_LOCAL_TAILS} ]]; then
      echo "stopping local indy-tails-server..."
      auxiliaryService indy-tails stop
    fi

    if [[ ${STARTED_LOCAL_LEDGER} ]]; then
      echo "stopping local von-network..."
      auxiliaryService von-network stop
    fi

  elif [[ "all" = $1 ]]; then
    auxiliaryService uniresolver stop
    auxiliaryService orb stop
    auxiliaryService indy-tails stop
    auxiliaryService von-network stop
    auxiliaryService redis-cluster stop

  fi
}

serviceCommand() {
  local SERVICE_COMMAND
  SERVICE_COMMAND=$1
  local SERVICE_TARGET
  SERVICE_TARGET=$2

  # TODO: allow multiple services to be named - but can we handle logs command then?
  if [[ "all" = $SERVICE_TARGET ]]; then
    case "${SERVICE_COMMAND}" in
      start)
          createNetwork
          startServices all
        ;;
      stop)
          stopServices all
          cleanupNetwork
        ;;
      *)
          echo err: \'start\' and \'stop\' are only valid commands for target \'all\'
        ;;
    esac

    return
  fi

  case "${SERVICE_COMMAND}" in
    start)
        createNetwork
        auxiliaryService ${SERVICE_TARGET} ${SERVICE_COMMAND}
      ;;
    logs)
        auxiliaryService ${SERVICE_TARGET} ${SERVICE_COMMAND}
      ;;
    stop|clean)
        auxiliaryService ${SERVICE_TARGET} ${SERVICE_COMMAND}
        cleanupNetwork
      ;;
    *)
        auxiliaryService ${SERVICE_TARGET} ${SERVICE_COMMAND}
      ;;
  esac
}

startHarness(){
  echo Agents to be used:
  echo "  Acme - ${ACME}"
  echo "  Bob - ${BOB}"
  echo "  Faber - ${FABER}"
  echo "  Mallory - ${MALLORY}"
  echo ""

  createNetwork

  startServices auto

  dockerhost_url_templates

  export AIP_CONFIG=${AIP_CONFIG:-10}

  # Standup the ngrok container if we are using ngrok
  if [[ "${USE_NGROK}" = "true" ]]; then
    echo "Starting ngrok service for test harness ..."
    if  [[ -n "$NGROK_AUTHTOKEN" ]]; then
      NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN}"
    else
      NGROK_AUTHTOKEN="harness_${NGROK_AUTHTOKEN}"
    fi
    # start the ngrok container but don't start the tunnels in the config yml file. We will start them later as needed for each agent.
    docker run -d --rm -v $(pwd)/aath_ngrok_config.yml:/etc/ngrok.yml -e NGROK_CONFIG=/etc/ngrok.yml -e NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN}" --name agents-ngrok --network aath_network -p 4040:4040 ngrok/ngrok start --all
    
    export NGROK_NAME="agents-ngrok"
  else
    # if NGROK_NAME is populated then don't export it to null.
    if [[ -z "$NGROK_NAME" ]]; then
      export NGROK_NAME=
    fi
  fi

  # Only start agents that are asked for in the ./manage start command
  if [[ "$ACME" != "none" ]]; then
    export ACME_AGENT=${ACME_AGENT:-${ACME}-agent-backchannel}
    startAgent Acme acme_agent "$ACME_AGENT" "9020-9029" 9020 9021 "$AIP_CONFIG" "$ACME"
  fi
  if [[ "$BOB" != "none" ]]; then
    export BOB_AGENT=${BOB_AGENT:-${BOB}-agent-backchannel}
    startAgent Bob bob_agent "$BOB_AGENT" "9030-9039" 9030 9031 "$AIP_CONFIG" "$BOB"
  fi
  if [[ "$FABER" != "none" ]]; then
    export FABER_AGENT=${FABER_AGENT:-${FABER}-agent-backchannel}
    startAgent Faber faber_agent "$FABER_AGENT" "9040-9049" 9040 9041 "$AIP_CONFIG" "$FABER"
  fi
  if [[ "$MALLORY" != "none" ]]; then
    export MALLORY_AGENT=${MALLORY_AGENT:-${MALLORY}-agent-backchannel}
    startAgent Mallory mallory_agent "$MALLORY_AGENT" "9050-9059" 9050 9051 "$AIP_CONFIG" "$MALLORY"
  fi

  echo
  # Check if agents were successfully started.
  if [[ "$ACME" != "none" ]]; then
    waitForAgent Acme 9020
  fi
  if [[ "$BOB" != "none" ]]; then
    waitForAgent Bob 9030
  fi
  if [[ "$FABER" != "none" ]]; then
    waitForAgent Faber 9040
  fi
  if [[ "$MALLORY" != "none" ]]; then
    waitForAgent Mallory 9050
  fi
  echo

  export PROJECT_ID=${PROJECT_ID:-general}

  echo
  # Allure Reports environment.properties file handling
  # Only do this if reporting parameter is passed.
  if [[ "${REPORT}" = "allure" ]]; then
    writeEnvProperties
  fi
}

deleteAgents() {
    deleteAgent acme_agent
    deleteAgent bob_agent
    deleteAgent faber_agent
    deleteAgent mallory_agent
}

deleteAgent() {
    agent=$1
    docker rm -f $agent || 1
}

runSetUsage() {
  # =================================================================================================================
  # runset Usage:
  # -----------------------------------------------------------------------------------------------------------------
  cat <<-EOF

    Usage: $0 runset [run-set-name] [options]

    Command: runset

    Run the agents and tests for a named "runset", one of the test runs executed nightly via GitHub Actions.
    
    Options:

      -b : run a "build" for the runset agents before the "run"
      -r : run a "rebuild" for the runset agents before the "run"
      -n : dry-run; don't run the commands, just print them

    The run-set-name must be one from the following list, each associated with a GHA file in .github/workflows.
    In most cases, the first named framework in the runset name runs Acme, Faber and Mallory, and the second, Bob.

EOF
    listRunSets | tr '\n' ' '
    echo ""
}

listRunSets() {
  for runset in .github/workflows/*test-harness-*.yml; do
    echo $runset | sed "s/.*test-harness-//" | sed "s/.yml//"
  done
}

runRunSet() {
  runSets=$(listRunSets)
  for i in $runSets; do
    if [[ "${runSet}" == "$i" ]]; then
      runSetFile=.github/workflows/*-harness-${runSet}.yml
      break
    fi
  done
  if [[ -z ${runSetFile} ]]; then
     echo Error: AATH RunSet $1 not found, must be one of:
     echo ""
     listRunSets | tr '\n' ' '
     echo ""
     echo ""
     echo For help, run \"./manage runset -h\"
     exit 1
  fi
  buildAgents=$(grep BUILD_AGENTS $runSetFile | sed "s/.*: \"//" | sed "s/\"//" | head -1)
  testAgents=$(grep TEST_AGENTS $runSetFile | sed "s/.*: \"//" | sed "s/\"//" | head -1)
  otherParams=$(grep OTHER_PARAMS $runSetFile | sed "s/.*: \"//" | sed "s/\"//" | head -1)
  testScope=$(grep TEST_SCOPE $runSetFile | sed "s/.*: \"//" | sed "s/\"//" | head -1)
  reportProject=$(grep REPORT_PROJECT $runSetFile | sed "s/.*: //" | head -1)
  env=$(grep env $runSetFile )
  serviceCommand=$(grep SERVICE_COMMAND $runSetFile | sed "s/.*: \"//" | sed "s/\"//" | head -1)

  if [[ "${runSetDryRun}" != "" ]]; then
     echo Dry run -- nothing will be executed
     echo ""
  fi
  echo Running runset: $runSet, using agents: $testAgents
  echo Scope of tests: $testScope
  if [[ "$otherParams" != "" ]]; then echo Other parameters: $otherParams; fi
  echo ""
  if [[ "$serviceCommand" != "" ]]; then echo WARNING: The runset assumes the service command \"$serviceCommand\" has been run; fi
  if [[ "$env" != "" ]]; then
    echo WARNING: The runset has environment variables that this run will not use.
    echo ""
    read  -n 1 -p "Hit Ctrl-C to stop, any other key to continue..." warning
    echo ""
    echo ""

  fi

  if [[ "$runSetBuild" == "1" ]]; then
    ${runSetDryRun} ./manage ${runSetReBuild}build $buildAgents
  fi

  ${runSetDryRun} ./manage run $testAgents $otherParams $testScope
  exit 0
}

runTests() {
  runArgs=${@}

  if [[ "${TAGS}" ]]; then
      echo "Tags: ${TAGS}"
  else
      echo "No tags specified; all tests will be run."
  fi

  if [[ "${GITHUB_ACTIONS}" != "true" ]]; then
    mkdir -p .logs
    echo "" > .logs/request.log
  fi

  echo
  # Behave.ini file handling
  export BEHAVE_INI_TMP="$(pwd)/behave.ini.tmp"
  cp ${BEHAVE_INI} ${BEHAVE_INI_TMP}

  if [[ "${REPORT}" = "allure" && "${COMMAND}" != "dry-run" ]]; then
      echo "Executing tests with Allure Reports."
      ${terminalEmu} docker run ${INTERACTIVE} --rm --network="host" -v ${BEHAVE_INI_TMP}:/aries-test-harness/behave.ini -v "$(pwd)/aries-test-harness/allure/allure-results:/aries-test-harness/allure/allure-results/" $DOCKER_ENV aries-test-harness -k ${runArgs} -f allure_behave.formatter:AllureFormatter -o ./allure/allure-results -f progress -D Acme=http://0.0.0.0:9020 -D Bob=http://0.0.0.0:9030 -D Faber=http://0.0.0.0:9040 -D Mallory=http://0.0.0.0:9050
  elif [[ "${COMMAND}" = "dry-run" ]]; then
      ${terminalEmu} docker run ${INTERACTIVE} --rm --network="host" -v ${BEHAVE_INI_TMP}:/aries-test-harness/behave.ini $DOCKER_ENV aries-test-harness -k ${runArgs} -D Acme=http://0.0.0.0:9020 -D Bob=http://0.0.0.0:9030 -D Faber=http://0.0.0.0:9040 -D Mallory=http://0.0.0.0:9050 |\
        grep "Feature:\|Scenario Outline\|\@" | sed "/n(u/d"
  else
      ${terminalEmu} docker run ${INTERACTIVE} --rm --network="host" -v ${BEHAVE_INI_TMP}:/aries-test-harness/behave.ini -v "$(pwd)/.logs:/aries-test-harness/logs" $DOCKER_ENV aries-test-harness -k ${runArgs} -D Acme=http://0.0.0.0:9020 -D Bob=http://0.0.0.0:9030 -D Faber=http://0.0.0.0:9040 -D Mallory=http://0.0.0.0:9050
  fi
  local docker_result=$?
  rm ${BEHAVE_INI_TMP}

  # Export agent logs
  if [[ "${GITHUB_ACTIONS}" != "true" && ${COMMAND} != "dry-run" ]]; then
    echo ""
    echo "Exporting Agent logs."
    docker logs acme_agent > .logs/acme_agent.log
    docker logs bob_agent > .logs/bob_agent.log
    docker logs faber_agent > .logs/faber_agent.log
    docker logs mallory_agent > .logs/mallory_agent.log

    if [[ "${USE_NGROK}" = "true" ]]; then
      echo "Exporting ngrok Agent logs."
      docker logs acme_agent-ngrok > .logs/acme_agent-ngrok.log
      docker logs bob_agent-ngrok > .logs/bob_agent-ngrok.log
      docker logs faber_agent-ngrok > .logs/faber_agent-ngrok.log
      docker logs mallory_agent-ngrok > .logs/mallory_agent-ngrok.log
    fi
  fi

  return ${docker_result}
}

stopIfExists(){
  local CONTAINER_NAME
  CONTAINER_NAME=$1
  local CONTAINER_ID
  CONTAINER_ID=`docker ps -q --filter "name=${CONTAINER_NAME}"`

  if [[ ${CONTAINER_ID} ]]; then
    docker stop ${CONTAINER_ID} > /dev/null
  fi
}

stopHarness(){

  stop_option="all"
  if [[ -n $1 ]]; then
    stop_option=$1
  fi

  echo "Cleanup:"
  echo "  - Shutting down all the agents ..."
  docker stop acme_agent bob_agent faber_agent mallory_agent > /dev/null
  docker rm -v acme_agent bob_agent faber_agent mallory_agent > /dev/null

  stopIfExists acme_agent-ngrok
  stopIfExists bob_agent-ngrok
  stopIfExists faber_agent-ngrok
  stopIfExists mallory_agent-ngrok

  printf "Done\n"

  if [[ "${REPORT}" = "allure" ]]; then
    if [[ "${REPORT_ERROR_TYPE}" = "comparison" ]]; then
      # TODO run the same_as_yesterday.py script and capture the result
      echo "Checking results vs KGR ..."
      ${terminalEmu} docker run ${INTERACTIVE} --rm -v "$(pwd)/aries-test-harness/allure/allure-results:/aries-test-harness/allure/allure-results/" --entrypoint /aries-test-harness/allure/same_as_yesterday.sh -e PROJECT_ID=${PROJECT_ID} aries-test-harness
      docker_result=$?
    fi
  fi

  printf "StopServices: ${stop_option}\n"
  stopServices ${stop_option}

  stopIfExists agents-ngrok

  cleanupNetwork

  if [ -n "${docker_result}" ] && [ ! "${docker_result}" = "0" ]; then
    echo "Exit with error code ${docker_result}"
    exit ${docker_result}
  fi
}

isAgent() {
  result=false

  for agent in ${VALID_AGENTS}; do
    if [[ "${1}" == "${agent}" ]]; then
        result=true
    fi
  done

  echo $result
}

printLetsEncryptWarning() {
  [ -n "${LetsEncryptWarningPrinted}" ] && return
  cat << EOWARN
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
>> WARNING
>> This applies to mobile testing using Android-Based digital wallet,
>> as far as we know.

If you are using a mobile/smartphone-based Wallet, the test harness is going to
make use of the https://ngrok.com/ infrastructure, generating url like this one
https://aabbccdd.ngrok.io

The Ngrok infrastructure makes use of a wildcard TLS certificate *.ngrok.io,
certified by Let's Encrypt (https://letsencrypt.org/).
However, some OS and platform are still making use of an expired root
certificate, namely "DST Root CA X3", which expired on September 30th 2021.
Ref: https://letsencrypt.org/docs/dst-root-ca-x3-expiration-september-2021

If:
- The wallet your are testing somehow never manages to establish a
  connection after scanning the first QR code.
Then:
- you might be facing this issue.

The solution is to disable the expired certificate into your android device
trusted certificate store.

Here's how: Of course, your mileage might vary depending on brand and device:

* The simplest way is to launch your setting application
  a. Use the search bar to find "certificate"-related entries
     (you can probably use a shorter substring)
  b. This should display a few entries, including something like
    Trusted Certificates (or the equivalent in your phone language)
  c. Selecting this should display two list of trusted certificates:
    the System ones and the ones input by the user
  d. Go to the System list of trusted certificates, and simply find the
    DST Root CA X3 in the sorted list
  e. Click on the certificate and deactivate it.

* If the search does not work for you, we are aware of two alternate ways
  to access the trusted certificates store, but again we cannot document for
  all brand/models

  * Either:
    Settings
    => Biometrics & security
    => Other security settings
    => View security certificates
  * Or:
    Settings
    => Security
    => Advanced
    => Encryption and Credentials
    => Trusted Certificates
  * Then go to step b. above to disable the faulty certificate.

Now, if the faulty certificate is not is your trust store, then you have
another issue, sorry.
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
EOWARN
LetsEncryptWarningPrinted=1
}
