using PnP.Core.Services;

namespace M365.Comms.API.Auth
{
    /// <summary>
    /// PnP Context Factory
    /// </summary>
    /// <remarks>
    /// Sourced from https://github.com/pnp/pnpcore/blob/dev/samples/Demo.Blazor/Services/MyContextFactory.cs
    /// </remarks>
    public class M365PnPContextFactory : IM365PnPContextFactory
    {
        private readonly IPnPContextFactory _contextFactory;
        private readonly IConfiguration _configuration;
        private readonly IAuthenticationProvider _webAPiAuthProvider;

        public M365PnPContextFactory(IPnPContextFactory contextFactory, IConfiguration configuration, IAuthenticationProvider webAPiAuthProvider)
        {
            _configuration = configuration;
            _contextFactory = contextFactory;
            _webAPiAuthProvider = webAPiAuthProvider;
        }

        public async Task<PnPContext> GetContextAsync()
        {
            string siteUrl = _configuration["SharePoint:SiteUrl"] ?? 
                    throw new InvalidOperationException("SiteUrl is not configured in the appsettings.json file");

           return await _contextFactory.CreateAsync(new Uri(siteUrl), _webAPiAuthProvider);
        }
    }

    /// <summary>
    /// Interface for the PnP Context Factory
    /// </summary>
    public interface IM365PnPContextFactory
    {
        public Task<PnPContext> GetContextAsync();
    }
}
