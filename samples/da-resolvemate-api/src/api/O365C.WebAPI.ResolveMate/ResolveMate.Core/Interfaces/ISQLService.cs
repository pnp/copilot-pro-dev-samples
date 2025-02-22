using ResolveMate.Core.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Interfaces
{
    public interface ISQLService
    {
        Task<IEnumerable<Ticket?>> GetTicketByIdAsync(string ticketId);
        Task<IEnumerable<Ticket?>> GetTicketsByStatusAndPriorityAsync(string status, string priority);
        Task<IEnumerable<Ticket?>> SearchTicketsAsync(string searchTerm);
        Task<IEnumerable<Ticket?>> UpdateTicketDetailsAsync(string ticketId, string ticketStatus, string ticketPriority, string? customerRating = null);
        Task<IEnumerable<Ticket?>> GetCustomerTicketsAsync(string customerId);
        Task<IEnumerable<ResolvedTicketWithSatisfaction>> GetResolvedTicketsWithCustomerSatisfactionAsync();
        Task<IEnumerable<ResolutionMetric>> GetTicketsResolutionMetricsAsync();
    }
}
