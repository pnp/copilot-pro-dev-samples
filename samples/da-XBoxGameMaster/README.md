# XBOX Game Master

## Summary

This sample is a declarative agent that is a master of XBOX games. Using the live XBOX gaming web site, it is able to answer questions, make recommendations, and even create graphics in the style of XBOX games.

![picture of the app recommending games](./assets/XBOX%20Game%20Master%202.png)
![picture of the app generating a simulated game image](./assets/XBOX%20Game%20Master%201.png)

## Frameworks

![No frameworks](https://img.shields.io/badge/nothing-1.00-green)

This app requires no tooling and can be developed using utilities that are built into any modern operating system such as a text editor, a web browser, and the ability to create a Zip archive file.

## Prerequisites

* [Office 365 tenant](https://dev.office.com/sharepoint/docs/spfx/set-up-your-development-environment) with permission to upload or install Teams applications
* [Microsoft 365 Copilot](https://www.microsoft.com/microsoft-365/copilot#plans)
* Any modern computer using Windows, MacOS, or Linux

## Version history

Version|Date|Author|Comments
-------|----|----|--------
1.0|January 9, 2025|Bob German|Initial release

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

---

## Minimal Path to Awesome

* Clone or download this repository
* Navigate to this sample's **appPackage** folder on your computer
* (Optional: View or modify the files in the **appPackage** folder)
* Create a Zip file containing the contents of the **appPackage** folder at the root
* In Microsoft Teams click "Apps" 1️⃣ , "Manage yor apps"2️⃣ , "Upload an app" 3️⃣ , and then Upload a custom app 4️⃣ . Upload the zip file and follow the prompts to use your new agent in Copilot.

![Uploading a Teams application](./assets/Upload%20Teams%20app.png)

NOTE: If you want to make a second app, just copy and edit the files however **be sure to generate a new "id" value in manifest.json**. This can be any Globally Unique ID (GUID) as long as it's unique; you can generate one using the [online GUID generator](https://guidgenerator.com/)

## Features

This declarative agent includes:

* Ability to answer questions and make recommendations about XBOX games
* Grounded in the online XBOX game catalog at https://www.xbox.com
* Able to generate images based on XBOX games
* Shows how to use the `WebSearch` and `GraphicArt` capabilities for declarative agents

<img src="https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/samples/da-xbox-game-master" />