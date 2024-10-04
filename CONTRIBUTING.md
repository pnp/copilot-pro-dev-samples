# Contribution Guidance

This is a community repository for sample Microsoft 365 Copilot agents developed using code-first approaches using tools such as Visual Studio Code and Teasm Toolkit. 

If you'd like to contribute to this repository, please read the following guidelines. Contributors are more than welcome to share their learnings with others in this centralized location.

## Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information, see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

Remember that this repository is maintained by community members who volunteer their time to help. Be courteous and patient.

## Question or Problem?

Please do not open GitHub issues for general support questions as the GitHub list should be used for feature requests and bug reports. This way we can more easily track actual issues or bugs from the code and keep the general discussion separate from the actual code.

## Typos, Issues, Bugs and contributions

Whenever you are submitting any changes to repositories in the PnP organization, please follow these recommendations.

* Always fork the repository to your own account before making your modifications
* Do not combine multiple changes to one pull request. For example, submit any samples and documentation updates using separate PRs
* If your pull request shows merge conflicts, make sure to update your local main to be a mirror of what's in the main repo before making your modifications
* If you are submitting multiple samples, please create a specific PR for each of them
* If you are submitting typo or documentation fix, you can combine modifications to single PR where suitable

## Sample Naming and Structure Guidelines

When you submit a new sample, please follow these guidelines:

* Each sample must be placed in a folder under the `samples` folder
* Your sample folder must include the following content:
  * Your solution's source code
  * An `assets` folder, containing screenshots
  * A `README.md` file
* You must only submit samples for which you have the rights to share. Make sure that you asked for permission from your employer and/or clients before committing the code to an open-source repository, because once you submit a pull request, the information is public and _cannot be removed_.

### Sample Folder

* When submitting a new sample solution, please name the sample solution folder accordingly
* Do not use period/dot in the folder name of the provided sample

### README.md

* You will need to have a `README.md` file for your contribution, which is based on [the provided template](templates/README-template.md) under the `samples` folder. Please copy this template to your project and update it accordingly. Your `README.md` must be named exactly `README.md` -- with capital letters -- as this is the information we use to make your sample public.
* You will need to have a screenshot picture of your sample in action in the `README.md` file ("pics or it didn't happen"). The preview image must be located in the `assets` folder in the root of your sample folder.
  * All screen shots must be located in the `assets` folder. Do not point to your own repository or any other external source
* The README template contains a specific tracking image at the end of the file with an `img` element pointing to `https://m365-visitor-stats.azurewebsites.net/SamplesGallery/pnp-copilot-pro-dev-your-sample`. This is a transparent image which is used to track how many visits each sample receives in GitHub.
* Update the image `src` attribute according with the repository name and folder information. For example, if your sample is named `my-agent` in the `samples` folder, you should update the `src` attribute to `https://m365-visitor-stats.azurewebsites.net/SamplesGallery/pnp-copilot-pro-dev-my-agent`
  * Update the image `src` attribute according with the repository name and folder information.
* If you find an existing sample which is similar to yours, please extend the existing one rather than submitting a new similar sample
  * When you update existing samples, please update also `README.md` file accordingly with information on provided changes and with your author details
* Make sure to document each function in the `README.md`
* If you include your social media information under **Authors** in the **Solution** section, we'll use this information to promote your contribution on social media, blog posts, and community calls.
    * Try to use the following syntax:
    ```md
    folder name | Author Name ([@yourtwitterhandle](https://twitter.com/yourtwitterhandle))
    ```
* If you include your company name after your name, we'll try to include your company name in blog posts and community calls.
    * Try to use the following syntax:
    ```md
    folder name | Author Name ([@yourtwitterhandle](https://twitter.com/yourtwitterhandle)), Company Name
    ```
* For multiple authors, please provide one line per author
* If you prefer to not use social media or disclose your name, we'll still accept your sample, but we'll assume that you don't want us to promote your contribution on social media.

### Assets

* To help people understand your sample, make sure to always include at least one screenshot of your solution in action. People are more likely to click on a sample if they can preview it before installing it.
* Please provide a high-quality screenshot
* If possible, use a resolution of **1920x1080**
* You can add as many screen shots as you'd like to help users understand your sample without having to download it and install it.
* You can include animated images (such as `.gif` files), but you must provide at least one static `.png` file

## Sample naming and  file structure

New sample submissions must follow these naming and structure guidelines:

### 1. Folder

Each sample should be in its own folder within the /samples directory. Your folder name should include a prefix depending on the type of sample, as follows:

| Prefix | Description |
| --- | --- |
| cea- | These are Custom engine agents that interact with users in the Bizchat chat surface via the Azure Bot Framework |
| da - | These are Declarative agents that run using Microsoft 365 Copilot's AI and orchestration and may include API plugins and Graph connectors |
| msgext- | These are agents implemented as Microsoft 365 Message extensions |

### 2. README.md file

Your sample folder should contain a `README.md` file for your contribution. Please base your `README.md` file on one of the following templates:

| If your sample is | use this template |
| --- | --- |
| built with Teams Toolkit for VS Code | [README.md](/samples/_SAMPLE_templates/ttk-vs-code-sample/README.md) |
| built with Teams Toolkit for Visual Studio | [README.md](/samples/_SAMPLE_templates/ttk-vs-sample/README.md) |
| something else | [README.md](/samples/_SAMPLE_templates/any-sample/README.md) |

Please copy the template to your project and update it accordingly. Your `README.md` must be named exactly `README.md` -- with capital letters -- as this is the information we use to make your sample public.

Each README.md file must contain detailed build and use instructions.

### 3. .gitignore

The [.gitignore](https://git-scm.com/docs/gitignore) file controls which files are ignored, to prevent checking in files that are part of packages and other files generated at build time.

Since the samples are built with a variety of toolchains, it is not possible to have a global .gitignore file that will work with all of them. So please be sure to include a .gitignore file in your sample folder that will ignore anything that will be downloaded or created locally when building  your solution.

| If your sample is | sample gitignore |
| --- | --- |
| built with Teams Toolkit | no sample needed - file is generated by Teams Toolkit |
| a Web service based on .NET | [.gitignore](/samples/_SAMPLE_templates/dotnet-sample/.gitignore) |
| a Web service based on nodeJS | [.gitignore](/samples/_SAMPLE_templates/node-sample/.gitignore) |
| something else | You may find [these samples](https://github.com/github/gitignore) to be helpful |

This is also a good time to check to make sure you have removed any secrets or tenant-specific settings from your sample such as application IDs and secrets.

### 4. Handling environment variables

Environment variables are often stored in files such as **.env**, **.env.local**, or **appSettings.json**. If they aren't already, consider adding these files to your .gitignore and providing sample files instead.

> Special note for projects using [Teams Toolkit for Visual Studio Code](https://aka.ms/teams-toolkit): The .gitignore file generated by Teams Toolkit does not exclude the dev environment file (**env\.env.dev**) to facilitate sharing dev settings among a team. For your sample please  make sure you don't check your tenant-specific settings in, and be aware they may have been put there during provisioning by Teams Toolkit. Feel free to add this file to .gitignore.

It's a good idea to provide sample files so people know what's required to run your solution. For example you might provide an **.env.local.sample** file like this:

```text
# Generated during provision
BOT_ID=
TEAMS_APP_ID=
BOT_DOMAIN=
BOT_ENDPOINT=

# Set by the developer
OPENAI_API_ENDPOINT=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=text-davinci-03
```
and **.env.local.user.sample** like this:

```text
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The instructions would tell developers to copy the **.env.local.sample** to a new file **.env.local**, and to also copy **.env.local.user.sample** to **.env.local.user**, and then to fill in certain values.

Notice that:

 * Values generated by Teams Toolkit, such as BOT_ID, are blank. Teams Toolkit will generate new values and fill them in during provisioning.
 * Values that are likely to work for all developers are filled in, and
 * Values to be provided manually by each developer are shown with the details removed to convey the format while not revealing the sample author's personal settings.

### 5. Screen shot

You will need to have a screenshot picture of your sample in action in the `README.md` file ("pics or it didn't happen"). This is manditory since we've found that users tend not to try samples that lack a screen shot. Please use a standard format such as .png, .jpg, or .gif for your screen shot so it will work in various places, such as in the [sample browser](https://adoption.microsoft.com/en-us/sample-solution-gallery/){target=_blank}. Animated .png or .gif files are welcome.

The preview image must be located in the `/assets/` folder in the root your solution. Even if it's a simple bot sending a single chat message, please include a screen shot!

### 6. M365 App manifest

Your sample should include a clearly marked folder containing a Teams/M365 `manifest.json` file and well-formed application icons along with any additional files such as declarative agent and API plugin JSON files.

 * If the manifest works as-is, you may optionally include an installable Teams application package (zip archive containing these files).

 * If the `manifest.json` requires modification before use, please do not include a zip archive. Instead, include instructions in your `README.md` file explaining how to modify the manifest and create the Teams application package

### 7. Telemetry

Each `README` template contains a specific tracking image at the bottom of the file with an `img` tag, where the `src` attribute points to `https://m365-visitor-stats.azurewebsites.net/teams-dev-samples/samples/xxx`. This is a transparent image which is used to track viewership of individual samples in GitHub. We only count the number of times each page is accessed, and capture no personal information or correlation with other pages.

Please update the image `src` attribute according with the repository name and folder information. For example, if your sample is named `bot-todo` in the `samples` folder, you should update the `src` attribute to `https://m365-visitor-stats.azurewebsites.net/sp-dev-fx-webparts/samples/bot-todo`.


## Submitting Pull Requests

> If you aren't familiar with how to contribute to open-source repositories using GitHub, or if you find the instructions on this page confusing, [sign up](https://forms.office.com/Pages/ResponsePage.aspx?id=KtIy2vgLW0SOgZbwvQuRaXDXyCl9DkBHq4A2OG7uLpdUREZVRDVYUUJLT1VNRDM4SjhGMlpUNzBORy4u) for one of our [Sharing is Caring](https://pnp.github.io/sharing-is-caring/#pnp-sic-events) events. It's completely free, and we'll guide you through the process.

Here's a high-level process for submitting new samples or updates to existing ones.

1. Sign the Contributor License Agreement (see below)
2. Fork this repository [pnp/copilot-pro-dev-samples](https://github.com/pnp/copilot-pro-dev-samples) to your GitHub account
3. Create a new branch from the `main` branch for your fork for the contribution
4. Include your changes to your branch
5. Commit your changes using descriptive commit message. These are used to track changes on the repositories for monthly communications
6. Create a pull request in your own fork and target the `main` branch
7. Fill up the provided PR template with the requested details

Before you submit your pull request consider the following guidelines:

* Search [GitHub](https://github.com/pnp/copilot-pro-dev-samples/pulls) for an open or closed Pull Request which relates to your submission. You don't want to duplicate effort.
* Make sure you have a link in your local cloned fork to the [pnp/copilot-pro-dev-samples](https://github.com/pnp/copilot-pro-dev-samples):

  ```shell
  # check if you have a remote pointing to the Microsoft repo:
  git remote -v

  # if you see a pair of remotes (fetch & pull) that point to https://github.com/pnp/copilot-pro-dev-samples, you're ok... otherwise you need to add one

  # add a new remote named "upstream" and point to the Microsoft repo
  git remote add upstream https://github.com/pnp/copilot-pro-dev-samples.git
  ```

* Make your changes in a new git branch:

  ```shell
  git checkout -b my-agent main
  ```

* Ensure your fork is updated and not behind the upstream **copilot-pro-dev-samples** repo. Refer to these resources for more information on syncing your repo:
  * [GitHub Help: Syncing a Fork](https://help.github.com/articles/syncing-a-fork/)
  * [Keep Your Forked Git Repo Updated with Changes from the Original Upstream Repo](http://www.andrewconnell.com/blog/keep-your-forked-git-repo-updated-with-changes-from-the-original-upstream-repo)
  * For a quick cheat sheet:

    ```shell
    # assuming you are in the folder of your locally cloned fork....
    git checkout main

    # assuming you have a remote named `upstream` pointing official **copilot-pro-dev-samples** repo
    git fetch upstream

    # update your local main to be a mirror of what's in the main repo
    git pull --rebase upstream main

    # switch to your branch where you are working, say "my-agent"
    git checkout my-agent

    # update your branch to update it's fork point to the current tip of main & put your changes on top of it
    git rebase main
    ```

* Push your branch to GitHub:

  ```shell
  git push origin my-agent
  ```

## Merging your Existing GitHub Projects with this Repository

If the sample you wish to contribute is stored in your own GitHub repository, you can use the following steps to merge it with this repository:

* Fork the `copilot-pro-dev-samples` repository from GitHub
* Create a local git repository

    ```shell
    md copilot-pro-dev-samples
    cd copilot-pro-dev-samples
    git init
    ```

* Pull your forked copy of `copilot-pro-dev-samples` into your local repository

    ```shell
    git remote add origin https://github.com/yourgitaccount/copilot-pro-dev-samples.git
    git pull origin main
    ```

* Pull your other project from GitHub into the `samples` folder of your local copy of `copilot-pro-dev-samples`

    ```shell
    git subtree add --prefix=samples/projectname https://github.com/yourgitaccount/projectname.git main
    ```

* Push the changes up to your forked repository

    ```shell
    git push origin main
    ```

## Signing the CLA

Before we can accept your pull requests you will be asked to sign electronically Contributor License Agreement (CLA), which is a pre-requisite for any contributions all PnP repositories. This will be one-time process, so for any future contributions you will not be asked to re-sign anything. After the CLA has been signed, our PnP core team members will have a look at your submission for a final verification of the submission. Please do not delete your development branch until the submission has been closed.

You can find Microsoft CLA from the following address - [https://cla.microsoft.com](https://cla.microsoft.com/).

Thank you for your contribution.

> Sharing is caring.

![](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/CONTRIBUTING.md)
