@Library('ottopia')_

pipeline {
    agent none

    options {
        timestamps()
        skipDefaultCheckout()
        copyArtifactPermission('vehicle_docker_aarch64')
    }

    parameters {
        booleanParam(name: 'WITH_SSH', defaultValue: false, description: 'Do you want SSH?')
    }

    environment {
        REPO_NAME = 'msquic'
        TARGET_ARCH = 'aarch64'
        TARGET_SYSTEM = 'aarch64_ubuntu_focal'
    }

    stages {
        stage('Build And Publish') {
            matrix {
                agent { label 'arm64_ubuntu20.04_v2_small' }
                axes {
                    axis {
                        name 'BUILD_TYPE'
                        values 'Release'
                    }
                }
                options {
                    timeout(time: params.WITH_SSH ? 120 : 60, unit: 'MINUTES')
                }
                stages {
                    stage('Prepare') {
                        steps {
                            deleteDir()
                            publishChecks(name: "${TARGET_SYSTEM}-${BUILD_TYPE}", status: 'IN_PROGRESS', text: 'Build is in progress')
                            gitClone(branchName: BRANCH_NAME, repoName: REPO_NAME, submodule: true)
                        }
                    }
                    stage('Conan Connect') {
                        steps {
                            conanRemoteConnect()
                        }
                    }
                    stage('Install Build Deps') {
                        steps {
                            sh(
                                label: 'apt deps',
                                script: 'apt-get install -y --no-install-recommends ninja-build liblttng-ust-dev || true'
                            )
                        }
                    }
                    stage('Build') {
                        steps {
                            sh(
                                label: 'cmake configure + build',
                                script: """
                                    cmake -B build -G Ninja \
                                        -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
                                        -DQUIC_BUILD_TEST=OFF \
                                        -DQUIC_BUILD_TOOLS=OFF \
                                        -DQUIC_ENABLE_LOGGING=OFF
                                    cmake --build build --parallel
                                """
                            )
                        }
                    }
                    stage('Package') {
                        steps {
                            sh(
                                label: 'conan export-pkg',
                                script: "conan export-pkg . -s build_type=${BUILD_TYPE}"
                            )
                        }
                    }
                    stage('Publish') {
                        steps {
                            conanPublish(buildType: BUILD_TYPE, platform: TARGET_ARCH, repoName: REPO_NAME, targetBranch: BRANCH_NAME)
                        }
                    }
                }
                post {
                    success {
                        publishChecks(name: "${TARGET_SYSTEM}-${BUILD_TYPE}", text: 'Build succeeded')
                    }
                    failure {
                        publishChecks(conclusion: 'FAILURE', name: "${TARGET_SYSTEM}-${BUILD_TYPE}", text: 'Build failed')
                    }
                    aborted {
                        publishChecks(conclusion: 'CANCELED', name: "${TARGET_SYSTEM}-${BUILD_TYPE}", text: 'Build cancelled')
                    }
                    always {
                        script {
                            if (params.WITH_SSH) {
                                enableSSH(timeout: 3600)
                            }
                        }
                    }
                }
            }
            post {
                failure {
                    failureInfraFunc(repo_name: REPO_NAME, branch_name: BRANCH_NAME, build_number: BUILD_NUMBER)
                }
            }
        }
    }
}
