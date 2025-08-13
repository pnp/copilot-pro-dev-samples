using M365.Comms.API.Models;
using M365.Comms.API.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Identity.Web.Resource;

namespace M365.Comms.API.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    [RequiredScope(RequiredScopesConfigurationKey = "AzureAd:Scopes")]
    public class MessageController : ControllerBase
    {
        private readonly IMessageService _messageService;

        /// <summary>
        /// Initializes a new instance of the <see cref="MessageController"/> class.
        /// </summary>
        /// <param name="messageService"></param>
        public MessageController(IMessageService messageService)
        {
            _messageService = messageService;
        }

        /// <summary>
        /// Gets all messages.
        /// </summary>
        /// <returns></returns>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Message>>> GetMessages()
        {
            var messages = await _messageService.GetMessagesAsync();
            return Ok(messages);
        }

        /// <summary>
        /// Gets a specific message by its unique identifier.
        /// </summary>
        /// <returns></returns>
        [HttpGet("{id}")]
        public async Task<ActionResult<Message>> GetMessage(int id)
        {
            try
            {
                var message = await _messageService.GetMessageAsync(id);
                return Ok(message);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(ex.Message);
            }
        }

        /// <summary>
        /// Creates a new message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        [HttpPost]
        public async Task<ActionResult<Message>> CreateMessage(Message message)
        {
            var createdMessage = await _messageService.CreateMessageAsync(message);
            return CreatedAtAction(nameof(GetMessages), new { id = createdMessage.Id }, createdMessage);
        }

        /// <summary>
        /// Updates an existing message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        [HttpPatch]
        public async Task<IActionResult> UpdateMessage(Message message)
        {
            try
            {
                var updatedMessage = await _messageService.UpdateMessageAsync(message);
                return Ok(updatedMessage);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(ex.Message);
            }

        }

        /// <summary>
        /// Cancels the approval of a message.
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        [HttpPatch("{id}/cancel")]
        public async Task<ActionResult<Message>> CancelMessageApproval(int id)
        {
            try
            {
                var updatedMessage = await _messageService.CancelApprovalAsync(id);
                return Ok(updatedMessage);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(ex.Message);
            }
        }

        /// <summary>
        /// Submits a message for approval.
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        [HttpPatch("{id}/submit")]
        public async Task<ActionResult<Message>> SubmitMessageApproval(int id)
        {
            try
            {
                var updatedMessage = await _messageService.SubmitApprovalAsync(id);
                return Ok(updatedMessage);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(ex.Message);
            }
        }
    }
}
