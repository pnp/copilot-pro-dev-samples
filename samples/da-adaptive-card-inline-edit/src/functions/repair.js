// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { app } = require("@azure/functions");
const fs = require('fs');
const path = require('path');

// Validates API key from request headers
function isApiKeyValid(req) {
  const apiKey = req.headers.get("X-API-Key")?.trim();
  return apiKey === process.env.API_KEY;
}

// Returns a list of repair records, optionally filtered by assignedTo query parameter
async function repairs(req, context) {
  if (!isApiKeyValid(req)) {
    return {
      status: 401,
    };
  }
  const filePath = path.join(__dirname, '../repairsData.json');
  const fileData = fs.readFileSync(filePath, 'utf-8');
  const repairRecords = JSON.parse(fileData);
  const res = {
    status: 200,
    jsonBody: {
      results: repairRecords,
    },
  };
  const assignedTo = req.query.get("assignedTo");
  if (!assignedTo) {
    return res;
  }
  const repairs = repairRecords.filter((item) => {
    const query = assignedTo.trim().toLowerCase();
    const fullName = item.assignedTo.toLowerCase();
    const [firstName, lastName] = fullName.split(" ");
    return fullName === query || firstName === query || lastName === query;
  });
  res.jsonBody.results = repairs ?? [];
  return res;
}

// Updates a repair record by ID
async function updateRepair(req, context) {
  if (!isApiKeyValid(req)) {
    return { status: 401 };
  }
  const id = req.params.id;
  const body = await req.json();
  const newTitle = body.title;
  const newAssignee = body.assignedTo;
  const filePath = path.join(__dirname, '../repairsData.json');
  const fileData = fs.readFileSync(filePath, 'utf-8');
  const repairs = JSON.parse(fileData);
  const idx = repairs.findIndex(r => r.id === id);
  if (idx < 0) {
    return { status: 404 };
  }
  if (newTitle !== undefined) repairs[idx].title = newTitle;
  if (newAssignee !== undefined) repairs[idx].assignedTo = newAssignee;
  fs.writeFileSync(filePath, JSON.stringify(repairs, null, 2));
  return {
    status: 200,
    jsonBody: { updatedRepair: repairs[idx] }
  };
}

app.http("repairs", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: repairs,
});

app.http("updateRepair", {
  methods: ["PATCH"],
  route: "repairs/{id}",
  authLevel: "anonymous",
  handler: updateRepair,
});
