using Azure.Data.Tables;
using Dapper;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ResolveMate.Core.Interfaces;
using ResolveMate.Core.Models;
using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Services
{

    public class SQLService : ISQLService
    {
        private readonly AppSettings _appSettings;
        private readonly ILogger<SQLService> _logger;

        public SQLService(IOptions<AppSettings> options, ILogger<SQLService> logger)
        {
            _logger = logger;
            _appSettings = options.Value;
        }
        public async Task<IEnumerable<Ticket?>> GetTicketByIdAsync(string ticketId)
        {
            try
            {
                var storedProcedureName = "GetTicketByID";
                var parameters = new { TicketId = Convert.ToInt32(ticketId) };
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<Ticket>(storedProcedureName, parameters, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }

        }
        public async Task<IEnumerable<Ticket?>> GetTicketsByStatusAndPriorityAsync(string status, string priority)
        {
            try
            {
                var storedProcedureName = "GetTicketsByStatusPriority";
                var parameters = new { @TicketStatus = status, TicketPriority = priority };
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<Ticket>(storedProcedureName, parameters, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }

        }
        public async Task<IEnumerable<Ticket?>> SearchTicketsAsync(string searchTerm)
        {
            try
            {
                var storedProcedureName = "SearchTickets";
                var parameters = new { SearchTerm = searchTerm };
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<Ticket>(storedProcedureName, parameters, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }
        public async Task<IEnumerable<Ticket?>> UpdateTicketDetailsAsync(string ticketId, string ticketStatus, string ticketPriority, string? customerRating = null)
        {
            try
            {
                var storedProcedureName = "UpdateTicket";
                var parameters = new
                {
                    TicketId = Convert.ToInt32(ticketId),
                    TicketPriority = ticketPriority,
                    TicketStatus = ticketStatus,
                    CustomerSatisfactionRating = !string.IsNullOrEmpty(customerRating) ? Convert.ToSingle(customerRating) : (object)DBNull.Value
                };
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    //update ticket
                    await db.QueryAsync<Ticket>(storedProcedureName, parameters, commandType: CommandType.StoredProcedure);
                    //get updated ticket
                    return await GetTicketByIdAsync(ticketId);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }
        public async Task<IEnumerable<Ticket?>> GetCustomerTicketsAsync(string customerId)
        {
            try
            {
                var storedProcedureName = "GetCustomerTicketHistory";
                var parameters = new { CustomerId = Convert.ToInt32(customerId) };
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<Ticket>(storedProcedureName, parameters, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }

        public async Task<IEnumerable<ResolvedTicketWithSatisfaction>> GetResolvedTicketsWithCustomerSatisfactionAsync()
        {
            try
            {
                var storedProcedureName = "AnalyzeResolvedTicketsWithSatisfaction";
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<ResolvedTicketWithSatisfaction>(storedProcedureName, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }


        public async Task<IEnumerable<ResolutionMetric>> GetTicketsResolutionMetricsAsync()
        {
            try
            {
                var storedProcedureName = "TicketResolutionMetrics";
                using (IDbConnection db = new SqlConnection(_appSettings.ConnectionString))
                {
                    return await db.QueryAsync<ResolutionMetric>(storedProcedureName, commandType: CommandType.StoredProcedure);
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }
    }
}
