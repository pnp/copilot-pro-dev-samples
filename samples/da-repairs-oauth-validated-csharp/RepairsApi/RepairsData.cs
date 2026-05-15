using RepairsApi.Models;
using System.Text.Json;

namespace RepairsApi
{
    public static class RepairsData
    {
        private static readonly List<Repair> _repairs;

        static RepairsData()
        {
            var dataPath = Path.Combine(AppContext.BaseDirectory, "repairsData.json");
            var json = File.ReadAllText(dataPath);
            _repairs = JsonSerializer.Deserialize<List<Repair>>(json) ?? new List<Repair>();
        }

        public static List<Repair> GetRepairs() => _repairs;
    }
}
