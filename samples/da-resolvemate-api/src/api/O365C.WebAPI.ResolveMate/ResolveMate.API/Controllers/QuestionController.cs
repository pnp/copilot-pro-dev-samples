using Microsoft.AspNetCore.Mvc;
using ResolveMate.Core.Models;

namespace ResolveMate.API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class QuestionController : Controller
    {

        [HttpPost]
        [Route("ask")]
        public async Task<IActionResult> AskQuestionAsync([FromForm] QuestionRequest questionRequest)
        {
            try
            {
                if (questionRequest == null)
                {
                    return BadRequest("Invalid question request.");
                }

                // Process the question request
                // For example, save the question to the database
                // and send an email notification to the support team

                return Ok("Question submitted successfully.");
            }
            catch (Exception ex)
            {
                // Log the exception (you can use a logging framework here)
                return StatusCode(StatusCodes.Status500InternalServerError, $"Error submitting question: {ex.Message}");
            }
        }
        //[HttpPost]
        //[Route("ask")]
        //public async Task<IActionResult> AskQuestionAsync()
        //{
        //    try
        //    {
        //        if (Request.ContentLength == 0)
        //        {
        //            return BadRequest("No file uploaded.");
        //        }

        //        using (var stream = new MemoryStream())
        //        {
        //            await Request.Body.CopyToAsync(stream);

        //            // Example: Save the file or process it
        //            var fileBytes = stream.ToArray();
        //            // Save fileBytes to a storage or process further

        //            // Log the file size
        //            Console.WriteLine($"Uploaded file size: {fileBytes.Length} bytes");

        //        }

        //        return Ok("File uploaded successfully.");
        //    }
        //    catch (Exception ex)
        //    {
        //        return StatusCode(StatusCodes.Status500InternalServerError, $"Error submitting question: {ex.Message}");
        //    }
        //}


    }
}
