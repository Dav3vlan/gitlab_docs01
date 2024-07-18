# How to Create a Merge Request in GitLab Image Repository for Installing a New Tool

## Step 1: Create a Branch

1. **Navigate to the Repository**: Open your GitLab project and navigate to the `image-tools` repository.
2. **Create a New Branch**:
   - Click on the **Repository** tab in the left sidebar.
   - Select **Branches**.
   - Click on **New branch**.
   - Enter a branch name, for example, `add-new-tool`.
   - Click **Create branch**.

Alternatively, you can use the Git CLI to create a branch:
```bash
git checkout -b add-new-tool
```

## Step 2: Edit the Dockerfile

1. **Open the Dockerfile**:
   - Navigate to the `Dockerfile` in the repository.
   - Click on the **Edit** button.

2. **Add the New Tool**:
   - Edit the `Dockerfile` to include the installation commands for your new tool. Here's an example snippet to add your tool:
     ```dockerfile
     # INSTALL new-tool
     RUN yum install -y new-tool
     ```

3. **Save Changes**:
   - Once you’ve made the necessary changes, click on **Commit changes**.
   - Add a commit message, such as `Added new-tool installation`.
   - Ensure **Commit to new branch** is selected and the correct branch is chosen (e.g., `add-new-tool`).
   - Click **Commit changes**.

Alternatively, you can use the Git CLI to commit your changes:
```bash
git add Dockerfile
git commit -m "Added new-tool installation"
git push origin add-new-tool
```

## Step 3: Verify the Build

1. **Pipeline Trigger**:
   - Once the changes are committed, a new build pipeline should automatically start. Navigate to the **CI/CD** tab in the left sidebar and select **Pipelines**.
   - Find the pipeline associated with your branch and monitor its status.

2. **Check Pipeline Logs**:
   - Click on the pipeline ID to view the detailed logs.
   - Ensure that the build stage completes successfully and that the new tool is installed without errors.

## Step 4: Submit a Merge Request

1. **Open a Merge Request**:
   - Navigate to the **Merge Requests** tab in the left sidebar.
   - Click on **New merge request**.
   - Select the source branch (`add-new-tool`) and the target branch (e.g., `main`).
   - Click on **Compare branches and continue**.

2. **Fill in Merge Request Details**:
   - Enter a title for your merge request, such as `Add new-tool to Dockerfile`.
   - Provide a description detailing the changes you made and why they are necessary.
   - Assign reviewers if required and set labels if applicable.

3. **Submit the Merge Request**:
   - Click on **Create merge request**.

Alternatively, you can use the Git CLI to create a merge request:
```bash
gitlab merge-request create --source-branch add-new-tool --target-branch main --title "Add new-tool to Dockerfile" --description "Added new-tool installation"
```

## Step 5: Verify and Merge

1. **Review Process**:
   - Wait for the reviewers to approve the changes. They may leave comments or request changes.

2. **Merge the Request**:
   - Once approved, navigate back to the **Merge Requests** tab.
   - Find your merge request and click on it.
   - Click on **Merge** to integrate the changes into the target branch.

Alternatively, you can use the Git CLI to merge the request:
```bash
gitlab merge-request merge --merge-request-id <id>
```
Replace `<id>` with the actual merge request ID.

This guide provides a step-by-step process for opening a Merge Request in the GitLab image repository, including editing the Dockerfile, verifying the build, and submitting the MR using both the web interface and the CLI.
```
