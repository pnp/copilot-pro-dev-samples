using AngleSharp.Dom;
using M365.Comms.API.Auth;
using M365.Comms.API.Models;
using Microsoft.Graph;
using Microsoft.Identity.Client;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;
using PnP.Core.QueryModel;
using PnP.Core.Services;
using Message = M365.Comms.API.Models.Message;

namespace M365.Comms.API.Services
{
    public class PnPSharePointMessageService : IMessageService
    {
        private readonly IM365PnPContextFactory _pnpContextFactory;
        private readonly string CommunicationQueueListName;
        private readonly ILogger<PnPSharePointMessageService> _logger;
        private readonly IConfiguration _configuration;

        public PnPSharePointMessageService(IM365PnPContextFactory pnpContextFactory, ILogger<PnPSharePointMessageService> logger, IConfiguration configuration)
        {
            _pnpContextFactory = pnpContextFactory;
            _logger = logger;
            _configuration = configuration;

            CommunicationQueueListName = _configuration.GetValue<string>("SharePoint:ListName") ??
                throw new InvalidOperationException("ListName is not configured in the appsettings.json file"); ;
        }

        /// <summary>
        /// Gets all messages from the SharePoint list.
        /// </summary>
        /// <returns></returns>
        public async Task<IEnumerable<Message>> GetMessagesAsync()
        {
            try
            {
                using (var context = await _pnpContextFactory.GetContextAsync())
                {
                    var list = context.Web.Lists.GetByTitle(CommunicationQueueListName);
                    var items = await list.Items.ToListAsync();

                    var messages = new List<Message>();
                    foreach (var item in items)
                    {
                        var message = new Message
                        {
                            Id = item.Id,
                            MarkdownContent = item.Values["MarkdownContent"]?.ToString() ?? string.Empty,
                            Approval = Enum.TryParse<ApprovalStatus>(item.Values["IsApproved"]?.ToString(), out var approval) ? approval : ApprovalStatus.Pending,
                            SendToSharePoint = item.Values["SendToSharePoint"] != null ? bool.Parse(item.Values["SendToSharePoint"].ToString()) : false,
                            SendToTeams = item.Values["SendToTeams"] != null ? bool.Parse(item.Values["SendToTeams"].ToString()) : false,
                            SendToOutlook = item.Values["SendToOutlook"] != null ? bool.Parse(item.Values["SendToOutlook"].ToString()) : false
                        };

                        // Get the URL of the list item
                        var listNameUrl = CommunicationQueueListName.Replace(" ", "%20");
                        var itemUrl = $"{context.Uri}/Lists/{listNameUrl}/DispForm.aspx?ID={item.Id}";
                        message.ReviewItemUrl = itemUrl;

                        messages.Add(message);

                    }

                    return messages;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while getting messages from the communication queue.");
                throw;
            }
        }

        /// <summary>
        /// Gets a message from the SharePoint list.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        public async Task<Message> GetMessageAsync(int messageId)
        {
            return await GetItemMessage(messageId);
        }

        /// <summary>
        /// Creates a new message in the SharePoint list.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        public async Task<Message> CreateMessageAsync(Message message)
        {
            try
            {
                using (var context = await _pnpContextFactory.GetContextAsync())
                {
                    var list = context.Web.Lists.GetByTitle(CommunicationQueueListName);

                    // New Messages should have pending approval
                    var pendingApproval = ApprovalStatus.Pending.ToString();
                    var now = DateTime.Now.ToString("yyyy-MMM-dd HH:mm:ss");
                    var prebakedTitle = $"{now} Communication Message";

                    // Useful reference for field values:
                    // https://pnp.github.io/pnpcore/using-the-sdk/listitems-fields.html
                    var newItem = list.Items.Add(
                        new Dictionary<string, object>
                        {
                            { "Title", prebakedTitle },
                            { "MarkdownContent", message.MarkdownContent },
                            { "IsApproved", pendingApproval },
                            { "SendToSharePoint", message.SendToSharePoint },
                            { "SendToTeams", message.SendToTeams },
                            { "SendToOutlook", message.SendToOutlook }
                        });

                    await newItem.UpdateAsync();

                    message.Id = newItem.Id;
                    return message;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while creating a message.");
                throw;
            }
        }

        /// <summary>
        /// Updates an existing message in the SharePoint list.
        /// </summary>
        /// <param name="message">Message to find</param>
        /// <returns></returns>
        /// <exception cref="KeyNotFoundException"></exception>
        public async Task<Message> UpdateMessageAsync(Message message)
        {
            try
            {

                using (var context = await _pnpContextFactory.GetContextAsync())
                {
                    var list = context.Web.Lists.GetByTitle(CommunicationQueueListName);
                    var item = await list.Items.GetByIdAsync(message.Id);

                    if (item == null)
                    {
                        throw new KeyNotFoundException($"Message with ID {message.Id} not found.");
                    }

                    // In this method only two properties should be updated.
                    item.Values["MarkdownContent"] = message.MarkdownContent;
                   
                    await item.UpdateAsync();

                    var updatedMessage = await GetItemMessage(message.Id);

                    return await Task.FromResult(updatedMessage);
                }
            }
            catch (KeyNotFoundException ex)
            {
                _logger.LogWarning(ex, ex.Message);
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while updating a message.");
                throw;
            }
        }

        /// <summary>
        /// Cancels the approval of a message.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public async Task<Message> CancelApprovalAsync(int messageId)
        {
            var updatedMessage = await UpdateApprovalStatus(messageId, ApprovalStatus.Cancelled);
            return await Task.FromResult(updatedMessage);

        }

        /// <summary>
        /// Submits a message for approval.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        public async Task<Message> SubmitApprovalAsync(int messageId)
        {
            var updatedMessage = await UpdateApprovalStatus(messageId, ApprovalStatus.Submitted);
            return await Task.FromResult(updatedMessage);
        }


        /// <summary>
        /// Updates the approval status of a message.
        /// </summary>
        /// <param name="messageId">ID of the message to update</param>
        /// <param name="status">New status</param>
        /// <returns></returns>
        private async Task<Message> UpdateApprovalStatus(int messageId, ApprovalStatus status)
        {
            try
            {

                using (var context = await _pnpContextFactory.GetContextAsync())
                {
                    var list = context.Web.Lists.GetByTitle(CommunicationQueueListName);
                    var item = await list.Items.GetByIdAsync(messageId);

                    if (item == null)
                    {
                        throw new KeyNotFoundException($"Message with ID {messageId} not found.");
                    }

                    item.Values["IsApproved"] = status.ToString();

                    await item.UpdateAsync();

                    var updatedMessage = await GetItemMessage(messageId);

                    return await Task.FromResult(updatedMessage);
                }
            }
            catch (KeyNotFoundException ex)
            {
                _logger.LogWarning(ex, ex.Message);
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while canceling the approval of a message.");
                throw;
            }
        }


        /// <summary>
        /// Gets a message from the SharePoint list.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        /// <exception cref="ArgumentException"></exception>
        private async Task<Message> GetItemMessage(int messageId)
        {
            using (var context = await _pnpContextFactory.GetContextAsync())
            {
                var list = context.Web.Lists.GetByTitle(CommunicationQueueListName);

                var item = await list.Items.GetByIdAsync(messageId);

                if (item != null) { 

                    var message = new Message()
                    {
                        Id = item.Id,
                        MarkdownContent = item.Values["MarkdownContent"]?.ToString() ?? string.Empty,
                        Approval = Enum.TryParse<ApprovalStatus>(item.Values["IsApproved"]?.ToString(), out var approval) ? approval : ApprovalStatus.Pending,
                        SendToSharePoint = item.Values["SendToSharePoint"] != null ? bool.Parse(item.Values["SendToSharePoint"].ToString()) : false,
                        SendToTeams = item.Values["SendToTeams"] != null ? bool.Parse(item.Values["SendToTeams"].ToString()) : false,
                        SendToOutlook = item.Values["SendToOutlook"] != null ? bool.Parse(item.Values["SendToOutlook"].ToString()) : false
                    };

                    // Get the URL of the list item
                    var listNameUrl = CommunicationQueueListName.Replace(" ", "%20");
                    var itemUrl = $"{context.Uri}/Lists/{listNameUrl}/DispForm.aspx?ID={item.Id}";
                    message.ReviewItemUrl = itemUrl;


                    return await Task.FromResult(message); 
                }

                throw new KeyNotFoundException("Message not found.");
            }
        }
    }
}
