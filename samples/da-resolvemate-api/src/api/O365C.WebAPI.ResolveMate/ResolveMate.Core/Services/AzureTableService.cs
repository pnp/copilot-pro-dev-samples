//using Azure;
//using Azure.Data.Tables;
//using Microsoft.Extensions.Logging;
//using Microsoft.Extensions.Options;
//using ResolveMate.Core.Helpers;
//using ResolveMate.Core.Interfaces;
//using ResolveMate.Core.Mappers;
//using ResolveMate.Core.Models;

//using System;
//using System.Collections;
//using System.Collections.Concurrent;
//using System.Collections.Generic;
//using System.Linq;
//using System.Runtime;
//using System.Text;
//using System.Threading.Tasks;

//namespace ResolveMate.Core.Services
//{
//    public class AzureTableService : IAzureTableService
//    {
//        private readonly TableClient _tableClient;
//        private readonly AppSettings _appSettings;
//        private readonly ILogger<AzureTableService> _logger;

//        public AzureTableService(IOptions<AppSettings> options, ILogger<AzureTableService> logger)
//        {
//            _logger = logger;
//            _appSettings = options.Value;
//            _tableClient = new TableClient(new Uri(_appSettings.StorageURI), _appSettings.TableName, new TableSharedKeyCredential(_appSettings.AccountName, _appSettings.StorageAccountKey));
//        }

//        // 2. View existing ticket by ticketId
//        public async Task<Ticket?> GetTicketAsync(string ticketId)
//        {
//            List<Ticket> ticketList = new List<Ticket>();

//            try
//            {

//                /*Example of how to use a filter query to retrieve specific entities from Azure Table Storage.*/

//                // var partitionKey = "SupportTicket";
//                // var rowKey = "000d45ca-d74c-476d-b056-5d960a518e3d";
//                // var query = $"PartitionKey eq '{partitionKey}' and RowKey eq '{rowKey}'";
//                // AsyncPageable<TableEntity> queryResults = _tableClient.QueryAsync<TableEntity>(filter: query);
//                // await foreach (TableEntity qEntity in queryResults)
//                // {
//                //     ticketList.Add(TicketMapper.MapEntityToTicketAsync(qEntity));
//                // }

//                /*LINQ style query*/

//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.TicketId == ticketId);
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    ticketList.Add(qEntity);
//                }
//                Ticket? queriedTicket = ticketList.FirstOrDefault();
//                return queriedTicket;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying ticket: {ex.Message}");
//                return null;
//            }
//        }

//        //3. Get tickets by ticketStatus
//        public async Task<List<Ticket>> GetTicketsByStatusAsync(string ticketStatus = "Open")
//        {
//            List<Ticket> tickets = new List<Ticket>();
//            try
//            {

//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.TicketStatus.Equals(ticketStatus, StringComparison.InvariantCultureIgnoreCase));
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    tickets.Add(qEntity);
//                }
//                return tickets;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying tickets by ticketStatus: {ex.Message}");
//                return null;
//            }

//        }

//        // 3. Update existing ticket
//        public async Task<Ticket?> UpdateTicketAsync(Ticket ticket)
//        {
//            try
//            {
//                await _tableClient.UpdateEntityAsync(ticket, ticket.ETag, TableUpdateMode.Replace);
//                //Get updated ticket
//                var updatedTicket = await GetTicketAsync(ticket.TicketId);
//                return updatedTicket;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error updating ticket: {ex.Message}");
//                return null;
//            }
//        }

//        // 4. Update ticket priority
//        public async Task<Ticket?> UpdateTicketDetailsAsync(string ticketId, string priority)
//        {
//            try
//            {
//                var ticket = await GetTicketAsync(ticketId);
//                if (ticket != null)
//                {
//                    ticket.TicketPriority = priority;
//                    var updatedTicket = await UpdateTicketAsync(ticket);
//                    return updatedTicket;
//                }
//                return null;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error updating ticket priority: {ex.Message}");
//                return null;
//            }
//        }

//        //5. Get tickets by Ticket Type
//        public async Task<List<Ticket>> GetTicketsByTypeAsync(string ticketType)
//        {
//            List<Ticket> tickets = new List<Ticket>();
//            try
//            {
//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.TicketType.Equals(ticketType, StringComparison.InvariantCultureIgnoreCase));
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    tickets.Add(qEntity);
//                }
//                return tickets;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying tickets by ticketType: {ex.Message}");
//                return null;
//            }
//        }

//        //6. Search tickets by subject or description
//        public async Task<List<Ticket>> SearchTicketsBySubjectOrDescriptionAsync(string ticketSubject, string ticketDescription)
//        {
//            List<Ticket> tickets = new List<Ticket>();
//            try
//            {
//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.TicketSubject.Contains(ticketSubject) || ent.TicketDescription.Contains(ticketDescription));
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    tickets.Add(qEntity);
//                }
//                return tickets;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying tickets by ticketSubject or ticketDescription: {ex.Message}");
//                return null;
//            }
//        }

//        //7. Filter tickets by status and priority
//        public async Task<List<Ticket>> GetTicketsByStatusAndPriorityAsync(string status, string priority)
//        {
//            List<Ticket> tickets = new List<Ticket>();
//            try
//            {
//                //Convert enum to string                
//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.TicketPriority == priority.ToString());
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    tickets.Add(qEntity);
//                }

//                return tickets;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying tickets by status and priority: {ex.Message}");
//                return null;
//            }
//        }

//        //8. Get tickets by customer email
//        public async Task<List<Ticket>> GetTicketsByCustomerAsync(string customerEmail)
//        {
//            List<Ticket> tickets = new List<Ticket>();
//            try
//            {
//                AsyncPageable<Ticket> queryResults = _tableClient.QueryAsync<Ticket>(ent => ent.CustomerEmail.Equals(customerEmail, StringComparison.InvariantCultureIgnoreCase));
//                await foreach (Ticket qEntity in queryResults)
//                {
//                    tickets.Add(qEntity);
//                }
//                return tickets;
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error querying tickets by customerEmail: {ex.Message}");
//                return null;
//            }
//        }

//        // 9. Analyze customer satisfaction
//        public async Task<double> AnalyzeCustomerSatisfactionAsync(string ticketType)
//        {
//            double totalRating = 0;
//            int count = 0;
//            try
//            {
//                AsyncPageable<Ticket> queryResults;
//                if (string.IsNullOrEmpty(ticketType))
//                {
//                    queryResults = _tableClient.QueryAsync<Ticket>(t => t.CustomerSatisfactionRating > 0);
//                }
//                else
//                {
//                    queryResults = _tableClient.QueryAsync<Ticket>(t => t.CustomerSatisfactionRating > 0 && t.TicketType == ticketType);
                    
//                }
                
//                await foreach (var ticket in queryResults)
//                {
//                    totalRating += ticket.CustomerSatisfactionRating;
//                    count++;
//                }
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError($"Error analyzing customer satisfaction: {ex.Message}");
//            }
//            return count > 0 ? totalRating / count : 0;
//        }

//    }
//}
