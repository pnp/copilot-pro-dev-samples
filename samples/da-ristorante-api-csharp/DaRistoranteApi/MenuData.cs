using DaRistoranteApi.Models;
using System.Text.Json;

namespace DaRistoranteApi
{
    public static class MenuData
    {
        private static readonly List<Dish> _dishes;

        static MenuData()
        {
            var dataPath = Path.Combine(AppContext.BaseDirectory, "data.json");
            var json = File.ReadAllText(dataPath);
            _dishes = JsonSerializer.Deserialize<List<Dish>>(json) ?? new List<Dish>();
        }

        public static List<Dish> GetDishes() => _dishes;
    }
}
