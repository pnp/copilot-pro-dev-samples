// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using System.Text.Json;
using AdaptiveCardInlineEdit.Models;

namespace AdaptiveCardInlineEdit
{
    public static class RepairData
    {
        private static readonly string _dataFilePath = Path.GetFullPath(
            Path.Combine(AppContext.BaseDirectory, "..", "..", "repairData.json"));

        private static readonly JsonSerializerOptions _jsonOptions = new()
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        public static List<RepairModel> GetRepairs()
        {
            var json = File.ReadAllText(_dataFilePath);
            return JsonSerializer.Deserialize<List<RepairModel>>(json, _jsonOptions) ?? new List<RepairModel>();
        }

        public static RepairModel? UpdateRepair(string id, string? title, string? assignedTo)
        {
            var repairs = GetRepairs();
            var repair = repairs.FirstOrDefault(r => r.Id == id);
            if (repair == null) return null;

            if (title != null)
                repair.Title = title;
            if (assignedTo != null)
                repair.AssignedTo = assignedTo;

            var json = JsonSerializer.Serialize(repairs, _jsonOptions);
            File.WriteAllText(_dataFilePath, json);
            return repair;
        }
    }
}
