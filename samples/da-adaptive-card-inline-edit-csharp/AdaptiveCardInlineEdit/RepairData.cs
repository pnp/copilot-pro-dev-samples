// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using System.Text.Json;
using AdaptiveCardInlineEdit.Models;

namespace AdaptiveCardInlineEdit
{
    public static class RepairData
    {
        private static readonly JsonSerializerOptions _jsonOptions = new()
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        // Loaded once from the seed file; mutations are kept in memory for the lifetime of the process.
        private static readonly List<RepairModel> _repairs = JsonSerializer.Deserialize<List<RepairModel>>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "repairData.json")), _jsonOptions) ?? [];

        public static List<RepairModel> GetRepairs() => _repairs;

        public static RepairModel? UpdateRepair(string id, string? title, string? assignedTo)
        {
            var repair = _repairs.FirstOrDefault(r => r.Id == id);
            if (repair == null) return null;

            if (title != null) repair.Title = title;
            if (assignedTo != null) repair.AssignedTo = assignedTo;

            return repair;
        }
    }
}
