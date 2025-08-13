using M365.Comms.API.Models;
using Microsoft.AspNetCore.Http.HttpResults;

namespace M365.Comms.API.Services
{


    /// <summary>
    /// Provides methods for managing messages.
    /// </summary>
    public class MockMessageService : IMessageService
    {
        private readonly List<Message> _messages = new List<Message>();


        /// <summary>
        /// 
        /// </summary>
        public MockMessageService()
        {
            //Seed with test data for good responses.
            SeedTestData();
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="MockMessageService"/> class.
        /// </summary>
        /// <returns></returns>
        public async Task<IEnumerable<Message>> GetMessagesAsync()
        {
            return await Task.FromResult(_messages);
        }

        /// <summary>
        /// Creates a new message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        public async Task<Message> CreateMessageAsync(Message message)
        {
            message.Id = _messages.Count + 1;
            _messages.Add(message);
            return await Task.FromResult(message);
        }

        /// <summary>
        /// Updates an existing message.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        public async Task<Message> UpdateMessageAsync(Message message)
        {
            var existingMessage = _messages.Find(m => m.Id == message.Id);
            if (existingMessage != null)
            {
                existingMessage.MarkdownContent = message.MarkdownContent;
                return await Task.FromResult(existingMessage);
            }
            
            throw new KeyNotFoundException("Message not found.");
        }

        /// <summary>
        /// Cancels a message.
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        public async Task<Message> CancelApprovalAsync(int messageId)
        {
            var message = _messages.Find(m => m.Id == messageId);
            if (message != null)
            {
                message.Approval = ApprovalStatus.Cancelled;
                return await Task.FromResult(message);
            }
            
            throw new KeyNotFoundException("Message not found.");
        }

        public async Task<Message> SubmitApprovalAsync(int messageId)
        {
            var message = _messages.Find(m => m.Id == messageId);
            if (message != null)
            {
                message.Approval = ApprovalStatus.Submitted;
                return await Task.FromResult(message);
            }

            throw new KeyNotFoundException("Message not found.");
        }

        /// <summary>
        /// Gets a message by its unique identifier.
        /// </summary>
        /// <param name="messageId"></param>
        /// <returns></returns>
        public async Task<Message> GetMessageAsync(int messageId)
        {
            var message = _messages.Find(m => m.Id == messageId);
            if (message != null)
            {
                message.Approval = ApprovalStatus.Submitted;
                return await Task.FromResult(message);
            }

            throw new KeyNotFoundException("Message not found.");
        }

        /// <summary>
        /// Seed test data into the messages to ensure there is data initially
        /// </summary>
        private void SeedTestData()
        {
            _messages.Add(new Message { 
                Id = 1, 
                Approval = ApprovalStatus.Pending,
                MarkdownContent = "# Test Message from Mock SERVICE\n\n**Date:** Mon, 24 Feb 2025\n\n**Author:** Paul Bullock\n\n## Introduction\n\nThis is a test message to verify the functionality of the M365 Communication Queue service.\n\n## Key Points\n\n- **Testing:** This message is created to test the message creation and targeting functionality.\n- **Verification:** Ensure that the message is successfully created and targeted to SharePoint.\n\n## Conclusion\n\nThis test message will help us verify the proper functioning of the M365 Communication Queue service.\n\nThank you for your attention.\n\nBest regards,\n\nPaul Bullock",
                SendToSharePoint = true,
                SendToOutlook = false,
                SendToTeams = true,
                ReviewItemUrl = "https://localhost/item1" 
            });

            _messages.Add(new Message
            {
                Id = 2,
                Approval = ApprovalStatus.Cancelled,
                MarkdownContent = "# Test Message from Mock SERVICE, this is not to be used",
                SendToSharePoint = false,
                SendToOutlook = false,
                SendToTeams = true,
                ReviewItemUrl = "https://localhost/item2"
            });

            _messages.Add(new Message
            {
                Id = 3,
                Approval = ApprovalStatus.Pending,
                MarkdownContent = "## Introducing Blog Helper Agent, a Microsoft 365 Copilot Agent!\n\nThis new service is designed to assist you in creating, managing, and optimizing your blog content with ease. Whether you're drafting a new post, scheduling updates, or analyzing reader engagement, Blog Helper Agent is here to streamline your blogging experience. Stay tuned for more details on how this innovative tool can enhance your content creation process.\n\n**Date:** 13th February 2025\n\n**Signature:** Paul Bullock",
                SendToSharePoint = false,
                SendToOutlook = false,
                SendToTeams = true,
                ReviewItemUrl = "https://localhost/item3"
            });

            _messages.Add(new Message
            {
                Id = 4,
                Approval = ApprovalStatus.Pending,
                MarkdownContent = "### Exciting New Product Launch: Drone X1000 Series!\n\nWe are thrilled to announce the upcoming launch of our latest innovation, the **Drone X1000 Series**! Mark your calendars for **6th March** as we unveil our fastest, lightest drone yet, equipped with a stunning **4K camera**.\n\n#### Key Features:\n- **Fastest**: Experience unparalleled speed and agility.\n- **Lightest**: Designed for maximum portability and ease of use.\n- **4K Camera**: Capture breathtaking, high-resolution footage.\n\nJoin us in celebrating this exciting milestone and stay tuned for more updates. Get ready to elevate your aerial photography and videography to new heights with the Drone X1000 Series!\n\nStay excited and be prepared for the big reveal on 6th March!",
                SendToSharePoint = true,
                SendToOutlook = true,
                SendToTeams = false,
                ReviewItemUrl = "https://localhost/item4"
            });

            _messages.Add(new Message
            {
                Id = 99,
                Approval = ApprovalStatus.Pending,
                MarkdownContent = "# Test Message from Mock SERVICE - this is enabled for this web api",
                SendToSharePoint = true,
                SendToOutlook = true,
                SendToTeams = true,
                ReviewItemUrl = "https://localhost/item99"
            });
        }
    }
}
