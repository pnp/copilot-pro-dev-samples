<!--
This template is for Copilot Studio samples only. Please update mcs-BlogPostHelper to the folder of this agent. Please delete this line before submission.
-->

# Blog Post Helper for Copilot Studio

## Summary

This sample helps users that often create blog post to help with elements of the creation process to get posts created quicker using capabilities within Declarative Agents.

Common features that the agent can help with:

 - Suggest an introduction based on a topic 
 - Review existing articles, or Find content that I would reference quickly.

> Note: This agent is built with Copilot Studio, as an equivelant variation of ```da-BlogPostHelper``` sample and and advising example of how to import a Copilot Studio agent

## Contributors

* [Paul Bullock](https://github.com/pkbullock.png)

## Version history

Version|Date|Comments
-------|----|--------
1.0|Feburary 01, 2026|Initial release

## Prerequisites

* Microsoft 365 tenant with Microsoft 365 Copilot
* Access to Copilot Studio

## Minimal path to awesome

**Import Solution into Copilot Studio**

This sample uses the Power Platform CLI to import samples, for documenation and installation instructions please visit: [What is Microsoft Power Platform CLI? | Microsoft Learn](https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction) 

- Ensure you are authenticated with ```pac auth```

```powershell

cd samples/mcs-BlogPostHelper

# Package up the solution, note the SRC part is important to pack.
pac solution pack --zipfile mcs-BlogPostHelper.zip --folder ./src

# Import into specific environment use -env, or leave blank for defualt environment
pac env list
pac solution import --path ./mcs-BlogPostHelper.zip -env ba171802-488b-ed1b-b121-e778530363a2

```

## Features

Extended description of the contents of the sample. What elements does it include? What concepts does illustrate?

Using this sample you can extend Microsoft 365 Copilot with an agent that:

* Helps build blog posts
* This is just a simple agent for testing the Copilot Samples process.

## Help

We do not support samples, but this community is always willing to help, and we want to improve these samples. We use GitHub to track issues, which makes it easy for  community members to volunteer their time and help resolve issues.

You can try looking at [issues related to this sample](https://github.com/pnp/copilot-pro-dev-samples/issues?q=label%3A%22sample%3A%20mcs-BlogPostHelper%22) to see if anybody else is having the same issues.

If you encounter any issues using this sample, [create a new issue](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

Finally, if you have an idea for improvement, [make a suggestion](https://github.com/pnp/copilot-pro-dev-samples/issues/new).

## Disclaimer

**THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.**

![](https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/mcs-BlogPostHelper)
