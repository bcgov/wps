pipeline {
    agent none
    environment {
        MODULE_NAME = "<%= name%>"
        BUILD_TRIGGER_EXCLUDES = "^.jenkins/"
    }
    options {
        disableResume()
    }
    stages {
        stage('Build') {
            agent { label 'build' }
            steps {
                script {
                    // only continue build if changes are relevant to this module.
                    // WARNING: it only checks the last commit!!!
                    def filesInThisCommitAsString = sh(script:"git diff --name-only HEAD~1..HEAD | grep -v '$BUILD_TRIGGER_EXCLUDES' || echo -n ''", returnStatus: false, returnStdout: true).trim()
                    def hasChangesInPath = (filesInThisCommitAsString.length() > 0)
                    echo "${filesInThisCommitAsString}"
                    if (!currentBuild.rawBuild.getCauses()[0].toString().contains('UserIdCause') && !hasChangesInPath){
                        currentBuild.rawBuild.delete()
                        error("No changes detected in the module path for ${MODULE_NAME} (${BUILD_TRIGGER_EXCLUDES})")
                    }
                }
                echo "Aborting all running jobs for ${MODULE_NAME}"
                script {
                    abortAllPreviousBuildInProgress(currentBuild)
                }
                echo "Building ..."
                sh "curl -X POST -H \"Content-Type: application/json\" https://chat.pathfinder.gov.bc.ca/hooks/7A8RwSpZPDAqc6uXS/z8nRXX43oifYWELkwJKeLj4e86rtyfvtJdqdvjSE3XoK2sri -d '{\"text\":\"Building wps-web for PR-${CHANGE_ID}.\"}'"
                sh "cd .pipeline && chmod +x npmw && ./npmw ci DEBUG='*' && ./npmw run build -- --pr=${CHANGE_ID} --git.branch.name=${CHANGE_BRANCH} --git.branch.merge=${CHANGE_BRANCH} --git.branch.remote=${CHANGE_BRANCH} --git.url=${GIT_URL} --git.change.target=${CHANGE_TARGET}"
            }
        }
        stage('Deploy (DEV)') {
            agent { label 'deploy' }
            steps {
                echo "Deploying ..."
                sh "cd .pipeline && chmod +x npmw && ./npmw ci && ./npmw run deploy -- --pr=${CHANGE_ID} --env=dev --git.branch.name=${CHANGE_BRANCH} --git.branch.merge=${CHANGE_BRANCH} --git.branch.remote=${CHANGE_BRANCH} --git.url=${GIT_URL} --git.change.target=${CHANGE_TARGET}"
            }
        }
        stage('Deploy (PROD)') {
            agent { label 'deploy' }
            when {
                expression { return env.CHANGE_TARGET == 'master';}
                beforeInput true
            }
            input {
                message "Should we continue with deployment to PROD?"
                ok "Yes!"
            }
            steps {
                echo "Deploying ..."
                sh "cd .pipeline && chmod +x npmw && ./npmw ci && ./npmw run deploy -- --pr=${CHANGE_ID} --env=prod --git.branch.name=${CHANGE_BRANCH} --git.branch.merge=${CHANGE_BRANCH} --git.branch.remote=${CHANGE_BRANCH} --git.url=${GIT_URL} --git.change.target=${CHANGE_TARGET}"
                sh "curl -X POST -H \"Content-Type: application/json\" https://chat.pathfinder.gov.bc.ca/hooks/7A8RwSpZPDAqc6uXS/z8nRXX43oifYWELkwJKeLj4e86rtyfvtJdqdvjSE3XoK2sri -d '{\"text\":\"Deployed wps-web to PROD for PR-${CHANGE_ID}.\"}'"
            }
        }
    }
}
