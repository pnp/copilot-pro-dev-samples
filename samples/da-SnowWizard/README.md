# CopilotSnowWizard

This project demonstrates a sample implementation of an M365 Declarative Copilot that interfaces with ServiceNow to list and create incidents.

**Note:** This is sample code and should not be used in production without thorough review. It is designed to illustrate how to build a simple Declarative Copilot using Visual Studio Code and the Teams Toolkit.



| ![CopilotSnowWizard Screenshot 1](images/2024-10-11_16-29.png) | ![CopilotSnowWizard Screenshot 1](images/2024-10-11_16-39.png) | ![CopilotSnowWizard Screenshot 1](images/2024-10-11_16-40.png) |
|:-------------------------------------------------------------:|:-------------------------------------------------------------:|:-------------------------------------------------------------:|


## Preparing your Development Environment

In order to run the code, you will need an M365 tenant with Copilot licenses enabled. Additionally, you must enable a policy to sideload custom applications. Without this, you will not be able to run the code. These instructions assume you have admin rights on the tenant. If you do not have admin rights, please work with your administrator to allow the upload of custom applications.

### Enable Teams custom application uploads

By default, end users can't upload applications directly; an Administrator needs to upload them into the enterprise app catalog. Follow these steps to enable direct uploads via Teams Toolkit:

1. Navigate to the [Microsoft 365 Admin Center](https://admin.microsoft.com/).

2. In the left panel, select **Show all** to expand the navigation menu. Then, select **Teams** to open the Microsoft Teams admin center.

3. In the Teams admin center, expand the **Teams apps** section and select **Setup policies**. You will see a list of App setup policies. Select the **Global (Org-wide default)** policy.

4. Ensure the **Upload custom apps** switch is turned **On**.

5. Scroll down and select the **Save** button to apply your changes.

Next, you need to install the following software on your computer to use the sample code:

1. [Visual Studio Code](https://code.visualstudio.com/download)
2. [Node.js](https://nodejs.org/en/download/)
3. [Teams Toolkit](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension)

## Creating the ServiceNow Personal Developer Instance

To use the sample code provided, you will need a ServiceNow Personal Developer Instance (PDI). Follow the instructions below to create your instance and familiarize yourself with the basics of ServiceNow:

1. **Sign in to the [ServiceNow Developer Site](https://developer.servicenow.com/dev.do).**
2. In the header, click the **Request Instance** button.
3. Select a ServiceNow release for your instance.
4. Click the **Request** button.
5. When your instance is ready, a dialog will provide the URL and admin login details. Copy the current password to a safe location for future use.
6. Click the **Open Instance** button to open your instance in a new browser tab.

To open your instance later, sign in to the Developer Site, open the Account menu, and click the **Start Building** button.

ServiceNow offers free PDIs to registered users who want to develop applications or improve their skills on the ServiceNow platform. New Developer Program members automatically receive a PDI running the latest release, which remains active as long as there is activity on the instance.

It is strongly recommended to acquire basic knowledge of ServiceNow concepts. This will help you understand how M365 Copilot interfaces with ServiceNow. You can follow a basic learning path at [New to ServiceNow | ServiceNow Developers](https://developer.servicenow.com/dev.do#!/learn/learning-plans/washingtondc/new_to_servicenow/).

For more detailed instructions and learning resources, visit [ServiceNow Basics Objectives | ServiceNow Developers](https://developer.servicenow.com/dev.do#!/learn/learning-plans/washingtondc/new_to_servicenow/app_store_learnv2_buildmyfirstapp_washingtondc_servicenow_basics_objectives).

## Download the Sample Code from GitHub

If you are familiar with Git, you can clone this repository and open the `SnowWizard` folder in Visual Studio Code. If not, you can download a ZIP file containing all the content by clicking the green "Code" button at the top right corner of the repository page.

If you download the ZIP file, uncompress it on your PC and use Visual Studio Code to open the `SnowWizard` folder.

## Configuring the Declarative Copilot 

Once you downloaded the code and opened in with Visual Studio Code you will need to create a configuration file and provide some config information in order to make the declarative agent to interface with your ServiceNow development instance.

On Visual Studio Code, create a file named .env.local.user inside the env folder. 

# ServiceNow Configuration

Create a `.env.local.user` file inside the `env` folder with the following content:

```
SN_INSTANCE='devxxxxxx'
SN_USERNAME='user'
SN_PASSWORD='user_password'
```

**Note:**
- The `SN_INSTANCE` value should be the initial part of your ServiceNow development instance URL.
- This sample code uses user credentials to interface with ServiceNow. Ensure the user has the necessary permissions to list and create incidents in ServiceNow.
- Store your credentials securely and avoid sharing them publicly.

## Install the Node.js requisites

Open a Command Prompt and navigate to the SnowWizard folder. Run NPM INSTALL and wait until all the libraries and requirements get installed.

## Run the Declarative Agent

Now on Visual Studio, click on the Teams Toolkit icon on the left rail and sign-in with your M365 tenant credentials. You do that on the Accounts section by providing your M365 tenant credentials.

Now click Preview Your Teams App (F5) and enjoy.

## Sample Prompts

```
List all ServiceNow incidents
Create a table with all ServiceNow open incidents 
Create a ServiceNow incident with jokes as short and full descriptions
Create a ServiceNow incident based on the content of the text below. <provide a text describing a problem>
```

Please note that the code is limiting the return from the ServiceNow interface in just 10 incidents. That can be easily changed by adjusting the limit on the service interface implemented by snow_incidents.ts.
