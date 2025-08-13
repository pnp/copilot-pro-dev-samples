# Declarative Agent - PnP Assistant

## Summary

This declarative agent is designed to assist users in finding more information about the PnP reusable React controls. It provides a user-friendly interface for users to ask questions and receive relevant answers based on the information available in the PnP documentation.

PnP Assistant helping user to find information about a specific control:
![PnP Assistant - help with control](<assets/PnP Assistant - help with control.gif>)

PnP Assistant helping user to find information about a specific control's properties:
![PnP Assistant - control properties](<assets/PnP Assistant - control properties.gif>)

PnP Assistant helping user to find a control that matches a specific requirement:
![PnP Assistant - suggest control](<assets/PnP Assistant - suggest control.gif>)

## Contributors

* [Guido Zambarda](https://github.com/GuidoZam) - M365 Development MVP

## Version history

Version|Date|Comments
-------|----|--------
1.0 | May 18, 2025 | Initial release

> **Prerequisites**
>
> To run this app template from your local dev machine, you will need:
>
> * A [Microsoft 365 account for development](https://docs.microsoft.com/microsoftteams/platform/toolkit/accounts).
> * [Teams Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) version 5.0.0 and higher or [Teams Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
> * [Microsoft 365 Copilot license](https://learn.microsoft.com/microsoft-365-copilot/extensibility/prerequisites#prerequisites)

## Minimal path to awesome

1. Clone this repository (or [download solution as .ZIP file](https://pnp.github.io/download-partial/?url=https://github.com/pnp/copilot-pro-dev-samples/tree/main/samples/da-pnpassistant))

2. Rename the `.env.dev.example` file to `.env.dev` and update the following values:

    ```bash
    # Built-in environment variables
    TEAMSFX_ENV=" dev"
    APP_NAME_SUFFIX=" dev"

    TEAMS_APP_ID=aad90fc0-dbbc-42e2-b9c1-f30b8cc3894d
    TEAMS_APP_TENANT_ID=<tenant_id>
    M365_TITLE_ID=
    M365_APP_ID=
    ```

3. From the VSCode Teams Toolkit sign-in to your Microsoft 365 account.
4. From the VSCode Teams Toolkit provision the solution to create the Teams app.
5. Go to [https://www.office.com/chat?auth=2](https://www.office.com/chat?auth=2) URL and select the agent.
6. Use one of the conversation starters to start trying the agent.

## Features

This sample demonstrates the following concepts:

* Build a declarative agent that uses one or multiple sites as knowledge base.
* Answer questions about the PnP reusable React controls and PnP reusable property controls.

<!--
RESERVED FOR REPO MAINTAINERS

We'll add the video from the community call recording here

## Video

[![YouTube video title](./assets/video-thumbnail.jpg)](https://www.youtube.com/watch?v=XXXXX "YouTube video title")
-->

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20da-pnpassistant%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/SamplesGallery/da-pnpassistant)