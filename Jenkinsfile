pipeline {
    agent any
    
    stages {
        stage('Check Disk Space') {
            steps {
                sh '''
                    df -h /
                    FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
                    if (( $(echo "$FREE_SPACE < 10" | bc -l) )); then
                        echo "Insufficient disk space. At least 10GB required."
                        exit 1
                    fi
                '''
            }
        }
        
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh '''
                    # Create and activate virtual environment
                    python3 -m venv ${VENV_NAME}
                    . ${VENV_NAME}/bin/activate

                    # Upgrade pip and install dependencies
                    python -m pip install --upgrade pip
                    
                    # Install numpy first (as per requirements.txt)
                    pip install numpy==1.24.3
                    
                    # Install project dependencies
                    pip install -r requirements.txt
                    
                    # Install test dependencies
                    pip install flake8 pytest
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . ${VENV_NAME}/bin/activate
                    
                    # Run flake8 checks (using same settings as in test_ci_local.ps1)
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . ${VENV_NAME}/bin/activate
                    
                    # Run tests excluding huggingface tests
                    python -m pytest tests/ -v -m "not huggingface"
                '''
            }
        }
    }

    post {
        always {
            // Clean up workspace
            cleanWs()
        }
        success {
            echo 'Build and tests completed successfully!'
        }
        failure {
            echo 'Build or tests failed!'
        }
    }
}
