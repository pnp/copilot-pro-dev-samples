import Clarity from "@microsoft/clarity";

//const projectId = import.meta.env.PUBLIC_CLARITY_PROJECT_ID;
const projectId = "yos3v2mtcy";

if (projectId) {
  Clarity.init(projectId);
}
