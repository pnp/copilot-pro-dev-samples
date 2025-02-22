using Azure.Core;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using ResolveMate.Core.Helpers;
using ResolveMate.Core.Interfaces;
using ResolveMate.Core.Models;
using ResolveMate.Core.Services;
using System;
using System.Threading.Tasks;

namespace ResolveMate.API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class TicketController : ControllerBase
    {
        private readonly ISQLService _sqlService;

        public TicketController(ISQLService sQLService)
        {
            _sqlService = sQLService;
        }
        

        [HttpGet]
        [Route("{ticketId}")]
        [EndpointName("GetTicketById")]
        [EndpointSummary("Find a ticket by its ID.")]
        [EndpointDescription("Find a ticket by its ID. This feature allows you to retrieve a specific customer support ticket using its unique identifier. for example, you can find a ticket with ID 7402.")]        
        public async Task<IActionResult> GetTicketByIdAsync(string ticketId)
        {
            try
            {
                var ticket = await _sqlService.GetTicketByIdAsync(ticketId);
                if (ticket == null)
                {
                    return NotFound($"Ticket with ID {ticketId} not found.");
                }
                return Ok(ticket);
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error retrieving ticket: {ex.Message}");
            }
        }

        [HttpGet]
        [Route("statusandpriority")]
        public async Task<IActionResult> GetTicketsByStatusAndPriorityAsync(string ticketStatus, string ticketPriority)
        {
            try
            {
                if (string.IsNullOrEmpty(ticketStatus) || string.IsNullOrEmpty(ticketPriority))
                {
                    return BadRequest("Invalid status or priority value.");
                }
                var tickets = await _sqlService.GetTicketsByStatusAndPriorityAsync(ticketStatus, ticketPriority);
                return Ok(tickets);
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error retrieving tickets by status: {ex.Message}");
            }
        }

        [HttpGet]
        [Route("search/{searchTerm}")]
        public async Task<IActionResult> SearchTicketsAsync(string searchTerm)
        {
            try
            {
                if (string.IsNullOrEmpty(searchTerm))
                {
                    return BadRequest("Invalid search term value.");
                }
                var tickets = await _sqlService.SearchTicketsAsync(searchTerm);
                return Ok(tickets);
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error retrieving tickets by status: {ex.Message}");
            }
        }

        [HttpPut]
        [Route("update")]
        public async Task<IActionResult> UpdateTicketDetailAsync([FromBody] UpdateTicketRequest request)
        {
            try
            {

                   
                   //Check the  parameters are not null
                    if (string.IsNullOrEmpty(request.TicketId) || string.IsNullOrEmpty(request.TicketStatus) || string.IsNullOrEmpty(request.TicketPriority))
                    {
                        return BadRequest("Invalid ticket ID, status or priority value.");
                    }                                                   

                    var updatedTicket = await _sqlService.UpdateTicketDetailsAsync(request.TicketId, request.TicketStatus, request.TicketPriority,request.CustomerRating);
                    return Ok(updatedTicket);
                
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error updating ticket priority: {ex.Message}");
            }
        }


        [HttpGet]
        [Route("customerTickets/{customerId}")]
        public async Task<IActionResult> GetTicketsByCustomerAsync(string customerId)
        {
            try
            {
                if (!string.IsNullOrEmpty(customerId))
                {
                    var tickets = await _sqlService.GetCustomerTicketsAsync(customerId);
                    return Ok(tickets);
                }
                else
                {
                    return BadRequest("Invalid customer email value.");
                }
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error retrieving tickets by customer email: {ex.Message}");
            }
        }
        [HttpGet]
        [Route("resolvedTicketsWithSatisfaction")]
        public async Task<IActionResult> GetResolvedTicketsWithCustomerSatisfactionAsync()
        {
            try
            {
                var result = await _sqlService.GetResolvedTicketsWithCustomerSatisfactionAsync();
                return Ok(result);
                
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error retrieving resolution metrics: {ex.Message}");
            }
        }    

    }
}