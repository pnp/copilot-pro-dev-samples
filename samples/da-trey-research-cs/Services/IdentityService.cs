using TreyResearch.Models;

namespace TreyResearch.Services;

public class IdentityService
{
    private static readonly IdentityService _instance = new();
    public static IdentityService Instance => _instance;

    public async Task<ApiConsultant> ValidateRequestAsync()
    {
        // Default user used for unauthenticated testing
        var userId = "1";
        var userName = "Avery Howard";
        var userEmail = "avery@treyresearch.com";

        ApiConsultant? consultant = null;
        try
        {
            consultant = await ConsultantApiService.Instance.GetApiConsultantByIdAsync(userId);
        }
        catch (HttpError ex) when (ex.Status == 404)
        {
            consultant = null;
        }

        if (consultant == null)
        {
            consultant = await CreateConsultantForUserAsync(userId, userName, userEmail);
        }

        return consultant;
    }

    private async Task<ApiConsultant> CreateConsultantForUserAsync(string userId, string userName, string userEmail)
    {
        var consultant = new Consultant
        {
            Id = userId,
            Name = userName,
            Email = userEmail,
            Phone = "1-555-123-4567",
            ConsultantPhotoUrl = "https://microsoft.github.io/copilot-camp/demo-assets/images/consultants/Unknown.jpg",
            Location = new Location
            {
                Street = "One Memorial Drive",
                City = "Cambridge",
                State = "MA",
                Country = "USA",
                PostalCode = "02142",
                Latitude = 42.361366,
                Longitude = -71.081257
            },
            Skills = new List<string> { "C#", "JavaScript", "TypeScript" },
            Certifications = new List<string> { "Azure Development" },
            Roles = new List<string> { "Architect", "Project Lead" }
        };

        return await ConsultantApiService.Instance.CreateApiConsultantAsync(consultant);
    }
}
