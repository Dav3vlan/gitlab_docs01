stages:
  - test

test_job:
  stage: test
  script:
    - echo "Running tests..."
    - ./run_tests.sh
  after_script:
    - if [ "$CI_JOB_STATUS" == "success" ]; then echo "Tests passed" | mail -s "CI Passed" your-email@example.com; else echo "Tests failed" | mail -s "CI Failed" your-email@example.com; fi
