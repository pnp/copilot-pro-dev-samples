using M365.Comms.API.Models;

namespace M365.Comms.API.Services
{
    /// <summary>
    /// Defines methods for managing messages.
    /// </summary>
    public interface IMessageService
    {
        /// <summary>
        /// Gets all messages.
        /// </summary>
        /// <returns></returns>
        Task<IEnumerable<Message>> GetMessagesAsync();

        /// <summary>
        /// Gets a message by its unique identifier.
        /// </summary>
        /// <returns></returns>
        Task<Message> GetMessageAsync(int messageId);

        /// <summary>
        /// Creates a new message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        Task<Message> CreateMessageAsync(Message message);

        /// <summary>
        /// Updates an existing message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        Task<Message> UpdateMessageAsync(Message message);


        /// <summary>
        /// Cancels the approval of a message.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        Task<Message> CancelApprovalAsync(int messageId);

        /// <summary>
        /// Submits a message for approval.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        Task<Message> SubmitApprovalAsync(int messageId);
    }
}
