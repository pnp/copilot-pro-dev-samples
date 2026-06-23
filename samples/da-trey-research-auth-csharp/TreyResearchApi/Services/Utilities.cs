namespace TreyResearchApi.Services;

public class HttpError : Exception
{
    public int Status { get; }

    public HttpError(int status, string message) : base(message)
    {
        Status = status;
    }
}

public static class Utilities
{
    public static string CleanUpParameter(string name, string value)
    {
        var val = value.ToLowerInvariant();

        if (val.Contains("trey") || val.Contains("research"))
        {
            var newVal = val.Replace("trey", "").Replace("research", "").Trim();
            Console.WriteLine($"   ❗ Plugin name detected in the {name} parameter '{val}'; replacing with '{newVal}'.");
            val = newVal;
        }

        if (val == "<user_name>")
        {
            Console.WriteLine($"   ❗ Invalid name '{val}'; replacing with 'avery'.");
            val = "avery";
        }

        if (name == "role" && val == "consultant")
        {
            Console.WriteLine($"   ❗ Invalid role name '{val}'; replacing with ''.");
            val = "";
        }

        if (val == "null")
        {
            Console.WriteLine($"   ❗ Invalid value '{val}'; replacing with ''.");
            val = "";
        }

        return val;
    }
}
