using ResolveMate.Core.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Interfaces
{
    public interface IAzureTableService
    {

        /// <summary>
        /// Get ticket by ticket id
        /// </summary>
        /// <param name="ticketId"></param>
        /// <returns></returns>
        Task<Ticket?> GetTicketAsync(string ticketId);
        /// <summary>
        /// Get tickets by status
        /// </summary>
        /// <param name="ticketStatus"></param>
        /// <returns></returns>
        Task<List<Ticket>> GetTicketsByStatusAsync(string ticketStatus);

        /// <summary>
        /// Update ticket priority
        /// </summary>
        /// <param name="ticketId"></param>
        /// <param name="priority"></param>
        /// <returns></returns>
        Task<Ticket?> UpdateTicketPriorityAsync(string ticketId, string priority);
        /// <summary>
        /// get tickets by type
        /// </summary>
        /// <param name="ticketType"></param>
        /// <returns></returns>
        Task<List<Ticket>> GetTicketsByTypeAsync(string ticketType);

        /// <summary>
        /// //get tickets by subject and description
        /// </summary>
        /// <param name="ticketSubject"></param>
        /// <param name="ticketDescription"></param>
        /// <returns></returns>
        Task<List<Ticket>> SearchTicketsBySubjectOrDescriptionAsync(string ticketSubject, string ticketDescription);

        /// <summary>
        /// filter tickets by status and priority
        /// </summary>
        /// <param name="status"></param>
        /// <param name="priority"></param>
        /// <returns></returns>
        Task<List<Ticket>> GetTicketsByStatusAndPriorityAsync(string status, string priority);

        /// <summary>
        /// Get tickets by customer email
        /// </summary>
        /// <param name="customerEmail"></param>
        /// <returns></returns>
        Task<List<Ticket>> GetTicketsByCustomerAsync(string customerEmail);

        /// <summary>
        /// Analyze customer satisfaction
        /// </summary>
        /// <returns></returns>
        Task<double> AnalyzeCustomerSatisfactionAsync(string ticketType);

    }
}
