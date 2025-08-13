namespace M365.Comms.API.Models
{
    /// <summary>
    /// Represents the settings for the application.
    /// </summary>
    public class AppSettings
    {
        /// <summary>
        /// Gets or sets the server URL for the API.
        /// </summary>
        public string? ServerUrl { get; set; }

        /// <summary>
        /// Gets or sets the Azure AD settings for the API.
        /// </summary>
        public AzureADSettings? AzureAd { get; set; }
    }
}
